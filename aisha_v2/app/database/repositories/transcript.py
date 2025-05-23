"""
Репозиторий для работы с транскриптами
"""
import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aisha_v2.app.database.models import UserTranscript
from aisha_v2.app.database.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class TranscriptRepository(BaseRepository[UserTranscript]):
    """
    Репозиторий для работы с транскриптами
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserTranscript)

    async def get_user_transcripts(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[UserTranscript]:
        """LEGACY: Получить транскрипты пользователя из БД (без MinIO). Использовать только для миграции."""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_transcript_by_id(
        self, user_id: int, transcript_id: UUID
    ) -> Optional[UserTranscript]:
        """Получить транскрипт по ID"""
        logger.info(f"[REPO] get_transcript_by_id: user_id={user_id} ({type(user_id)}), transcript_id={transcript_id} ({type(transcript_id)})")
        stmt = select(self.model).where(
            self.model.user_id == user_id, self.model.id == transcript_id
        )
        result = await self.session.execute(stmt)
        transcript = result.scalar_one_or_none()
        logger.info(f"[REPO] get_transcript_by_id: найден={transcript is not None}")
        return transcript
        
    async def get_transcript_by_id_only(
        self, transcript_id: UUID
    ) -> Optional[UserTranscript]:
        """Получить транскрипт только по ID (без проверки user_id)"""
        logger.info(f"[REPO] get_transcript_by_id_only: transcript_id={transcript_id} ({type(transcript_id)})")
        stmt = select(self.model).where(self.model.id == transcript_id)
        result = await self.session.execute(stmt)
        transcript = result.scalar_one_or_none()
        logger.info(f"[REPO] get_transcript_by_id_only: найден={transcript is not None}")
        if transcript:
            logger.info(f"[REPO] get_transcript_by_id_only: transcript.user_id={transcript.user_id} ({type(transcript.user_id)})")
        return transcript

    async def count_user_transcripts(self, user_id: int) -> int:
        """Подсчитать количество транскриптов пользователя"""
        stmt = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(stmt)
        return len(list(result.scalars().all()))
