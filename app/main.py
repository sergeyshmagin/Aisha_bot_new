"""
Основной модуль приложения.
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.core.config import settings
from app.handlers import (
    main_router,
    transcript_main_handler,
    transcript_processing_handler,
)
from app.handlers.gallery import router as gallery_router
from app.handlers.avatar import router as avatar_router  # Заменяем Legacy register_avatar_handlers
from app.handlers.fallback import fallback_router
from app.keyboards.main import get_main_menu

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


async def startup_tasks():
    """
    Задачи, выполняемые при запуске приложения
    """
    logger.info("🚀 Выполнение задач запуска...")
    
    try:
        # Проверяем и восстанавливаем мониторинг зависших аватаров
        from app.services.avatar.fal_training_service.startup_checker import startup_checker
        await startup_checker.check_and_restore_monitoring()
        
        # Запускаем периодические проверки в фоне
        asyncio.create_task(startup_checker.schedule_periodic_checks())
        
        logger.info("✅ Задачи запуска выполнены успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении задач запуска: {e}")


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
    
    # Регистрация роутера аватаров (новая архитектура заменяет Legacy register_avatar_handlers)
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

    # Выполняем задачи запуска
    await startup_tasks()

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
