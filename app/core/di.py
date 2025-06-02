"""
Dependency Injection контейнер
"""
from functools import lru_cache
from typing import Optional
import logging
from contextlib import asynccontextmanager
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry

from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.services.audio_processing.service import AudioService as AudioProcessingService
from app.services.avatar_db import AvatarService
