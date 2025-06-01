"""
Основной модуль приложения.
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import settings
from app.handlers import (
    main_router,
    debug_router,
    transcript_main_handler,
    transcript_processing_handler,
)
from app.handlers.gallery import router as gallery_router  # LEGACY: Старая галерея, заменена на generation system
from app.handlers.avatar import router as avatar_router  # Заменяем Legacy register_avatar_handlers
from app.handlers.generation.main_handler import router as generation_router  # Новый роутер генерации
from app.handlers.fallback import fallback_router

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
    dp.include_router(debug_router)
    dp.include_router(gallery_router)  # LEGACY: Старая галерея (пустой роутер)
    
    # Регистрация роутера аватаров (новая архитектура заменяет Legacy register_avatar_handlers)
    dp.include_router(avatar_router)
    
    # Регистрация роутера генерации изображений
    dp.include_router(generation_router)
    
    # Регистрация обработчиков транскриптов
    await transcript_main_handler.register_handlers()
    await transcript_processing_handler.register_handlers()
    
    dp.include_router(transcript_main_handler.router)
    dp.include_router(transcript_processing_handler.router)

    # Регистрируем fallback_router последним для ловли необработанных сообщений
    dp.include_router(fallback_router)

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
