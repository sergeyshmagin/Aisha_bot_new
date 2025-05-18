"""
Конфигурация для тестов.
"""

import os
import pytest
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import Base
import uuid
import asyncio
from minio import Minio
from frontend_bot.config.test_config import TestConfig
from tests.test_config import test_settings
from datetime import datetime
from typing import Dict, Any, Generator
from sqlalchemy.ext.asyncio import async_sessionmaker

# Настройки для тестовой базы данных
TEST_POSTGRES_USER = os.getenv("TEST_POSTGRES_USER", "aisha_user")
TEST_POSTGRES_PASSWORD = os.getenv("TEST_POSTGRES_PASSWORD", "test_password")
TEST_POSTGRES_HOST = os.getenv("TEST_POSTGRES_HOST", "localhost")
TEST_POSTGRES_PORT = os.getenv("TEST_POSTGRES_PORT", "5432")
TEST_POSTGRES_DB = os.getenv("TEST_POSTGRES_DB", "aisha_test")

# URL для тестовой базы данных
TEST_DATABASE_URL = f"postgresql+asyncpg://{TEST_POSTGRES_USER}:{TEST_POSTGRES_PASSWORD}@{TEST_POSTGRES_HOST}:{TEST_POSTGRES_PORT}/{TEST_POSTGRES_DB}"

# Создаем движок для тестовой базы данных
test_engine = create_async_engine(
    test_settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

# Создаем фабрику сессий для тестовой базы данных
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Автоматически загружать переменные окружения из .env.test для всех тестов
load_dotenv(".env.test")

# Создаем тестовую конфигурацию
test_settings = TestConfig()

@pytest.fixture(scope="session")
def event_loop():
    """Создаем event loop для тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Создаем тестовую базу данных."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def minio_client():
    """Создает клиент MinIO для тестов."""
    client = Minio(
        test_settings.MINIO_ENDPOINT,
        access_key=test_settings.MINIO_ACCESS_KEY,
        secret_key=test_settings.MINIO_SECRET_KEY,
        secure=test_settings.MINIO_SECURE
    )
    
    # Используем существующий тестовый бакет
    test_bucket = test_settings.MINIO_BUCKET
    try:
        client.make_bucket(test_bucket)
    except Exception:
        pass
    
    yield client
    
    # Очистка после тестов
    try:
        objects = client.list_objects(test_bucket, recursive=True)
        for obj in objects:
            client.remove_object(test_bucket, obj.object_name)
    except Exception:
        pass

@pytest.fixture
def test_uuid():
    """Генерирует тестовый UUID."""
    return uuid.uuid4()

@pytest.fixture
def test_user_data(test_uuid):
    """Создает тестовые данные пользователя."""
    return {
        "id": test_uuid,
        "telegram_id": 123456789,
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

@pytest.fixture
def test_avatar_data(test_uuid):
    """Создает тестовые данные аватара."""
    return {
        "id": uuid.uuid4(),
        "user_id": test_uuid,
        "photo_key": "test/photo.jpg",
        "preview_key": "test/preview.jpg",
        "avatar_data": {
            "size": 1024,
            "format": "jpg"
        },
        "created_at": datetime.utcnow()
    }

@pytest.fixture
def test_transcript_data(test_uuid):
    """Создает тестовые данные транскрипта."""
    return {
        "id": uuid.uuid4(),
        "user_id": test_uuid,
        "audio_key": "test/audio.mp3",
        "transcript_key": "test/transcript.txt",
        "transcript_data": {
            "duration": 60,
            "format": "mp3"
        },
        "created_at": datetime.utcnow()
    }

@pytest.fixture
def test_history_data(test_uuid):
    """Создает тестовые данные истории."""
    return {
        "id": uuid.uuid4(),
        "user_id": test_uuid,
        "content_key": "test/content.txt",
        "created_at": datetime.utcnow()
    }

@pytest.fixture
def test_state_data(test_uuid):
    """Создает тестовые данные состояния."""
    return {
        "id": uuid.uuid4(),
        "user_id": test_uuid,
        "state_data": {
            "state": "test",
            "data": {"key": "value"}
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

@pytest.fixture
def test_balance_data(test_uuid):
    """Создает тестовые данные баланса."""
    return {
        "id": uuid.uuid4(),
        "user_id": test_uuid,
        "coins": 100.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

@pytest.fixture
def test_transaction_data(test_uuid):
    """Создает тестовые данные транзакции."""
    return {
        "id": uuid.uuid4(),
        "user_id": test_uuid,
        "amount": 100.0,
        "type": "credit",
        "description": "Test transaction",
        "created_at": datetime.utcnow()
    } 