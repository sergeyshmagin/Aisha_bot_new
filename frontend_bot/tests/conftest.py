"""
Общие фикстуры и конфигурация для тестов.
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from minio import Minio
from frontend_bot.models.base import Base

# Тестовые настройки
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db"
)
TEST_MINIO_ENDPOINT = os.getenv("TEST_MINIO_ENDPOINT", "localhost:9000")
TEST_MINIO_ACCESS_KEY = os.getenv("TEST_MINIO_ACCESS_KEY", "minioadmin")
TEST_MINIO_SECRET_KEY = os.getenv("TEST_MINIO_SECRET_KEY", "minioadmin")
TEST_MINIO_BUCKET = os.getenv("TEST_MINIO_BUCKET", "test-bucket")

def pytest_configure(config):
    """Добавляем маркеры для тестов."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires Redis server)"
    )

@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Создает тестовый движок базы данных."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine):
    """Создает тестовую сессию базы данных."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="session")
def minio_client():
    """Создает клиент MinIO для тестов."""
    client = Minio(
        TEST_MINIO_ENDPOINT,
        access_key=TEST_MINIO_ACCESS_KEY,
        secret_key=TEST_MINIO_SECRET_KEY,
        secure=False
    )
    
    # Создаем тестовый бакет если его нет
    try:
        if not client.bucket_exists(TEST_MINIO_BUCKET):
            client.make_bucket(TEST_MINIO_BUCKET)
    except Exception as e:
        pytest.skip(f"MinIO server not available: {e}")
    
    yield client
    
    # Очистка после тестов
    try:
        objects = client.list_objects(TEST_MINIO_BUCKET, recursive=True)
        for obj in objects:
            client.remove_object(TEST_MINIO_BUCKET, obj.object_name)
    except Exception as e:
        pytest.skip(f"Failed to cleanup MinIO: {e}")

@pytest.fixture
async def session():
    """Создает тестовую сессию для работы с хранилищем."""
    # storage = await init_storage()
    yield storage
    await storage.close()

@pytest.fixture
def mock_bot():
    """Фикстура для мока бота."""
    with patch("frontend_bot.handlers.handlers.bot") as mock:
        mock.send_message = AsyncMock()
        mock.get_file = AsyncMock()
        mock.download_file = AsyncMock()
        yield mock

@pytest.fixture
def mock_avatar_workflow():
    """Фикстура для мока avatar_workflow."""
    with patch("frontend_bot.handlers.handlers.handle_photo_upload") as mock_upload, \
         patch("frontend_bot.handlers.handlers.handle_gender_selection") as mock_gender, \
         patch("frontend_bot.handlers.handlers.handle_name_input") as mock_name, \
         patch("frontend_bot.handlers.handlers.finalize_avatar") as mock_finalize, \
         patch("frontend_bot.handlers.handlers.cleanup_state") as mock_cleanup:
        
        mock_upload.return_value = AsyncMock()
        mock_gender.return_value = AsyncMock()
        mock_name.return_value = AsyncMock()
        mock_finalize.return_value = AsyncMock()
        mock_cleanup.return_value = AsyncMock()
        
        yield {
            "upload": mock_upload,
            "gender": mock_gender,
            "name": mock_name,
            "finalize": mock_finalize,
            "cleanup": mock_cleanup,
        } 