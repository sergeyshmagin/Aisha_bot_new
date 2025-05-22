"""
Обработчики команд
"""
from aisha_v2.app.handlers.main_menu import router as main_router
from aisha_v2.app.handlers.business import router as business_router
from aisha_v2.app.handlers.gallery import router as gallery_router
from aisha_v2.app.handlers.avatar import handler

# Legacy handlers (to be refactored)
from aisha_v2.app.handlers.transcript_main import TranscriptMainHandler
from aisha_v2.app.handlers.transcript_processing import TranscriptProcessingHandler
from aisha_v2.app.handlers.transcript_view import TranscriptViewHandler
from aisha_v2.app.handlers.transcript_management import TranscriptManagementHandler

__all__ = [
    # New routers
    "main_router",
    "business_router",
    "gallery_router",
    "handler",
    
    # Legacy handlers (to be refactored)
    "TranscriptMainHandler",
    "TranscriptProcessingHandler",
    "TranscriptViewHandler",
    "TranscriptManagementHandler",
]
