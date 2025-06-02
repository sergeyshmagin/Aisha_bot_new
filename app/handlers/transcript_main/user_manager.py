"""
Управление пользователями для основного обработчика транскриптов
Выделено из app/handlers/transcript_main.py для соблюдения правила ≤500 строк
"""
import logging
from typing import Optional
from aiogram.types import User as TelegramUser

from app.core.di import get_user_service_with_session
from app.database.models import User
from .models import UserRegistrationData

logger = logging.getLogger(__name__)class TranscriptUserManager:
    """
    Менеджер пользователей для обработчика транскриптов
    
    Отвечает за:
    - Получение пользователей по Telegram ID
    - Автоматическую регистрацию новых пользователей
    - Валидацию пользователей
    """
    
    def __init__(self, get_session_func):
        """
        Инициализация менеджера пользователей
        
        Args:
            get_session_func: Функция получения сессии БД
        """
        self.get_session = get_session_func
    
    async def get_or_register_user(self, telegram_user: TelegramUser) -> Optional[User]:
        """
        Получает пользователя или автоматически регистрирует нового
        
        Args:
            telegram_user: Объект пользователя Telegram
            
        Returns:
            Объект пользователя из БД или None при ошибке
        """
        try:
            async with self.get_session() as session:
                user_service = get_user_service_with_session(session)
                
                # Пытаемся найти существующего пользователя
                user = await user_service.get_user_by_telegram_id(telegram_user.id)
                
                if user:
                    logger.debug(f"Найден существующий пользователь: {user.id}")
                    return user
                
                # Регистрируем нового пользователя
                logger.info(f"Регистрируем нового пользователя: {telegram_user.id}")
                user_data = UserRegistrationData(telegram_user).to_dict()
                user = await user_service.register_user(user_data)
                
                if user:
                    logger.info(f"Пользователь успешно зарегистрирован: {user.id}")
                else:
                    logger.error(f"Не удалось зарегистрировать пользователя: {telegram_user.id}")
                
                return user
                
        except Exception as e:
            logger.error(f"Ошибка при получении/регистрации пользователя {telegram_user.id}: {e}")
            return None
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Получает пользователя по Telegram ID без автоматической регистрации
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Объект пользователя из БД или None
        """
        try:
            async with self.get_session() as session:
                user_service = get_user_service_with_session(session)
                return await user_service.get_user_by_telegram_id(telegram_id)
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя {telegram_id}: {e}")
            return None
    
    async def validate_user_access(self, telegram_user: TelegramUser, resource_id: str) -> bool:
        """
        Проверяет права доступа пользователя к ресурсу
        
        Args:
            telegram_user: Объект пользователя Telegram
            resource_id: ID ресурса для проверки доступа
            
        Returns:
            True если доступ разрешен, False иначе
        """
        try:
            user = await self.get_or_register_user(telegram_user)
            if not user:
                logger.warning(f"Не удалось получить пользователя для проверки доступа: {telegram_user.id}")
                return False
            
            # Здесь можно добавить дополнительную логику проверки прав
            # Пока что все пользователи имеют доступ к своим ресурсам
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при проверке доступа пользователя {telegram_user.id} к ресурсу {resource_id}: {e}")
            return False
