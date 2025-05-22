"""
Конфигурация для работы с базами данных
"""
from contextlib import asynccontextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from aisha_v2.app.core.config import settings
from aisha_v2.app.database.base import Base

# Инициализируем модели и маппинги
from aisha_v2.app.database.init_models import init_models
registry = init_models()

# Создаем асинхронный движок
async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=settings.DEBUG
)

# Создаем фабрику сессий

# Создаем фабрику сессий для асинхронных операций
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncSession:
    """
    Получить асинхронную сессию БД для FastAPI
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session():
    """
    Контекстный менеджер для асинхронной сессии БД
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# Redis конфигурация
REDIS_CONFIG = {
    "host": settings.REDIS_HOST,
    "port": settings.REDIS_PORT,
    "db": settings.REDIS_DB,
    "password": settings.REDIS_PASSWORD,
    "decode_responses": True,
    "encoding": "utf-8"
}

# MinIO конфигурация
MINIO_CONFIG = {
    "endpoint": settings.MINIO_ENDPOINT,
    "access_key": settings.MINIO_ACCESS_KEY,
    "secret_key": settings.MINIO_SECRET_KEY,
    "secure": settings.MINIO_SECURE,
    "bucket_avatars": settings.MINIO_BUCKET_AVATARS,
    "bucket_photos": settings.MINIO_BUCKET_PHOTOS,
    "bucket_temp": settings.MINIO_BUCKET_TEMP
}
