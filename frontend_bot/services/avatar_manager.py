"""
Сервис управления аватарами.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import os
from pathlib import Path
import mimetypes
from PIL import Image
import io
import uuid
import sys
from uuid import UUID
from datetime import datetime
from minio.error import S3Error
from frontend_bot.services.minio_client import upload_file, download_file, ensure_bucket_exists

from database.models import UserAvatar, UserAvatarPhoto
from frontend_bot.utils.logger import get_logger
from frontend_bot.config import settings
from frontend_bot.config.storage import StorageConfig, BUCKET_STRUCTURES

logger = logging.getLogger(__name__)

print("[DEBUG] avatar_manager.py: start", file=sys.stderr)

# Словарь для хранения текущих ID аватаров пользователей
_current_avatar_ids: Dict[int, str] = {}

# Создаем необходимые директории при импорте
os.makedirs(settings.AVATAR_FSM_PATH, exist_ok=True)
os.makedirs(settings.AVATAR_PHOTOS_PATH, exist_ok=True)

# Инициализация MinIO клиента
storage_config = StorageConfig()

# Создаем бакет для аватаров, если его нет
try:
    ensure_bucket_exists(storage_config.AVATAR_DIR)
except S3Error as e:
    logger.error(f"Ошибка при создании бакета MinIO: {e}")

def init_avatar_fsm(user_id: int) -> None:
    """
    Инициализирует FSM для создания аватара.
    
    Args:
        user_id (int): ID пользователя
    """
    _current_avatar_ids[user_id] = None

async def create_draft_avatar(user_id: int, session: AsyncSession, avatar_data: dict) -> str:
    """
    Создаёт черновик аватара и возвращает его id.
    """
    from database.models import UserAvatar
    avatar_id = str(uuid.uuid4())
    logger.debug(f"[create_draft_avatar] user_id={user_id}, avatar_id={avatar_id}, avatar_data={avatar_data}")
    logger.debug(f"[create_draft_avatar] user_id type: {type(user_id)}, avatar_id type: {type(avatar_id)}")
    try:
        avatar = UserAvatar(id=avatar_id, user_id=user_id, avatar_data=avatar_data)
        session.add(avatar)
        await session.commit()
        await session.refresh(avatar)
        logger.debug(f"[create_draft_avatar] created avatar: {avatar}")
        return avatar_id
    except Exception as e:
        logger.error(f"[create_draft_avatar] Ошибка при создании аватара: {e}")
        raise

def get_current_avatar_id(user_id: Union[int, UUID]) -> Optional[str]:
    """
    Получает текущий ID аватара пользователя.
    
    Args:
        user_id (Union[int, UUID]): ID пользователя (int или UUID)
        
    Returns:
        Optional[str]: ID аватара или None
    """
    if isinstance(user_id, UUID):
        user_id = user_id.int
    avatar_id = _current_avatar_ids.get(user_id)
    logger.debug(f"[get_current_avatar_id] user_id={user_id}, avatar_id={avatar_id}")
    return avatar_id

def set_current_avatar_id(user_id: Union[int, UUID], avatar_id: Optional[str]) -> None:
    """
    Устанавливает текущий ID аватара пользователя.
    
    Args:
        user_id (Union[int, UUID]): ID пользователя (int или UUID)
        avatar_id (Optional[str]): ID аватара или None
    """
    # Если user_id - UUID, преобразуем в int
    if isinstance(user_id, UUID):
        user_id = user_id.int
    _current_avatar_ids[user_id] = avatar_id

async def get_avatars_index(user_id: int, session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Получает список аватаров пользователя.
    
    Args:
        user_id (int): ID пользователя
        session (AsyncSession): Сессия SQLAlchemy
        
    Returns:
        List[Dict[str, Any]]: Список аватаров
    """
    try:
        query = select(UserAvatar).where(
            UserAvatar.user_id == user_id
        ).order_by(
            UserAvatar.created_at.desc()
        )
        
        result = await session.execute(query)
        avatars = result.scalars().all()
        
        return [
            {
                "avatar_id": avatar.id,
                "photo_key": avatar.photo_key,
                "preview_key": avatar.preview_key,
                "created_at": avatar.created_at,
                "avatar_data": avatar.avatar_data
            }
            for avatar in avatars
        ]
    except Exception as e:
        logger.error(f"Ошибка при получении списка аватаров: {e}")
        return []

