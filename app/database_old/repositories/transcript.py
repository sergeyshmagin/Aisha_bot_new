"""
Репозиторий для работы с транскриптами
"""
import logging
from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserTranscript
from app.database.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class TranscriptRepository(BaseRepository[UserTranscript]):
    """
    Репозиторий для работы с транскриптами
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserTranscript)

    async def get_user_transcripts(
        self, 
        user_id: Union[int, str, UUID], 
        limit: int = 10, 
        offset: int = 0
    ) -> List[UserTranscript]:
        """
        Получить транскрипты пользователя с пагинацией
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество записей
            offset: Смещение для пагинации
            
        Returns:
            Список транскриптов пользователя
        """
        logger.info(f"[REPO] get_user_transcripts: user_id={user_id}, limit={limit}, offset={offset}")
        
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(desc(self.model.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(stmt)
        transcripts = result.scalars().all()
        
        logger.info(f"[REPO] get_user_transcripts: найдено {len(transcripts)} записей")
        return list(transcripts)

    async def get_transcript_by_id(
        self, user_id: Union[int, str, UUID], transcript_id: UUID
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

    async def count_user_transcripts(self, user_id: Union[int, str, UUID]) -> int:
        """Подсчитать количество транскриптов пользователя"""
        stmt = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(stmt)
        return len(list(result.scalars().all()))
