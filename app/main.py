"""
Основной модуль приложения.
"""
import asyncio
import logging
import signal
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
from app.handlers.avatar import router as avatar_router
from app.handlers.generation.main_handler import router as generation_router
from app.handlers.gallery import main_router as gallery_main_router, filter_router as gallery_filter_router
from app.handlers.profile.router import profile_router
from app.handlers.fallback import fallback_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Глобальные переменные для корректного завершения
bot_instance = None
background_tasks = set()


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
        task = asyncio.create_task(startup_checker.schedule_periodic_checks())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
        
        logger.info("✅ Задачи запуска выполнены успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении задач запуска: {e}")


async def shutdown_handler():
    """
    Корректное завершение приложения
    """
    logger.info("🔄 Начинаем корректное завершение приложения...")
    
    try:
        # Отменяем все фоновые задачи
        if background_tasks:
            logger.info(f"⏹️ Отменяем {len(background_tasks)} фоновых задач...")
            for task in background_tasks:
                if not task.done():
                    task.cancel()
            
            # Ждем завершения отмененных задач
            if background_tasks:
                await asyncio.gather(*background_tasks, return_exceptions=True)
        
        # Закрываем сессию бота
        if bot_instance and bot_instance.session:
            logger.info("🔐 Закрываем сессию бота...")
            await bot_instance.session.close()
        
        # Закрываем подключения к базе данных
        try:
            from app.core.di import _engine, _redis_client
            if _engine:
                logger.info("🗄️ Закрываем подключения к базе данных...")
                await _engine.dispose()
            
            # Закрываем Redis подключение
            if _redis_client:
                logger.info("🟥 Закрываем подключение к Redis...")
                await _redis_client.aclose()
                
        except Exception as db_error:
            logger.warning(f"Предупреждение при закрытии ресурсов: {db_error}")
        
        # Даем время на завершение всех операций
        await asyncio.sleep(0.1)
        
        logger.info("✅ Приложение корректно завершено")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при завершении приложения: {e}")


def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info(f"🛑 Получен сигнал {signum}, начинаем завершение...")
    raise KeyboardInterrupt()


async def main():
    """
    Основная функция запуска бота
    """
    global bot_instance
    
    logger.info("Запуск бота...")

    # Инициализация бота и диспетчера
    bot_instance = Bot(token=settings.TELEGRAM_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация роутеров
    dp.include_router(main_router)
    dp.include_router(debug_router)
    
    # Регистрация роутера аватаров
    dp.include_router(avatar_router)
    
    # Регистрация роутера генерации изображений
    dp.include_router(generation_router)
    
    # Регистрируем галерею
    dp.include_router(gallery_main_router)
    dp.include_router(gallery_filter_router)
    
    # Регистрируем личный кабинет пользователя
    dp.include_router(profile_router)
    
    # Регистрация обработчиков транскриптов
    await transcript_main_handler.register_handlers()
    await transcript_processing_handler.register_handlers()
    
    dp.include_router(transcript_main_handler.router)
    dp.include_router(transcript_processing_handler.router)
    
    # Регистрация роутеров платной транскрипции и промо-кодов
    from app.handlers.transcript_processing.paid_transcription_handler import router as paid_transcription_router
    from app.handlers.transcript_processing.promo_handler import router as promo_router
    dp.include_router(paid_transcription_router)
    dp.include_router(promo_router)

    # Регистрируем fallback_router последним для ловли необработанных сообщений
    dp.include_router(fallback_router)

    # Выполняем задачи запуска
    await startup_tasks()

    # Запуск бота
    try:
        logger.info("Запуск polling...")
        await dp.start_polling(bot_instance)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        # Корректное завершение
        await shutdown_handler()


if __name__ == "__main__":
    # Настройка обработчиков сигналов для graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("Старт приложения")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"Ошибка при запуске бота: {e}")
    finally:
        # Финальная очистка на уровне event loop
        try:
            # Получаем текущий loop если он еще существует
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                # Отменяем все оставшиеся задачи
                pending = asyncio.all_tasks(loop)
                if pending:
                    logger.info(f"🧹 Отменяем {len(pending)} оставшихся задач...")
                    for task in pending:
                        task.cancel()
                    
                    # Ждем завершения отмененных задач
                    try:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except Exception:
                        pass
        except Exception as cleanup_error:
            # Игнорируем ошибки финальной очистки
            pass
        
        logger.info("🏁 Финальная очистка завершена")
