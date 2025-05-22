"""
Основной модуль приложения.
"""
import asyncio
import logging
import os
import sys
import traceback
import uuid
import time
from contextlib import asynccontextmanager
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from aiogram.types import Message
from aiogram.filters import Command

import aiohttp
from telebot.async_telebot import AsyncTeleBot

from aisha_v2.app.core.config import settings
from aisha_v2.app.core.redis import acquire_lock, release_lock, refresh_lock
from aisha_v2.app.handlers import (
    main_router,
    business_router,
    gallery_router,
    handler,
    TranscriptMainHandler,
    TranscriptProcessingHandler,
    TranscriptViewHandler,
    TranscriptManagementHandler,
)
from aisha_v2.app.services.audio.service import AudioProcessingService
from aisha_v2.app.services.storage.minio import MinioStorage
from aisha_v2.app.handlers.audio import AudioHandler, register_handlers, router as audio_router
from aisha_v2.app.handlers.menu import router as menu_router, setup_menu_handlers
from aisha_v2.app.keyboards.main import get_main_menu
from aisha_v2.app.handlers.fallback import fallback_router

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Временно устанавливаем DEBUG уровень
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Константы для блокировки
BOT_LOCK_KEY = "aisha_bot:instance_lock"
BOT_LOCK_EXPIRE = 60  # секунды
BOT_LOCK_REFRESH_INTERVAL = 30  # секунды
BOT_FORCE_RELEASE_LOCK = True  # Принудительно освобождать блокировку при запуске


@asynccontextmanager
async def get_http_session():
    """
    Контекстный менеджер для создания и закрытия HTTP сессии
    """
    async with aiohttp.ClientSession() as session:
        yield session


async def refresh_lock_task(lock_token):
    """
    Задача для периодического обновления блокировки
    """
    while True:
        try:
            # Обновляем блокировку
            success = await refresh_lock(BOT_LOCK_KEY, lock_token, BOT_LOCK_EXPIRE)
            if not success:
                logger.error("Не удалось обновить блокировку. Возможно, она была захвачена другим процессом.")
                return False
            
            # Ждем до следующего обновления
            await asyncio.sleep(BOT_LOCK_REFRESH_INTERVAL)
        except Exception as e:
            logger.error(f"Ошибка при обновлении блокировки: {e}")
            return False


async def main():
    """
    Основная функция запуска бота
    """
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Инициализация бота и диспетчера
    bot = Bot(token=settings.TELEGRAM_TOKEN)
    retry = Retry(ExponentialBackoff(), retries=3)
    redis = Redis(
        host="192.168.0.3",
        port=6379,
        db=0,
        password="wd7QuwAbG0wtyoOOw3Sm",
        ssl=False,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
        max_connections=10,
        retry=retry,
    )
    storage = RedisStorage(redis=redis, key_builder=DefaultKeyBuilder(with_bot_id=True))
    dp = Dispatcher(storage=storage)

    # Регистрация роутеров
    routers = [
        main_router,
        business_router,
        gallery_router,
        handler.router,
        menu_router,
        audio_router,
    ]
    for router in routers:
        dp.include_router(router)
    # Регистрируем fallback_router последним
    dp.include_router(fallback_router)

    # Регистрация legacy-хендлеров (если нужно)
    transcript_main_handler = TranscriptMainHandler()
    transcript_processing_handler = TranscriptProcessingHandler()
    transcript_view_handler = TranscriptViewHandler()
    transcript_management_handler = TranscriptManagementHandler()
    legacy_handlers = [
        transcript_main_handler,
        transcript_processing_handler,
        transcript_view_handler,
        transcript_management_handler,
    ]
    for legacy_handler in legacy_handlers:
        dp.include_router(legacy_handler.router)

    minio_storage = MinioStorage()
    audio_service = AudioProcessingService()
    audio_handler = AudioHandler(
        bot=bot,
        audio_service=audio_service,
        minio_storage=minio_storage
    )
    register_handlers(audio_handler)
    setup_menu_handlers(audio_handler)

    @dp.message(Command("start"))
    async def cmd_start(message: Message):
        await message.answer("Выберите действие:", reply_markup=get_main_menu())

    # Запуск бота
    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        # Проверяем, запущен ли уже бот
        pid = os.getpid()
        logger.info(f"Запуск бота с PID: {pid}")
        
        # Запускаем основную функцию
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"Ошибка при запуске бота: {e}")
