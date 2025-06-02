"""
Обработчик часовых поясов для приложения
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.utils.timezone import TimezoneUtils
from app.services.user import UserService

logger = logging.getLogger(__name__)class TimezoneHandler:
    """
    Обработчик часовых поясов для приложения
    
    Этот класс предоставляет методы для работы с часовыми поясами пользователей,
    включая форматирование дат и получение часовых поясов из Telegram.
    """
    
    def __init__(self, user_service: UserService):
        """
        Инициализация обработчика часовых поясов
        
        Args:
            user_service: Сервис пользователей для получения часовых поясов
        """
        self.user_service = user_service
    
    async def get_user_timezone(self, user_id: int) -> str:
        """
        Получить часовой пояс пользователя
        
        Args:
            user_id: ID пользователя в Telegram
            
        Returns:
            Строка с часовым поясом пользователя (например, "UTC+5")
        """
        try:
            return await self.user_service.get_user_timezone(user_id)
        except Exception as e:
            logger.error(f"Ошибка при получении часового пояса пользователя: {e}")
            return "UTC+5"  # Значение по умолчанию
    
    async def format_date(
        self, 
        dt: datetime, 
        user_id: int, 
        format_str: str = "%d.%m.%Y %H:%M"
    ) -> str:
        """
        Форматировать дату с учетом часового пояса пользователя
        
        Args:
            dt: Дата для форматирования
            user_id: ID пользователя в Telegram
            format_str: Строка формата (по умолчанию "%d.%m.%Y %H:%M")
            
        Returns:
            Отформатированная строка даты с учетом часового пояса
        """
        timezone = await self.get_user_timezone(user_id)
        return TimezoneUtils.format_date_with_timezone(dt, timezone, format_str)
    
    async def format_metadata_date(
        self, 
        metadata: Dict[str, Any], 
        user_id: int,
        date_key: str = "created_at",
        format_str: str = "%d.%m.%Y %H:%M"
    ) -> str:
        """
        Форматировать дату из метаданных с учетом часового пояса пользователя
        
        Args:
            metadata: Словарь с метаданными
            user_id: ID пользователя в Telegram
            date_key: Ключ для даты в метаданных (по умолчанию "created_at")
            format_str: Строка формата (по умолчанию "%d.%m.%Y %H:%M")
            
        Returns:
            Отформатированная строка даты с учетом часового пояса
        """
        try:
            created_at = metadata.get(date_key)
            if not created_at:
                return "неизвестно"
                
            timezone = await self.get_user_timezone(user_id)
            return TimezoneUtils.format_date_with_timezone(created_at, timezone, format_str)
        except Exception as e:
            logger.error(f"Ошибка при форматировании даты из метаданных: {e}")
            return "неизвестно"
