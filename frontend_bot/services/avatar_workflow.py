"""
Рабочий процесс для создания и управления аватарами.
"""

import os
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from shared_storage.storage_utils import (
    init_storage,
    upload_file,
    download_file,
    delete_file,
    generate_presigned_url,
    get_file_metadata
)
from database.models import UserAvatar
from frontend_bot.config import settings
from frontend_bot.utils.logger import get_logger
from frontend_bot.services.state_utils import set_state_pg
from database.config import AsyncSessionLocal
# from database.repository import UserAvatarRepository  # раскомментируйте, если нужен реальный репозиторий

logger = get_logger(__name__)

async def save_avatar(
    user_id: int,
    image_data: bytes,
    name: str,
    session: AsyncSession,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Сохраняет аватар пользователя.
    
    Args:
        user_id (int): ID пользователя
        image_data (bytes): Данные изображения
        name (str): Имя аватара
        session (AsyncSession): Сессия SQLAlchemy
        metadata (Dict[str, Any], optional): Дополнительные метаданные
        
    Returns:
        Dict[str, Any]: Метаданные сохраненного аватара
    """
    try:
        # Генерируем уникальный ключ для файла
        avatar_id = str(uuid.uuid4())
        image_key = f"{user_id}/{avatar_id}/avatar.jpg"
        
        # Загружаем файл в MinIO
        await upload_file(
            "avatars",
            image_key,
            image_data,
            content_type="image/jpeg"
        )
        
        # Сохраняем метаданные в БД
        avatar = UserAvatar(
            user_id=user_id,
            avatar_id=avatar_id,
            name=name,
            image_path=image_key,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        session.add(avatar)
        await session.commit()
        
        return {
            "avatar_id": avatar_id,
            "name": name,
            "image_url": f"/avatars/{image_key}",
            "metadata": metadata,
            "created_at": avatar.created_at
        }
    except Exception as e:
        logger.error(f"Ошибка при сохранении аватара: {e}")
        raise

async def get_avatar(
    user_id: int,
    avatar_id: str,
    session: AsyncSession
) -> Optional[Dict[str, Any]]:
    """
    Получает аватар пользователя.
    
    Args:
        user_id (int): ID пользователя
        avatar_id (str): ID аватара
        session (AsyncSession): Сессия SQLAlchemy
        
    Returns:
        Optional[Dict[str, Any]]: Метаданные аватара или None если не найден
    """
    try:
        query = select(UserAvatar).where(
            UserAvatar.user_id == user_id,
            UserAvatar.avatar_id == avatar_id
        )
        result = await session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            return None
            
        # Получаем presigned URL для файла
        image_url = await generate_presigned_url("avatars", avatar.image_path)
        
        return {
            "avatar_id": avatar.avatar_id,
            "name": avatar.name,
            "image_url": image_url,
            "metadata": avatar.metadata,
            "created_at": avatar.created_at
        }
    except Exception as e:
        logger.error(f"Ошибка при получении аватара: {e}")
        return None

async def delete_avatar(
    user_id: int,
    avatar_id: str,
    session: AsyncSession
) -> bool:
    """
    Удаляет аватар пользователя.
    
    Args:
        user_id (int): ID пользователя
        avatar_id (str): ID аватара
        session (AsyncSession): Сессия SQLAlchemy
        
    Returns:
        bool: True если аватар был удален
    """
    try:
        # Получаем метаданные аватара
        query = select(UserAvatar).where(
            UserAvatar.user_id == user_id,
            UserAvatar.avatar_id == avatar_id
        )
        result = await session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            return False
            
        # Удаляем файл из MinIO
        await delete_file("avatars", avatar.image_path)
        
        # Удаляем метаданные из БД
        await session.execute(
            delete(UserAvatar).where(
                UserAvatar.user_id == user_id,
                UserAvatar.avatar_id == avatar_id
            )
        )
        await session.commit()
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении аватара: {e}")
        return False

async def list_avatars(
    user_id: int,
    session: AsyncSession,
    limit: int = 10,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Получает список аватаров пользователя.
    
    Args:
        user_id (int): ID пользователя
        session (AsyncSession): Сессия SQLAlchemy
        limit (int, optional): Максимальное количество аватаров
        offset (int, optional): Смещение
        
    Returns:
        List[Dict[str, Any]]: Список метаданных аватаров
    """
    try:
        query = select(UserAvatar).where(
            UserAvatar.user_id == user_id
        ).order_by(
            UserAvatar.created_at.desc()
        ).limit(limit).offset(offset)
        
        result = await session.execute(query)
        avatars = result.scalars().all()
        
        # Получаем presigned URL для файлов
        avatar_list = []
        for avatar in avatars:
            image_url = await generate_presigned_url("avatars", avatar.image_path)
            avatar_list.append({
                "avatar_id": avatar.avatar_id,
                "name": avatar.name,
                "image_url": image_url,
                "metadata": avatar.metadata,
                "created_at": avatar.created_at
            })
            
        return avatar_list
    except Exception as e:
        logger.error(f"Ошибка при получении списка аватаров: {e}")
        return []

async def create_draft_avatar(user_id: str, session: AsyncSession, data: dict) -> UserAvatar:
    """
    Создаёт черновик аватара (is_draft=True).
    """
    draft = UserAvatar(
        user_id=user_id,
        photo_key=data.get("photo_key", ""),
        preview_key=data.get("preview_key", ""),
        avatar_data=data.get("avatar_data", {}),
        is_draft=1,
        created_at=datetime.utcnow(),
    )
    session.add(draft)
    await session.commit()
    return draft

async def update_draft_avatar(user_id: str, session: AsyncSession, data: dict) -> None:
    """
    Обновляет черновик аватара (is_draft=True).
    """
    await session.execute(
        update(UserAvatar)
        .where(UserAvatar.user_id == user_id, UserAvatar.is_draft == 1)
        .values(
            photo_key=data.get("photo_key", ""),
            preview_key=data.get("preview_key", ""),
            avatar_data=data.get("avatar_data", {}),
        )
    )
    await session.commit()

async def finalize_draft_avatar(user_id: str, session: AsyncSession) -> None:
    """
    Переводит черновик в финальный аватар (is_draft=False).
    """
    await session.execute(
        update(UserAvatar)
        .where(UserAvatar.user_id == user_id, UserAvatar.is_draft == 1)
        .values(is_draft=0)
    )
    await session.commit()

async def delete_draft_avatar(user_id: str, session: AsyncSession) -> None:
    """
    Удаляет черновик аватара пользователя.
    """
    await session.execute(
        delete(UserAvatar)
        .where(UserAvatar.user_id == user_id, UserAvatar.is_draft == 1)
    )
    await session.commit()

async def cleanup_state(user_id: int, session: AsyncSession):
    """
    Очищает временные данные, связанные с созданием аватара пользователя.
    - Сбрасывает FSM-состояние.
    - Удаляет черновики аватара из БД.
    - (Опционально) Удаляет временные файлы из MinIO.
    """
    async with AsyncSessionLocal() as session:
        await set_state_pg(user_id, "main_menu", session)
    await delete_draft_avatar(user_id, session)
    # Если есть временные файлы — добавьте удаление из MinIO 

async def set_main_avatar(user_id: int, avatar_id: str, session: AsyncSession) -> None:
    """
    Устанавливает основной аватар пользователя (is_main=True), сбрасывает у остальных.
    """
    # Сбросить is_main у всех аватаров пользователя
    await session.execute(
        update(UserAvatar)
        .where(UserAvatar.user_id == user_id)
        .values(avatar_data={"is_main": False})
    )
    # Установить is_main у выбранного аватара
    await session.execute(
        update(UserAvatar)
        .where(UserAvatar.id == avatar_id)
        .values(avatar_data={"is_main": True})
    )
    await session.commit() 