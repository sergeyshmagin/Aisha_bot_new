"""
Рабочие процессы для работы с аватарами.
"""

import os
import uuid
import hashlib
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from telebot.async_telebot import AsyncTeleBot

from database.models import UserAvatar, UserAvatarPhoto
from frontend_bot.config import settings
from frontend_bot.config.storage import StorageConfig
from frontend_bot.utils.logger import get_logger
from frontend_bot.services.state_utils import set_state as set_state_pg
from database.config import AsyncSessionLocal
from frontend_bot.services.minio_client import delete_file, upload_file, generate_presigned_url, check_file_exists
from frontend_bot.services.avatar_manager import save_avatar_minio
from frontend_bot.services.photo_buffer import get_buffered_photos_redis, clear_photo_buffer_redis
# from database.repository import UserAvatarRepository  # раскомментируйте, если нужен реальный репозиторий

logger = logging.getLogger(__name__)
storage_config = StorageConfig()

class PhotoValidationError(Exception):
    """Ошибка валидации фото (дубль, невалидный формат и т.д.)."""
    pass

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

async def delete_draft_avatar(user_id: str, avatar_id: str, session: AsyncSession) -> None:
    """
    Удаляет черновик аватара пользователя и все связанные файлы.
    """
    try:
        # 1. Удаляем все фото из user_avatar_photos
        res = await session.execute(
            delete(UserAvatarPhoto)
            .where(UserAvatarPhoto.user_id == user_id, UserAvatarPhoto.avatar_id == avatar_id)
        )
        logger.info(f"[AVATAR_WORKFLOW] Удалено фото: {res.rowcount} шт. user_id={user_id}, avatar_id={avatar_id}")
        # 2. Удаляем сам аватар
        res2 = await session.execute(
            delete(UserAvatar)
            .where(UserAvatar.user_id == user_id, UserAvatar.id == avatar_id)
        )
        logger.info(f"[AVATAR_WORKFLOW] Удалён аватар: {res2.rowcount} user_id={user_id}, avatar_id={avatar_id}")
        await session.commit()
        logger.info(f"[AVATAR_WORKFLOW] Удален черновик аватара: user_id={user_id}, avatar_id={avatar_id}")
    except Exception as e:
        logger.error(f"[AVATAR_WORKFLOW] Ошибка при удалении черновика: {e}")
        await session.rollback()
        raise

async def cleanup_state(user_id: int, session: AsyncSession):
    """
    Очищает временные данные, связанные с созданием аватара пользователя.
    - Сбрасывает FSM-состояние.
    - Удаляет черновики аватара из БД.
    - (Опционально) Удаляет временные файлы из MinIO.
    """
    async with AsyncSessionLocal() as session:
        await set_state_pg(user_id, "main_menu", session)
    await delete_draft_avatar(user_id, avatar_id, session)
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

async def check_photo_duplicate(user_id, avatar_id, photo_hash, session):
    query = select(UserAvatarPhoto).where(
        UserAvatarPhoto.user_id == user_id,
        UserAvatarPhoto.avatar_id == avatar_id,
        UserAvatarPhoto.photo_hash == photo_hash
    )
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None

