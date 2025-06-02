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
