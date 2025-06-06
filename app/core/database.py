"""
Конфигурация для работы с базами данных
"""
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.database.base import Base

# Инициализируем модели и маппинги
from app.database.init_models import init_models
registry = init_models()

# Создаем асинхронный движок
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)

# Создаем фабрику сессий для асинхронных операций
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncSession:
    """Dependency для FastAPI"""
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