async def handle_photo_upload(
    bot: AsyncTeleBot,
    chat_id: int,
    user_id: int,
    avatar_id: str,
    session: AsyncSession
) -> None:
    """
    Обрабатывает загрузку фото для аватара.
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        user_id: ID пользователя
        avatar_id: ID аватара
        session: Сессия БД
    """
    try:
        # Получаем фото из буфера
        photos = await get_buffered_photos_redis(user_id)
        
        if not photos:
            await bot.send_message(
                chat_id,
                "❌ Не удалось получить фото из буфера."
            )
            return
            
        # Обрабатываем каждое фото
        for photo_data in photos:
            # Считаем md5-хеш фото
            photo_hash = hashlib.md5(photo_data["photo"]).hexdigest()
            logger.warning(f"[DEBUG] md5 hash загружаемого фото: {photo_hash}")
            
            # Проверяем на дубли по хешу через утилиту
            is_duplicate = await check_photo_duplicate(user_id, avatar_id, photo_hash, session)
            logger.warning(f"[DEBUG] check_photo_duplicate: {is_duplicate}")
            
            if is_duplicate:
                logger.warning(f"[DEBUG] Найден дубль по md5: {photo_hash}")
                raise PhotoValidationError("Это фото уже загружено. Пожалуйста, загрузите другое фото.")
                
            # Сохраняем фото
            await save_avatar_minio(
                db=session,
                user_id=user_id,
                avatar_id=avatar_id,
                original=photo_data["photo"],
                metadata={"file_id": photo_data["meta"]["file_id"], "photo_hash": photo_hash}
            )
            logger.warning(f"[DEBUG] Фото успешно сохранено с md5: {photo_hash}")
            
        # Очищаем буфер
        await clear_photo_buffer_redis(user_id)
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке фото: {e}")
        raise

async def cleanup_drafts_task():
    """
    Периодическая задача для очистки старых черновиков.
    Запускается каждые 6 часов.
    """
    while True:
        try:
            # Получаем всех пользователей с черновиками
            users = await get_users_with_drafts()
            
            for user_id in users:
                await cleanup_old_drafts(user_id)
                
            logger.info("[AVATAR_WORKFLOW] Очистка черновиков завершена")
            
        except Exception as e:
            logger.error(f"[AVATAR_WORKFLOW] Ошибка при очистке черновиков: {e}")
            
        # Ждем 6 часов перед следующей очисткой
        await asyncio.sleep(6 * 60 * 60)

async def cleanup_minio_files(avatar_id: str, session: AsyncSession) -> None:
    """
    Очищает файлы аватара из MinIO.
    
    Args:
        avatar_id: ID аватара
        session: Сессия БД
    """
    try:
        # Получаем все фото аватара
        query = select(UserAvatarPhoto).where(
            UserAvatarPhoto.avatar_id == avatar_id
        )
        result = await session.execute(query)
        photos = result.scalars().all()
        
        # Удаляем каждое фото из MinIO
        for photo in photos:
            try:
                await delete_file(storage_config.AVATAR_DIR, photo.photo_key)
                logger.info(f"[AVATAR_WORKFLOW] Удален файл из MinIO: {photo.photo_key}")
            except Exception as e:
                logger.error(f"[AVATAR_WORKFLOW] Ошибка при удалении файла из MinIO: {e}")
                
    except Exception as e:
        logger.error(f"[AVATAR_WORKFLOW] Ошибка при очистке файлов MinIO: {e}")

async def cleanup_old_drafts(user_id: int, max_age_hours: int = 24) -> None:
    """
    Очищает старые черновики аватаров и их файлы.
    
    Args:
        user_id: ID пользователя
        max_age_hours: Максимальный возраст черновика в часах
    """
    try:
        async with AsyncSessionLocal() as session:
            # Получаем все черновики пользователя
            query = select(UserAvatar).where(
                UserAvatar.user_id == user_id,
                UserAvatar.is_draft == 1
            )
            result = await session.execute(query)
            drafts = result.scalars().all()
            
            now = datetime.utcnow()
            
            for draft in drafts:
                created_at = draft.created_at
                age_hours = (now - created_at).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    # Удаляем черновик и все связанные файлы
                    await delete_draft_avatar(user_id, draft.id, session)
                    logger.info(f"[AVATAR_WORKFLOW] Удален старый черновик: user_id={user_id}, avatar_id={draft.id}")
                    
    except Exception as e:
        logger.error(f"[AVATAR_WORKFLOW] Ошибка при очистке черновиков: {e}") 

async def get_users_with_drafts():
    async with AsyncSessionLocal() as session:
        query = select(UserAvatar.user_id).where(UserAvatar.is_draft == 1).distinct()
        result = await session.execute(query)
        return [row[0] for row in result.fetchall()] 