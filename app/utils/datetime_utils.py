"""
Утилиты для работы с датой и временем с учетом часового пояса пользователя.
Централизованное решение для отображения времени в проекте.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession

# Ленивый импорт для избежания циклических зависимостей
if TYPE_CHECKING:
    from app.services.user import UserService

from app.utils.timezone import TimezoneUtils

logger = logging.getLogger(__name__)


class DateTimeManager:
    """Менеджер для работы с датой и временем с учетом часового пояса пользователя."""
    
    def __init__(self, user_service: Optional["UserService"] = None):
        self.user_service = user_service
        self._default_timezone = "UTC+3"  # Москва по умолчанию
    
    async def get_user_timezone(self, user_id: int) -> str:
        """Получить часовой пояс пользователя."""
        if not self.user_service:
            return self._default_timezone
        
        try:
            user_timezone = await self.user_service.get_user_timezone(user_id)
            return user_timezone or self._default_timezone
        except Exception as e:
            logger.warning(f"Ошибка получения часового пояса для пользователя {user_id}: {e}")
            return self._default_timezone
    
    async def format_datetime_for_user(
        self,
        dt: Union[datetime, str, int, None],
        user_id: int,
        format_str: str = "%d.%m.%Y %H:%M"
    ) -> str:
        """
        Форматировать дату-время для пользователя с учетом его часового пояса.
        
        Args:
            dt: Дата-время для форматирования
            user_id: ID пользователя для получения часового пояса
            format_str: Формат вывода даты
            
        Returns:
            Отформатированная строка с датой
        """
        if dt is None:
            return "—"
        
        try:
            # Конвертируем в datetime если нужно
            if isinstance(dt, str):
                # Пытаемся распарсить ISO формат
                if 'T' in dt or dt.endswith('Z'):
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                else:
                    return dt  # Возвращаем как есть если не можем распарсить
            elif isinstance(dt, int):
                dt = datetime.fromtimestamp(dt, tz=timezone.utc)
            elif not isinstance(dt, datetime):
                return str(dt)
            
            # Получаем часовой пояс пользователя
            user_timezone = await self.get_user_timezone(user_id)
            
            # Применяем часовой пояс и форматируем
            return TimezoneUtils.format_date_with_timezone(dt, user_timezone, format_str)
            
        except Exception as e:
            logger.error(f"Ошибка форматирования даты для пользователя {user_id}: {e}")
            return str(dt) if dt else "—"
    
    async def format_created_at(self, obj: any, user_id: int) -> str:
        """Форматировать поле created_at объекта."""
        created_at = getattr(obj, 'created_at', None)
        return await self.format_datetime_for_user(created_at, user_id)
    
    async def format_updated_at(self, obj: any, user_id: int) -> str:
        """Форматировать поле updated_at объекта."""
        updated_at = getattr(obj, 'updated_at', None)
        return await self.format_datetime_for_user(updated_at, user_id)
    
    def now_utc(self) -> datetime:
        """Получить текущее время в UTC."""
        return datetime.now(timezone.utc)
    
    async def now_for_user(self, user_id: int) -> datetime:
        """Получить текущее время в часовом поясе пользователя."""
        utc_now = self.now_utc()
        user_timezone = await self.get_user_timezone(user_id)
        return TimezoneUtils.apply_timezone(utc_now, user_timezone)


# Глобальный экземпляр для использования без DI
_global_datetime_manager: Optional[DateTimeManager] = None


def get_global_datetime_manager() -> DateTimeManager:
    """Получить глобальный экземпляр DateTimeManager."""
    global _global_datetime_manager
    if _global_datetime_manager is None:
        _global_datetime_manager = DateTimeManager()
    return _global_datetime_manager


def set_global_datetime_manager(user_service):
    """Установить глобальный DateTimeManager с UserService."""
    global _global_datetime_manager
    _global_datetime_manager = DateTimeManager(user_service)


# Функции-утилиты для быстрого доступа
async def format_datetime_for_user(
    dt: Union[datetime, str, int, None],
    user_id: int,
    format_str: str = "%d.%m.%Y %H:%M"
) -> str:
    """Быстрая функция для форматирования даты для пользователя."""
    manager = get_global_datetime_manager()
    return await manager.format_datetime_for_user(dt, user_id, format_str)


async def format_created_at(obj: any, user_id: int) -> str:
    """Быстрая функция для форматирования created_at."""
    manager = get_global_datetime_manager()
    return await manager.format_created_at(obj, user_id)


async def format_updated_at(obj: any, user_id: int) -> str:
    """Быстрая функция для форматирования updated_at."""
    manager = get_global_datetime_manager()
    return await manager.format_updated_at(obj, user_id)


def now_utc() -> datetime:
    """Получить текущее время в UTC."""
    return datetime.now(timezone.utc)


async def now_for_user(user_id: int) -> datetime:
    """Получить текущее время в часовом поясе пользователя."""
    manager = get_global_datetime_manager()
    return await manager.now_for_user(user_id) 