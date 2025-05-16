"""
Модуль для управления процессом создания аватара.
Реализует полный workflow создания аватара с обработкой ошибок и валидацией.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime

from frontend_bot.services.avatar_manager import (
    init_avatar_fsm,
    add_photo_to_avatar,
    update_avatar_fsm,
    mark_avatar_ready,
    load_avatar_fsm,
)
from frontend_bot.services.state_utils import set_state, get_state, clear_state
from frontend_bot.constants.avatar import AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS
from frontend_bot.shared.image_processing import AsyncImageProcessor
from frontend_bot.config import PHOTO_MIN_RES

logger = logging.getLogger(__name__)

class AvatarCreationError(Exception):
    """Базовый класс для ошибок создания аватара."""
    pass

class PhotoValidationError(AvatarCreationError):
    """Ошибка валидации фото."""
    pass

class StateError(AvatarCreationError):
    """Ошибка состояния."""
    pass

class ValidationError(AvatarCreationError):
    """Ошибка валидации данных."""
    pass

async def init_avatar_creation(user_id: int) -> str:
    """
    Инициализирует процесс создания аватара.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        str: ID созданного аватара
        
    Raises:
        AvatarCreationError: Если не удалось инициализировать аватар
    """
    try:
        avatar_id = str(uuid4())
        await init_avatar_fsm(user_id, avatar_id)
        set_state(user_id, "avatar_photo_upload")
        return avatar_id
    except Exception as e:
        logger.error(f"Failed to init avatar creation: {e}")
        raise AvatarCreationError(f"Failed to init avatar creation: {e}")

async def validate_photo(photo_bytes: bytes) -> bool:
    """
    Валидирует фото по размеру и качеству.
    
    Args:
        photo_bytes: Байты фото
        
    Returns:
        bool: True если фото валидно
        
    Raises:
        PhotoValidationError: Если фото не прошло валидацию
    """
    try:
        # Проверяем размер фото
        if len(photo_bytes) > 10 * 1024 * 1024:  # 10MB
            raise PhotoValidationError("Photo size exceeds 10MB")
            
        # Проверяем разрешение
        img = await AsyncImageProcessor.open_from_bytes(photo_bytes)
        width, height = img.size
        if width < PHOTO_MIN_RES or height < PHOTO_MIN_RES:
            raise PhotoValidationError(
                f"Photo resolution too low. Minimum: {PHOTO_MIN_RES}x{PHOTO_MIN_RES}"
            )
            
        return True
    except Exception as e:
        logger.error(f"Photo validation error: {e}")
        raise PhotoValidationError(f"Photo validation failed: {e}")

async def handle_photo_upload(
    user_id: int, 
    avatar_id: str, 
    photo_bytes: bytes,
    file_id: Optional[str] = None
) -> str:
    """
    Обрабатывает загрузку фото для аватара.
    
    Args:
        user_id: ID пользователя
        avatar_id: ID аватара
        photo_bytes: Байты фото
        file_id: ID файла в Telegram (опционально)
        
    Returns:
        str: Путь к сохраненному фото
        
    Raises:
        PhotoValidationError: Если фото не прошло валидацию
        AvatarCreationError: При других ошибках
    """
    try:
        # Валидируем фото
        await validate_photo(photo_bytes)
        
        # Сохраняем фото
        photo_path = await add_photo_to_avatar(user_id, avatar_id, photo_bytes, file_id)
        
        # Проверяем количество фото
        data = await load_avatar_fsm(user_id, avatar_id)
        photos_count = len(data.get("photos", []))
        
        if photos_count > AVATAR_MAX_PHOTOS:
            raise PhotoValidationError(
                f"Maximum number of photos ({AVATAR_MAX_PHOTOS}) exceeded"
            )
            
        return photo_path
    except Exception as e:
        logger.error(f"Photo upload error: {e}")
        raise AvatarCreationError(f"Failed to upload photo: {e}")

async def handle_gender_selection(
    user_id: int, 
    avatar_id: str, 
    gender: str
) -> None:
    """
    Обрабатывает выбор пола для аватара.
    
    Args:
        user_id: ID пользователя
        avatar_id: ID аватара
        gender: Выбранный пол ('male' или 'female')
        
    Raises:
        ValidationError: Если пол невалиден
        AvatarCreationError: При других ошибках
    """
    try:
        if gender not in ["male", "female"]:
            raise ValidationError("Invalid gender value")
            
        await update_avatar_fsm(user_id, avatar_id, class_name=gender)
        set_state(user_id, "avatar_enter_name")
    except Exception as e:
        logger.error(f"Gender selection error: {e}")
        raise AvatarCreationError(f"Failed to set gender: {e}")

async def handle_name_input(
    user_id: int, 
    avatar_id: str, 
    name: str
) -> None:
    """
    Обрабатывает ввод имени для аватара.
    
    Args:
        user_id: ID пользователя
        avatar_id: ID аватара
        name: Имя аватара
        
    Raises:
        ValidationError: Если имя невалидно
        AvatarCreationError: При других ошибках
    """
    try:
        if not name or len(name.strip()) == 0:
            raise ValidationError("Name cannot be empty")
            
        if len(name) > 50:  # Максимальная длина имени
            raise ValidationError("Name is too long (max 50 characters)")
            
        await update_avatar_fsm(user_id, avatar_id, title=name)
        set_state(user_id, "avatar_confirm")
    except Exception as e:
        logger.error(f"Name input error: {e}")
        raise AvatarCreationError(f"Failed to set name: {e}")

async def finalize_avatar(
    user_id: int, 
    avatar_id: str
) -> None:
    """
    Завершает создание аватара.
    
    Args:
        user_id: ID пользователя
        avatar_id: ID аватара
        
    Raises:
        AvatarCreationError: Если не удалось завершить создание
    """
    try:
        # Проверяем количество фото
        data = await load_avatar_fsm(user_id, avatar_id)
        photos_count = len(data.get("photos", []))
        
        if photos_count < AVATAR_MIN_PHOTOS:
            raise ValidationError(
                f"Not enough photos. Minimum required: {AVATAR_MIN_PHOTOS}"
            )
            
        # Помечаем аватар как готовый
        await mark_avatar_ready(user_id, avatar_id)
        
        # Сбрасываем состояние
        set_state(user_id, "my_avatars")
    except Exception as e:
        logger.error(f"Avatar finalization error: {e}")
        raise AvatarCreationError(f"Failed to finalize avatar: {e}")

async def cleanup_state(user_id: int) -> None:
    """
    Очищает состояние пользователя.
    
    Args:
        user_id: ID пользователя
    """
    try:
        avatar_id = get_state(user_id)
        if avatar_id:
            # Удаляем временные файлы
            # TODO: Реализовать удаление временных файлов
            
            # Сбрасываем состояние
            set_state(user_id, "my_avatars")
    except Exception as e:
        logger.error(f"State cleanup error: {e}")

async def handle_creation_error(
    user_id: int, 
    chat_id: int, 
    error: Exception
) -> None:
    """
    Обрабатывает ошибки создания аватара.
    
    Args:
        user_id: ID пользователя
        chat_id: ID чата
        error: Ошибка
    """
    try:
        # Логируем ошибку
        logger.error(f"Avatar creation error: {error}")
        
        # Очищаем состояние
        await cleanup_state(user_id)
        
        # Отправляем сообщение об ошибке
        error_message = str(error)
        if isinstance(error, PhotoValidationError):
            error_message = "Ошибка при загрузке фото. Пожалуйста, проверьте требования к фото."
        elif isinstance(error, ValidationError):
            error_message = "Ошибка валидации данных. Пожалуйста, проверьте введенные данные."
        elif isinstance(error, StateError):
            error_message = "Ошибка состояния. Пожалуйста, начните создание аватара заново."
            
        # TODO: Отправить сообщение пользователю
        # await bot.send_message(chat_id, error_message)
        
    except Exception as e:
        logger.error(f"Error handling error: {e}") 