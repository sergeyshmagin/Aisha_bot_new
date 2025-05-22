"""
Dependency Injection контейнер
"""
from functools import lru_cache
from typing import Optional
import logging
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry

from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession

from aisha_v2.app.core.config import settings
from aisha_v2.app.services.audio.service import AudioProcessingService
from aisha_v2.app.services.avatar_db import AvatarService
from aisha_v2.app.services.backend import BackendService
from aisha_v2.app.services.text_processing import TextProcessingService
from aisha_v2.app.services.transcript import TranscriptService
from aisha_v2.app.services.user import UserService

logger = logging.getLogger(__name__)

# Глобальные экземпляры сервисов
_redis_client: Optional[Redis] = None
_state_storage: Optional[RedisStorage] = None

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
        secure=False
    )


def get_user_service(session: AsyncSession) -> UserService:
    """
    Получение сервиса для работы с пользователями
    """
    return UserService(session)


def get_avatar_service(session: AsyncSession) -> AvatarService:
    """
    Получение сервиса для работы с аватарами
    """
    return AvatarService(session)


def get_backend_service(session: AsyncSession, http_session=None) -> BackendService:
    """
    Получение сервиса для работы с Backend API
    """
    return BackendService(http_session, session)


def get_transcript_service(session: AsyncSession) -> TranscriptService:
    """
    Получение сервиса для работы с транскриптами
    """
    return TranscriptService(session)


def get_audio_processing_service(session: AsyncSession) -> AudioProcessingService:
    """
    Получение сервиса для обработки аудио
    """
    return AudioProcessingService()


def get_text_processing_service(session: AsyncSession) -> TextProcessingService:
    """
    Получение сервиса для обработки текста
    """
    return TextProcessingService(session)
