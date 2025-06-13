"""
Redis утилиты
"""
import logging
import uuid
from typing import Optional
import redis.asyncio as redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry

from app.core.config import settings

logger = logging.getLogger(__name__)

# Конфигурация Redis
REDIS_CONFIG = {
    "host": settings.REDIS_HOST,
    "port": settings.REDIS_PORT,
    "db": settings.REDIS_DB,
    "password": settings.REDIS_PASSWORD,
    "ssl": settings.REDIS_SSL,
    "socket_timeout": 5.0,
    "socket_connect_timeout": 5.0,
    "max_connections": settings.REDIS_POOL_SIZE,
    "retry": Retry(ExponentialBackoff(), retries=settings.REDIS_MAX_RETRIES),
}

async def acquire_lock(key: str, expire: int = 60) -> Optional[str]:
    """
    Приобретает блокировку в Redis
    """
    redis_client = redis.Redis(**REDIS_CONFIG)
    try:
        # Генерируем уникальный токен для блокировки
        token = str(uuid.uuid4())
        # Пытаемся установить блокировку
        if await redis_client.set(key, token, ex=expire, nx=True):
            return token
        return None
    finally:
        await redis_client.aclose()

async def release_lock(key: str, token: str) -> bool:
    """
    Освобождает блокировку в Redis
    """
    redis_client = redis.Redis(**REDIS_CONFIG)
    try:
        # Проверяем, что блокировка принадлежит нам
        current_token = await redis_client.get(key)
        if current_token and current_token.decode() == token:
            await redis_client.delete(key)
            return True
        return False
    finally:
        await redis_client.aclose()

async def refresh_lock(key: str, token: str, expire: int = 60) -> bool:
    """
    Обновляет время жизни блокировки
    """
    redis_client = redis.Redis(**REDIS_CONFIG)
    try:
        # Проверяем, что блокировка принадлежит нам
        current_token = await redis_client.get(key)
        if current_token and current_token.decode() == token:
            await redis_client.expire(key, expire)
            return True
        return False
    finally:
        await redis_client.aclose()
