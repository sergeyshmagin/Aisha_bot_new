"""
Handlers для Telegram-бота
"""

from app.handlers.main_menu import router as main_router
from app.handlers.main import router as debug_router
from app.handlers.transcript_main.main_handler import TranscriptMainHandler
from app.handlers.transcript_processing.main_handler import TranscriptProcessingHandler
from app.handlers.imagen4 import imagen4_router

# Галерея
from app.handlers.gallery import main_router as gallery_main_router, filter_router as gallery_filter_router

# Современные обработчики
transcript_main_handler = TranscriptMainHandler()
transcript_processing_handler = TranscriptProcessingHandler()

__all__ = [
    "main_router",
    "debug_router",
    "transcript_main_handler", 
    "transcript_processing_handler",
    "imagen4_router",
    "gallery_main_router",
    "gallery_filter_router",
]
