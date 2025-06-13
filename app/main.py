"""
Основной модуль приложения.
"""
import asyncio
import logging
import signal
import sys
import os
from contextlib import asynccontextmanager
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.core.config import settings
from app.core.logger import get_logger
from app.core.session import close_db_connection
from app.handlers import main_router
from app.handlers.avatar import router as avatar_router
from app.handlers.generation.main_handler import router as generation_router
from app.handlers.profile.router import profile_router
from app.handlers.fallback import fallback_router

# Импорты для дополнительных роутеров
try:
    from app.handlers.main import router as debug_router
except ImportError:
    logger.warning("Debug router не найден, создаем заглушку")
    from aiogram import Router
    debug_router = Router(name="debug_stub")

try:
    from app.handlers.imagen4 import imagen4_router
except ImportError:
    logger.warning("Imagen4 router не найден, создаем заглушку") 
    from aiogram import Router
    imagen4_router = Router(name="imagen4_stub")

try:
    from app.handlers.gallery import main_router as gallery_main_router, filter_router as gallery_filter_router
except ImportError:
    logger.warning("Gallery routers не найдены, создаем заглушки")
    from aiogram import Router
    gallery_main_router = Router(name="gallery_main_stub")
    gallery_filter_router = Router(name="gallery_filter_stub")
from app.middlewares import register_all_middlewares

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

# Проверка режима работы
BOT_MODE = os.getenv("BOT_MODE", "polling")
SET_POLLING = os.getenv("SET_POLLING", "true").lower() == "true"
INSTANCE_ID = os.getenv("INSTANCE_ID", "unknown")


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


@asynccontextmanager
async def bot_lifetime():
    """Контекстный менеджер для управления жизненным циклом бота"""
    try:
        # Запускаем бота
        logger.info("Запуск бота...")
        yield
    finally:
        # Останавливаем бота
        logger.info("Остановка бота...")
        await bot_instance.session.close()
        await close_db_connection()
        logger.info("Бот остановлен")


async def on_startup(app: Optional[web.Application] = None):
    """Действия при запуске"""
    logger.info("Бот запущен")


async def on_shutdown(app: Optional[web.Application] = None):
    """Действия при остановке"""
    logger.info("Бот останавливается...")
    await bot_instance.session.close()
    await close_db_connection()
    logger.info("Бот остановлен")


async def main():
    """
    Основная функция запуска бота
    """
    global bot_instance
    
    logger.info(f"🚀 Запуск бота - Экземпляр: {INSTANCE_ID}")
    logger.info(f"📋 Режим работы: {BOT_MODE}")
    logger.info(f"📡 Polling разрешен: {SET_POLLING}")

    # Инициализация бота и диспетчера с явной конфигурацией timeout
    try:
        # Создаем Bot с новым подходом aiogram 3.x
        from aiogram.client.default import DefaultBotProperties
        bot_instance = Bot(
            token=settings.effective_telegram_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        logger.info(f"✅ Bot создан с токеном для окружения: {settings.ENVIRONMENT}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания Bot: {e}")
        raise
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация роутеров
    dp.include_router(main_router)  # Уже содержит новую модульную структуру меню
    dp.include_router(debug_router)
    
    # ==================== LEGACY РОУТЕРЫ (ЗАКОММЕНТИРОВАНЫ) ====================
    # TODO: Удалить после полного перехода на новую структуру
    
    # LEGACY: Старый профиль - заменен на app/handlers/menu/
    # dp.include_router(profile_router)
    
    # LEGACY: Старая галерея - интегрирована в новое меню
    # dp.include_router(gallery_main_router)
    # dp.include_router(gallery_filter_router)
    
    # ==================== АКТИВНЫЕ РОУТЕРЫ ====================
    # Эти роутеры остаются активными
    
    # Регистрация роутера аватаров
    dp.include_router(avatar_router)
    
    # Регистрация роутера генерации изображений
    dp.include_router(generation_router)
    
    # Регистрация роутера Imagen 4
    dp.include_router(imagen4_router)
    
    # Регистрируем галерею
    # dp.include_router(gallery_main_router)
    # dp.include_router(gallery_filter_router)
    
    # Регистрируем личный кабинет пользователя
    # dp.include_router(profile_router)
    
    # ==================== TRANSCRIPT HANDLERS (ВРЕМЕННО ОТКЛЮЧЕНЫ) ====================
    # TODO: Восстановить после рефакторинга или удалить если не нужны
    # await transcript_main_handler.register_handlers()
    # await transcript_processing_handler.register_handlers()
    # dp.include_router(transcript_main_handler.router)
    # dp.include_router(transcript_processing_handler.router)
    
    # ==================== TRANSCRIPT PROCESSING (ВРЕМЕННО ОТКЛЮЧЕНО) ====================
    # TODO: Восстановить если эти модули нужны
    # from app.handlers.transcript_processing.paid_transcription_handler import router as paid_transcription_router
    # from app.handlers.transcript_processing.promo_handler import router as promo_router
    # dp.include_router(paid_transcription_router)
    # dp.include_router(promo_router)

    # Регистрируем fallback_router последним для ловли необработанных сообщений
    dp.include_router(fallback_router)

    # Регистрируем обработчики и middleware
    register_all_middlewares(dp)

    # Регистрируем обработчики запуска/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запускаем бота
    async with bot_lifetime():
        if settings.TELEGRAM_WEBHOOK_URL:
            # Webhook режим
            app = web.Application()
            webhook_handler = SimpleRequestHandler(
                dispatcher=dp,
                bot=bot_instance,
            )
            webhook_handler.register(app, path=settings.TELEGRAM_WEBHOOK_PATH)
            setup_application(app, dp, bot=bot_instance)
            
            # Запускаем webhook сервер
            await web._run_app(
                app,
                host=settings.TELEGRAM_WEBHOOK_HOST,
                port=settings.TELEGRAM_WEBHOOK_PORT
            )
        else:
            # Long polling режим
            await dp.start_polling(bot_instance)


if __name__ == "__main__":
    # Настройка обработчиков сигналов для graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("Старт приложения")
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Получен сигнал остановки...")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
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