async def validate_photo(photo_bytes: bytes, existing_paths: List[str]) -> Tuple[bool, str]:
    """
    Валидирует фото для аватара.
    
    Args:
        photo_bytes (bytes): Байты фото
        existing_paths (List[str]): Список существующих путей
        
    Returns:
        Tuple[bool, str]: (Результат валидации, Сообщение)
    """
    try:
        # Проверяем формат файла
        mime_type = mimetypes.guess_type("photo.jpg")[0]
        if not mime_type or not mime_type.startswith('image/'):
            return False, "Неподдерживаемый формат файла"
            
        # Проверяем размер файла
        if len(photo_bytes) > storage_config.MAX_PHOTO_SIZE:
            return False, f"Размер файла превышает {storage_config.MAX_PHOTO_SIZE / 1024 / 1024}MB"
            
        # Проверяем изображение через PIL
        try:
            img = Image.open(io.BytesIO(photo_bytes))
            
            # Проверяем размеры
            width, height = img.size
            if width < storage_config.PHOTO_MIN_RES or height < storage_config.PHOTO_MIN_RES:
                return False, f"Изображение слишком маленькое. Минимальный размер: {storage_config.PHOTO_MIN_RES}x{storage_config.PHOTO_MIN_RES}"
                
            # Проверяем формат
            if img.format.lower() not in storage_config.ALLOWED_PHOTO_FORMATS:
                return False, f"Неподдерживаемый формат изображения. Разрешены: {', '.join(storage_config.ALLOWED_PHOTO_FORMATS)}"
                
        except Exception as e:
            return False, f"Ошибка при обработке изображения: {str(e)}"
            
        # Проверяем количество существующих фото
        if len(existing_paths) >= storage_config.AVATAR_MAX_PHOTOS:
            return False, f"Достигнут лимит в {storage_config.AVATAR_MAX_PHOTOS} фото"
            
        return True, "OK"
        
    except Exception as e:
        logger.error(f"Ошибка при валидации фото: {e}")
        return False, str(e)

async def save_avatar_minio(db: AsyncSession, user_id: UUID, avatar_id: UUID, original: bytes, metadata: Dict[str, Any]) -> None:
    """
    Сохраняет фото аватара в MinIO и метаданные в PostgreSQL.
    
    Args:
        db (AsyncSession): Сессия SQLAlchemy
        user_id (UUID): ID пользователя
        avatar_id (UUID): ID аватара
        original (bytes): Байты фото
        metadata (Dict[str, Any]): Метаданные фото
    """
    try:
        # Проверяем существование аватара
        query = select(UserAvatar).where(
            UserAvatar.id == avatar_id,
            UserAvatar.user_id == user_id
        )
        result = await db.execute(query)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            # Создаём аватар, если его нет
            avatar = UserAvatar(
                id=avatar_id,
                user_id=user_id,
                created_at=datetime.utcnow(),
                photo_key="",  # Временное значение
                preview_key="",  # Временное значение
                is_draft=True
            )
            db.add(avatar)
            await db.commit()
            logger.info(f"[FSM] save_avatar_minio: создан новый аватар {avatar_id}")
        
        # Генерируем уникальный ID для фото
        photo_id = str(uuid.uuid4())
        # Формируем путь в MinIO согласно структуре бакетов
        minio_path = BUCKET_STRUCTURES["avatars"]["path"].format(
            user_id=user_id,
            avatar_id=avatar_id
        ) + f"/{photo_id}.jpg"
        logger.info(f"[FSM] save_avatar_minio: minio_path={minio_path}")
        
        # Сохраняем в MinIO
        await upload_file(
            bucket=storage_config.AVATAR_DIR,
            object_name=minio_path,
            data=io.BytesIO(original),
            content_type="image/jpeg"
        )
        
        # Сохраняем метаданные в PostgreSQL
        photo = UserAvatarPhoto(
            id=photo_id,
            user_id=user_id,
            avatar_id=avatar_id,
            photo_key=minio_path,
            photo_metadata=metadata,
            photo_hash=metadata.get("photo_hash", "")
        )
        
        db.add(photo)
        await db.commit()

        # --- NEW: обновляем photo_key/preview_key у аватара, если это первое фото ---
        query = select(UserAvatar).where(
            UserAvatar.id == avatar_id,
            UserAvatar.user_id == user_id
        )
        result = await db.execute(query)
        avatar = result.scalar_one_or_none()
        if avatar and (not avatar.photo_key or avatar.photo_key == ""):
            avatar.photo_key = minio_path
            avatar.preview_key = minio_path  # если нет отдельного превью
            await db.commit()
            logger.info(f"[FSM] save_avatar_minio: обновлён photo_key/preview_key для аватара {avatar_id}")
        
        logger.info(f"Фото сохранено в MinIO и PostgreSQL: {minio_path}")
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении в MinIO: {e}")
        await db.rollback()  # Откатываем транзакцию при ошибке
        raise

