"""
Handlers для Telegram-бота
"""

from app.handlers.main_menu import router as main_router
from app.handlers.transcript_main import TranscriptMainHandler
from app.handlers.transcript_processing import TranscriptProcessingHandler

# Современные обработчики
transcript_main_handler = TranscriptMainHandler()
transcript_processing_handler = TranscriptProcessingHandler()

__all__ = [
    "main_router",
    "transcript_main_handler", 
    "transcript_processing_handler",
]
