"""
Репозиторий для работы с транскриптами пользователей.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import UserTranscript


class UserTranscriptRepository:
    """Репозиторий для работы с транскриптами пользователей."""
    
    def __init__(self, session: AsyncSession):
        """Инициализация репозитория.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session
    
    async def create(self, user_id: str, audio_key: str, transcript_key: str) -> UserTranscript:
        """Создает новый транскрипт пользователя.
        
        Args:
            user_id: ID пользователя
            audio_key: Ключ аудиофайла
            transcript_key: Ключ транскрипта
            
        Returns:
            Созданный транскрипт
        """
        transcript = UserTranscript(
            user_id=user_id,
            audio_key=audio_key,
            transcript_key=transcript_key
        )
        self.session.add(transcript)
        await self.session.commit()
        await self.session.refresh(transcript)
        return transcript
    
    async def get_by_id(self, transcript_id: str) -> Optional[UserTranscript]:
        """Получает транскрипт по ID.
        
        Args:
            transcript_id: ID транскрипта
            
        Returns:
            Транскрипт или None, если не найден
        """
        result = await self.session.execute(
            select(UserTranscript).where(UserTranscript.id == transcript_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: str) -> List[UserTranscript]:
        """Получает все транскрипты пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список транскриптов
        """
        result = await self.session.execute(
            select(UserTranscript).where(UserTranscript.user_id == user_id)
        )
        return result.scalars().all()
    
    async def delete(self, transcript_id: str) -> bool:
        """Удаляет транскрипт.
        
        Args:
            transcript_id: ID транскрипта
            
        Returns:
            True, если транскрипт был удален, иначе False
        """
        transcript = await self.get_by_id(transcript_id)
        if transcript:
            await self.session.delete(transcript)
            await self.session.commit()
            return True
        return False 