"""
Middleware модуль
"""
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from app.core.logger import get_logger
from .database import DatabaseMiddleware

logger = get_logger(__name__)

class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Обработка события"""
        try:
            # Логируем входящее событие
            if isinstance(event, Message):
                logger.info(f"📨 Получено сообщение от {event.from_user.id}: {event.text}")
            elif isinstance(event, CallbackQuery):
                logger.info(f"🔘 Получен callback от {event.from_user.id}: {event.data}")
            
            # Вызываем следующий обработчик
            return await handler(event, data)
            
        except Exception as e:
            logger.exception(f"❌ Ошибка в middleware: {e}")
            raise

def register_all_middlewares(dp):
    """Регистрирует все middleware"""
    # Регистрируем middleware для логирования
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    # Регистрируем middleware для работы с БД
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware()) 