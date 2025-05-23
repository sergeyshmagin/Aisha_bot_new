"""
Основной модуль приложения.
"""
import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from aisha_v2.app.core.config import settings
from aisha_v2.app.handlers import (
    main_router,
    transcript_main_handler,
    transcript_processing_handler,
)
from aisha_v2.app.handlers.gallery import router as gallery_router
from aisha_v2.app.handlers.avatar import avatar_handler, register_avatar_handlers
from aisha_v2.app.handlers.fallback import fallback_router
from aisha_v2.app.keyboards.main import get_main_menu

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


async def main():
    """
    Основная функция запуска бота
    """
    logger.info("Запуск бота...")

    # Инициализация бота и диспетчера
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация роутеров
    dp.include_router(main_router)
    dp.include_router(gallery_router)
    
    # Регистрация обработчиков аватаров
    await register_avatar_handlers()
    from aisha_v2.app.handlers.avatar import router as avatar_router
    dp.include_router(avatar_router)
    
    # Регистрация обработчиков транскриптов
    await transcript_main_handler.register_handlers()
    await transcript_processing_handler.register_handlers()
    
    dp.include_router(transcript_main_handler.router)
    dp.include_router(transcript_processing_handler.router)

    # Регистрируем fallback_router последним
    dp.include_router(fallback_router)

    @dp.message(Command("start"))
    async def cmd_start(message: Message, state: FSMContext):
        try:
            # Отправить главное меню
            await message.answer(
                "👋 Добро пожаловать в Aisha Bot!\n\nВыберите действие:",
                reply_markup=get_main_menu()
            )
        except Exception as e:
            logger.error(f"Ошибка в команде /start: {e}")
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")

    # Запуск бота
    try:
        logger.info("Запуск polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        logger.info("Старт приложения")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"Ошибка при запуске бота: {e}")
