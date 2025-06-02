"""
Утилитарный класс для работы с часовыми поясами
"""
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Union

logger = logging.getLogger(__name__)class TimezoneUtils:
    """Утилитарный класс для работы с часовыми поясами"""

    @staticmethod
    def parse_timezone(timezone_str: str) -> Optional[Tuple[str, int]]:
        """
        Парсит строку часового пояса в формате UTC+X или UTC-X
        
        Args:
            timezone_str: Строка с часовым поясом (например, "UTC+5")
            
        Returns:
            Кортеж (знак, часы) или None, если формат некорректный
        """
        if not timezone_str:
            return None
            
        match = re.match(r'UTC([+-])(\d+)', timezone_str)
        if match:
            sign, hours = match.groups()
            return sign, int(hours)
        
        logger.warning(f"Некорректный формат часового пояса: {timezone_str}")
        return None

    @staticmethod
    def apply_timezone(dt: datetime, timezone_str: str) -> datetime:
        """
        Применяет смещение часового пояса к дате
        
        Args:
            dt: Исходная дата (предполагается UTC)
            timezone_str: Строка с часовым поясом (например, "UTC+5")
            
        Returns:
            Дата с примененным смещением часового пояса
        """
        if not dt or not timezone_str:
            return dt
            
        timezone_info = TimezoneUtils.parse_timezone(timezone_str)
        if not timezone_info:
            return dt
            
        sign, hours = timezone_info
        
        # Применяем смещение часового пояса
        if sign == '+':
            return dt + timedelta(hours=hours)
        else:
            return dt - timedelta(hours=hours)

    @staticmethod
    def format_date(dt: datetime, format_str: str = "%d.%m.%Y %H:%M") -> str:
        """
        Форматирует дату в строку по заданному формату
        
        Args:
            dt: Дата для форматирования
            format_str: Строка формата (по умолчанию "%d.%m.%Y %H:%M")
            
        Returns:
            Отформатированная строка даты
        """
        if not dt:
            return ""
            
        try:
            return dt.strftime(format_str)
        except Exception as e:
            logger.error(f"Ошибка форматирования даты: {e}")
            return str(dt)

    @staticmethod
    def format_date_with_timezone(
        dt: Union[datetime, str], 
        timezone_str: str, 
        format_str: str = "%d.%m.%Y %H:%M"
    ) -> str:
        """
        Форматирует дату с учетом часового пояса
        
        Args:
            dt: Дата для форматирования (datetime или строка ISO)
            timezone_str: Строка с часовым поясом (например, "UTC+5")
            format_str: Строка формата (по умолчанию "%d.%m.%Y %H:%M")
            
        Returns:
            Отформатированная строка даты с учетом часового пояса
        """
        try:
            # Преобразуем строку в datetime, если нужно
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt)
                except ValueError:
                    return dt
            
            # Применяем часовой пояс и форматируем
            if isinstance(dt, datetime):
                dt_with_tz = TimezoneUtils.apply_timezone(dt, timezone_str)
                return TimezoneUtils.format_date(dt_with_tz, format_str)
            
            return str(dt)
        except Exception as e:
            logger.error(f"Ошибка форматирования даты с часовым поясом: {e}")
            return str(dt)