async def remove_photo_from_avatar(db: AsyncSession, user_id: int, avatar_id: str, photo_id: str) -> bool:
    """
    Удаляет фото из аватара.
    
    Args:
        db (AsyncSession): Сессия SQLAlchemy
        user_id (int): ID пользователя
        avatar_id (str): ID аватара
        photo_id (str): ID фото
        
    Returns:
        bool: True если фото удалено, False если не найдено
    """
    try:
        logger.warning(f"[DEBUG] remove_photo_from_avatar: user_id={user_id}, avatar_id={avatar_id}, photo_id={photo_id}")
        # Получаем фото
        query = select(UserAvatarPhoto).where(
            UserAvatarPhoto.id == photo_id,
            UserAvatarPhoto.user_id == user_id,
            UserAvatarPhoto.avatar_id == avatar_id
        )
        result = await db.execute(query)
        photo = result.scalar_one_or_none()
        
        if not photo:
            logger.warning(f"[DEBUG] remove_photo_from_avatar: фото не найдено в БД")
            return False
            
        logger.warning(f"[DEBUG] remove_photo_from_avatar: найдено фото в БД, photo_key={photo.photo_key}")
            
        # Удаляем из MinIO
        try:
            logger.warning(f"[DEBUG] remove_photo_from_avatar: удаляем из MinIO bucket={storage_config.AVATAR_DIR}, object={photo.photo_key}")
            download_file(photo.photo_key)
            logger.warning(f"[DEBUG] remove_photo_from_avatar: успешно удалено из MinIO")
        except S3Error as e:
            logger.error(f"Ошибка при удалении из MinIO: {e}")
            
        # Удаляем из БД
        logger.warning(f"[DEBUG] remove_photo_from_avatar: удаляем из БД")
        await db.delete(photo)
        await db.commit()
        logger.warning(f"[DEBUG] remove_photo_from_avatar: успешно удалено из БД")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при удалении фото: {e}")
        return False

async def get_avatar_photo(photo_key: str) -> bytes:
    """
    Получает фото из MinIO по ключу.
    
    Args:
        photo_key (str): Ключ фото в MinIO
        
    Returns:
        bytes: Байты фото
    """
    try:
        return download_file(photo_key)
    except Exception as e:
        logger.error(f"Ошибка при получении фото из MinIO: {e}")
        raise

async def get_avatar_photos_from_db(
    user_id: int,
    avatar_id: str,
    session: AsyncSession
) -> List[Dict[str, Any]]:
    """
    Получает список фото аватара из БД.
    
    Args:
        user_id (int): ID пользователя
        avatar_id (str): ID аватара
        session (AsyncSession): Сессия БД
        
    Returns:
        List[Dict[str, Any]]: Список фото с их метаданными
    """
    try:
        # Получаем все фото аватара
        query = select(UserAvatarPhoto).where(
            UserAvatarPhoto.user_id == user_id,
            UserAvatarPhoto.avatar_id == avatar_id
        ).order_by(UserAvatarPhoto.created_at)
        
        result = await session.execute(query)
        photos = result.scalars().all()
        
        # Формируем список с метаданными
        return [{
            "id": photo.id,
            "photo_key": photo.photo_key,
            "created_at": photo.created_at
        } for photo in photos]
        
    except Exception as e:
        logger.error(f"Ошибка при получении фото аватара: {e}")
        return []

async def cleanup_old_drafts(user_id: int, max_age_hours: int = 24) -> None:
    """
    Очищает старые черновики аватаров.
    
    Args:
        user_id: ID пользователя
        max_age_hours: Максимальный возраст черновика в часах
    """
    try:
        # Получаем все черновики пользователя
        drafts = await get_user_drafts(user_id)
        now = datetime.utcnow()
        
        for draft in drafts:
            created_at = draft.created_at
            age_hours = (now - created_at).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                # Удаляем черновик и связанные файлы
                await delete_draft_avatar(user_id, draft.id)
                logger.info(f"[AVATAR_MANAGER] Удален старый черновик: user_id={user_id}, avatar_id={draft.id}")
    except Exception as e:
        logger.error(f"[AVATAR_MANAGER] Ошибка при очистке черновиков: {e}")

__all__ = [
    'init_avatar_fsm',
    'get_current_avatar_id',
    'set_current_avatar_id',
    'get_avatars_index',
    'validate_photo',
    'save_avatar_minio',
    'remove_photo_from_avatar',
    'get_avatar_photo',
    'get_avatar_photos_from_db',
    'cleanup_old_drafts'
]

print("[DEBUG] avatar_manager.py: end", file=sys.stderr) 