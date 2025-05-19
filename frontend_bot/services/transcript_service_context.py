"""
Контекстный менеджер для TranscriptService.
"""

from database.config import AsyncSessionLocal
from frontend_bot.services.transcript_service import TranscriptService

class TranscriptServiceContext:
    def __init__(self):
        self._service = None
        self._session = None

    async def __aenter__(self) -> TranscriptService:
        self._session = AsyncSessionLocal()
        self._service = TranscriptService(self._session)
        await self._service.init()
        return self._service

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

# Создаем глобальный экземпляр контекстного менеджера
transcript_service_context = TranscriptServiceContext() 