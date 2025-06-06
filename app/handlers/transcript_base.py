"""
Базовый класс для обработчиков транскриптов.
"""
import logging
from typing import Optional, Dict, Any
from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, User as TelegramUser
from abc import ABC, abstractmethod

from app.core.database import get_session
from app.utils.uuid_utils import safe_uuid
from app.core.di import get_user_service_with_session
from app.services.user import UserService
from app.database.models import User

logger = logging.getLogger(__name__)

class TranscriptBaseHandler(ABC):
    """
    Базовый класс для обработчиков транскриптов.
    Содержит общие методы и утилиты.
    """
    
    def __init__(self):
        """Инициализация базового обработчика"""
        pass  # self.session больше не нужен
    
    def get_session(self):
        """Получение контекстного менеджера сессии базы данных"""
        return get_session()
    
    async def _safe_delete_message(self, message: Message, reason: str = "Удаление сообщения"):
        """
        Безопасное удаление сообщения
        
        Args:
            message: Сообщение для удаления
            reason: Причина удаления
        """
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение ({reason}): {e}")
    
    async def _get_transcript_id(self, message: Message) -> Optional[str]:
        """
        Получение ID транскрипта из сообщения
        
        Args:
            message: Сообщение
            
        Returns:
            Optional[str]: ID транскрипта или None
        """
        try:
            # Пытаемся получить ID из текста сообщения
            text = message.text or message.caption
            if not text:
                return None
            
            # Ищем UUID в тексте
            transcript_id = safe_uuid(text)
            if transcript_id:
                return str(transcript_id)
            
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении ID транскрипта: {e}")
            return None
    
    async def get_or_register_user(self, telegram_user: TelegramUser, session) -> Optional[User]:
        """
        Получить пользователя или зарегистрировать его автоматически
        
        Args:
            telegram_user: Объект пользователя Telegram
            session: Сессия базы данных
            
        Returns:
            Optional[User]: Пользователь или None при ошибке
        """
        user_service = get_user_service_with_session(session)
        user = await user_service.get_user_by_telegram_id(telegram_user.id)
        
        if not user:
            # Автоматически регистрируем пользователя
            user_data = {
                "id": telegram_user.id,
                "username": telegram_user.username,
                "first_name": telegram_user.first_name,
                "last_name": telegram_user.last_name,
                "language_code": telegram_user.language_code or "ru",
                "is_bot": telegram_user.is_bot,
                "is_premium": getattr(telegram_user, "is_premium", False)
            }
            user = await user_service.register_user(user_data)
            
        return user

    @abstractmethod
    async def register_handlers(self, dp: Dispatcher):
        """
        Регистрация обработчиков
        
        Args:
            dp: Диспетчер aiogram
        """
        pass
