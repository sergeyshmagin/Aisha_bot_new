"""
Handlers для Telegram-бота
"""

from aisha_v2.app.handlers.main_menu import router as main_router
from aisha_v2.app.handlers.transcript_main import TranscriptMainHandler
from aisha_v2.app.handlers.transcript_processing import TranscriptProcessingHandler

# Современные обработчики
transcript_main_handler = TranscriptMainHandler()
transcript_processing_handler = TranscriptProcessingHandler()

__all__ = [
    "main_router",
    "transcript_main_handler", 
    "transcript_processing_handler",
]
