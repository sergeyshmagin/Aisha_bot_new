"""
Middleware для работы с базой данных
"""
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from app.core.logger import get_logger
from app.core.session import get_session

logger = get_logger(__name__)

class DatabaseMiddleware(BaseMiddleware):
    """Middleware для управления сессиями БД"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Обработка события"""
        try:
            # Создаем сессию БД
            async with get_session() as session:
                # Добавляем сессию в данные
                data["session"] = session
                
                # Вызываем следующий обработчик
                return await handler(event, data)
                
        except Exception as e:
            logger.exception(f"❌ Ошибка в database middleware: {e}")
            raise 