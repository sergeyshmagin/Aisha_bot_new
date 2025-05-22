"""
Базовый класс для обработчиков транскриптов.
"""
import logging
from typing import Optional
from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from aisha_v2.app.core.database import get_session
from aisha_v2.app.utils.uuid_utils import safe_uuid

logger = logging.getLogger(__name__)

class TranscriptBaseHandler:
    """
    Базовый класс для обработчиков транскриптов.
    Содержит общие методы и утилиты.
    """
    
    def __init__(self):
        """Инициализация базового обработчика"""
        self.session = None
    
    async def get_session(self):
        """Получение сессии базы данных"""
        if not self.session:
            self.session = await get_session()
        return self.session
    
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
    
    async def register_handlers(self, dp: Dispatcher):
        """
        Регистрация обработчиков
        
        Args:
            dp: Диспетчер aiogram
        """
        raise NotImplementedError("Метод register_handlers должен быть реализован в дочернем классе")
