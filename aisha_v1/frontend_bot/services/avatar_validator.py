"""
Сервис валидации аватаров.
"""

import logging
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from frontend_bot.services.avatar_manager import get_avatar_photos_from_db
from frontend_bot.services.minio_client import check_file_exists
from frontend_bot.repositories.user_repository import UserRepository
from frontend_bot.repositories.avatar_repository import UserAvatarRepository

logger = logging.getLogger(__name__)

async def validate_avatar_exists(
    user_id: int,
    avatar_id: str,
    session: AsyncSession
) -> Tuple[bool, str]:
    """
    Проверяет существование аватара в БД.
    
    Args:
        user_id (int): ID пользователя
        avatar_id (str): ID аватара
        session (AsyncSession): Сессия БД
        
    Returns:
        Tuple[bool, str]: (Результат валидации, Сообщение)
    """
    if session is None:
        logger.error(f"[validate_avatar_exists] session is None! user_id={user_id}, avatar_id={avatar_id}")
        return False, "Ошибка: нет соединения с БД"
    print(f"[validate_avatar_exists] user_id={user_id}, avatar_id={avatar_id}")
    logger.debug(f"[validate_avatar_exists] user_id type: {type(user_id)}, avatar_id type: {type(avatar_id)}")
    try:
        logger.debug(f"[validate_avatar_exists] user_id={user_id}, avatar_id={avatar_id}")
        avatar_repo = UserAvatarRepository(session)
        avatar = await avatar_repo.get_by_id(avatar_id)
        logger.debug(f"[validate_avatar_exists] avatar from db: {avatar}")
        
        if not avatar:
            return False, "Аватар не найден"
            
        if avatar.user_id != user_id:
            return False, "Аватар не принадлежит пользователю"
            
        return True, "OK"
        
    except Exception as e:
        logger.error(f"Ошибка при валидации аватара: {e}")
        return False, str(e)

async def validate_avatar_photos(
    user_id: int,
    avatar_id: str,
    session: AsyncSession
) -> Tuple[bool, str]:
    """
    Проверяет наличие фото аватара в MinIO.
    
    Args:
        user_id (int): ID пользователя
        avatar_id (str): ID аватара
        session (AsyncSession): Сессия БД
        
    Returns:
        Tuple[bool, str]: (Результат валидации, Сообщение)
    """
    try:
        # Получаем список фото из БД
        photos = await get_avatar_photos_from_db(user_id, avatar_id, session)
        
        if not photos:
            return False, "У аватара нет фотографий"
            
        # Проверяем каждое фото в MinIO
        for photo in photos:
            if not await check_file_exists("avatars", photo["photo_key"]):
                return False, f"Фото {photo['photo_key']} не найдено в хранилище"
                
        return True, "OK"
        
    except Exception as e:
        logger.error(f"Ошибка при валидации фото аватара: {e}")
        return False, str(e)

async def validate_avatar_state(
    user_id: int,
    avatar_id: str,
    session: AsyncSession
) -> Tuple[bool, str]:
    """
    Проверяет состояние аватара.
    
    Args:
        user_id (int): ID пользователя
        avatar_id (str): ID аватара
        session (AsyncSession): Сессия БД
        
    Returns:
        Tuple[bool, str]: (Результат валидации, Сообщение)
    """
    try:
        avatar_repo = UserAvatarRepository(session)
        avatar = await avatar_repo.get_by_id(avatar_id)
        
        if not avatar:
            return False, "Аватар не найден"
            
        if avatar.user_id != user_id:
            return False, "Аватар не принадлежит пользователю"
            
        if not avatar.is_ready:
            return False, "Аватар не готов к использованию"
            
        return True, "OK"
        
    except Exception as e:
        logger.error(f"Ошибка при валидации состояния аватара: {e}")
        return False, str(e) 