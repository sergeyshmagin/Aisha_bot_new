"""
Dependency Injection контейнер
"""

import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Optional

import redis.asyncio as redis
from aiogram.fsm.storage.redis import RedisStorage
from minio import Minio
from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.services.audio_processing.factory import get_audio_service
from app.services.audio_processing.service import AudioService as AudioProcessingService
from app.services.generation.generation_service import ImageGenerationService
from app.services.text_processing import TextProcessingService
from app.services.transcript import TranscriptService
from app.services.user import UserService
from app.services.audio_processing.factory import get_audio_service
from app.core.database import get_db_session as db_get_db_session
from app.services.generation.generation_service import ImageGenerationService
from app.core.logger import get_logger
from app.utils.timezone_handler import TimezoneHandler

logger = get_logger(__name__)

# Глобальные экземпляры сервисов
_redis_client: Optional[Redis] = None
_state_storage: Optional[RedisStorage] = None

_engine = None
_async_session = None

def get_db_session() -> AsyncSession:
    """Получить сессию БД"""
    return db_get_db_session()


def get_redis_client() -> Redis:
    """
    Получить клиент Redis
    """
    global _redis_client
    if _redis_client is None:
        retry = Retry(ExponentialBackoff(), retries=settings.REDIS_MAX_RETRIES)
        _redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            ssl=settings.REDIS_SSL,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            max_connections=settings.REDIS_POOL_SIZE,
            retry=retry,
        )
    return _redis_client


async def get_redis() -> Redis:
    """
    Асинхронный доступ к Redis клиенту
    """
    return get_redis_client()


def get_state_storage() -> RedisStorage:
    """
    Получить хранилище состояний
    """
    global _state_storage
    if _state_storage is None:
        redis = get_redis_client()
        _state_storage = RedisStorage(redis=redis)
    return _state_storage


@lru_cache
def get_minio_client() -> Minio:
    """
    Получение клиента MinIO
    """
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


@asynccontextmanager
async def get_user_service():
    """
    Контекстный менеджер для получения сервиса пользователей с автоматическим управлением сессией
    """
    session = get_db_session()
    try:
        user_service = UserService(session)
        yield user_service
        # Если дошли до этой точки без исключений, выполняем commit
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise
    finally:
        await session.close()


def get_user_service_with_session(session: AsyncSession) -> UserService:
    """
    Получение сервиса для работы с пользователями с переданной сессией
    """
    return UserService(session)


def get_timezone_handler_with_session(session: AsyncSession) -> TimezoneHandler:
    """Получить TimezoneHandler с переданной сессией."""
    user_service = UserService(session)
    return TimezoneHandler(user_service)


@asynccontextmanager
async def get_avatar_service():
    """
    Контекстный менеджер для получения сервиса аватаров с автоматическим управлением сессией
    """
    session = get_db_session()
    try:
        from app.services.avatar_db import AvatarService

        avatar_service = AvatarService(session)
        yield avatar_service
        # Если дошли до этой точки без исключений, выполняем commit
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager
async def get_avatar_service_with_session(session: AsyncSession):
    """Получить сервис аватаров с переданной сессией (старая версия)"""
    from app.services.avatar_db import AvatarService

    avatar_service = AvatarService(session)
    yield avatar_service


def get_avatar_service_sync(session: AsyncSession):
    """Получить сервис аватаров с сессией (синхронная версия)"""
    from app.services.avatar_db import AvatarService

    return AvatarService(session)


def get_transcript_service(session: AsyncSession) -> TranscriptService:
    """
    Получение сервиса для работы с транскриптами
    """
    return TranscriptService(session)


def get_audio_processing_service(session: AsyncSession) -> AudioProcessingService:
    """
    Получение сервиса для обработки аудио
    """
    return get_audio_service()


def get_text_processing_service(session: AsyncSession) -> TextProcessingService:
    """
    Получение сервиса для обработки текста
    """
    return TextProcessingService(session)


async def get_gallery_service(session: AsyncSession = None):
    """Получить оптимизированный сервис галереи"""
    from app.services.gallery_service import gallery_service

    if session:
        await gallery_service.set_session(session)
    return gallery_service
