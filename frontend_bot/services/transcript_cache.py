"""
Сервис для работы с кэшем последних транскриптов пользователя (user_transcript_cache).
"""
from typing import Optional, Dict
from database.config import AsyncSessionLocal
from database.models import UserTranscriptCache
from sqlalchemy import select, update, delete
from datetime import datetime
from uuid import UUID
import logging

logger = logging.getLogger("transcript_cache")

async def get(user_id: UUID) -> Optional[str]:
    """
    Получает путь к транскрипту из БД.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Optional[str]: Путь к транскрипту или None
    """
    async with AsyncSessionLocal() as session:
        query = select(UserTranscriptCache).where(UserTranscriptCache.user_id == user_id)
        result = await session.execute(query)
        cache = result.scalar_one_or_none()
        logger.info(f"[transcript_cache.get] user_id={user_id} → path={cache.path if cache else None}")
        return cache.path if cache else None

async def set(user_id: UUID, path: str) -> None:
    """
    Сохраняет путь к транскрипту в БД.
    
    Args:
        user_id: ID пользователя
        path: Путь к транскрипту
    """
    async with AsyncSessionLocal() as session:
        # upsert: если есть — обновить, иначе создать
        query = select(UserTranscriptCache).where(UserTranscriptCache.user_id == user_id)
        result = await session.execute(query)
        cache = result.scalar_one_or_none()
        if cache:
            cache.path = path
            cache.created_at = datetime.utcnow()
            logger.info(f"[transcript_cache.set] update user_id={user_id}, path={path}")
        else:
            cache = UserTranscriptCache(user_id=user_id, path=path, created_at=datetime.utcnow())
            session.add(cache)
            logger.info(f"[transcript_cache.set] insert user_id={user_id}, path={path}")
        await session.commit()

async def remove(user_id: UUID) -> None:
    """
    Удаляет транскрипт из БД.
    
    Args:
        user_id: ID пользователя
    """
    async with AsyncSessionLocal() as session:
        await session.execute(delete(UserTranscriptCache).where(UserTranscriptCache.user_id == user_id))
        await session.commit()
        logger.info(f"[transcript_cache.remove] user_id={user_id}")

async def clear() -> None:
    """Очищает все устаревшие транскрипты из БД."""
    async with AsyncSessionLocal() as session:
        await session.execute(delete(UserTranscriptCache))
        await session.commit()
        logger.info("[transcript_cache.clear] all cache cleared")

async def all() -> Dict[UUID, str]:
    """
    Получает все активные транскрипты из БД.
    
    Returns:
        Dict[UUID, str]: Словарь {user_id: path}
    """
    async with AsyncSessionLocal() as session:
        query = select(UserTranscriptCache)
        result = await session.execute(query)
        caches = result.scalars().all()
        logger.info(f"[transcript_cache.all] count={len(caches)}")
        return {cache.user_id: cache.path for cache in caches} 