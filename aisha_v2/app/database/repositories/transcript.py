"""
Репозиторий для работы с транскриптами
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aisha_v2.app.database.models import UserTranscript
from aisha_v2.app.database.repositories.base import BaseRepository


class TranscriptRepository(BaseRepository[UserTranscript]):
    """
    Репозиторий для работы с транскриптами
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserTranscript)

    async def get_user_transcripts(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[UserTranscript]:
        """Получить транскрипты пользователя с пагинацией"""
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
        stmt = select(self.model).where(
            self.model.user_id == user_id, self.model.id == transcript_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_user_transcripts(self, user_id: int) -> int:
        """Подсчитать количество транскриптов пользователя"""
        stmt = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(stmt)
        return len(list(result.scalars().all()))
