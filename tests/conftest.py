"""Общие фикстуры для тестов."""

import pytest
import pytest_asyncio
import asyncio
import random
from unittest.mock import patch, AsyncMock
from frontend_bot.services.state_utils import clear_state
from tests.conftest_redis import mock_redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

"""
Фикстуры для тестирования PostgreSQL.
"""

from frontend_bot.models.base import Base
from frontend_bot.database.db import get_session
from frontend_bot.repositories.user_repository import UserRepository
from frontend_bot.repositories.balance_repository import BalanceRepository
from frontend_bot.repositories.state_repository import StateRepository

# Тестовая БД
TEST_DATABASE_URL = "postgresql+asyncpg://aisha_user:KbZZGJHX09KSH7r9ev4m@192.168.0.4:5432/aisha_test"

def generate_telegram_id():
    """Генерирует уникальный telegram_id для тестов."""
    return random.randint(100000000, 999999999)

@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Создает тестовый движок SQLAlchemy."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture(autouse=True)
async def clean_tables(test_engine):
    """Очищает все таблицы перед каждым тестом."""
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncSession:
    """Создает тестовую сессию."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def user_repository(test_session) -> UserRepository:
    """Создает репозиторий пользователей."""
    return UserRepository(test_session)

@pytest_asyncio.fixture
async def balance_repository(test_session) -> BalanceRepository:
    """Создает репозиторий балансов."""
    return BalanceRepository(test_session)

@pytest_asyncio.fixture
async def state_repository(test_session) -> StateRepository:
    """Создает репозиторий состояний."""
    return StateRepository(test_session)

@pytest_asyncio.fixture
async def test_user(user_repository):
    """Создает тестового пользователя."""
    user = await user_repository.create(
        telegram_id=generate_telegram_id(),
        username="test_user"
    )
    return user

@pytest.fixture
async def clean_state(mock_redis):
    """
    Фикстура для очистки состояния до и после теста.
    
    Использование:
    ```python
    async def test_something(clean_state):
        # Состояние очищено
        ...
        # После теста состояние будет очищено автоматически
    ```
    """
    await clear_state()
    yield
    await clear_state()


@pytest.fixture
def mock_bot():
    """
    Фикстура для мока бота.
    
    Использование:
    ```python
    async def test_something(mock_bot):
        # Используем мок
        mock_bot.send_message.assert_called_once()
        args = mock_bot.send_message.call_args[0]
        assert args[0] == user_id
    ```
    """
    with patch('frontend_bot.bot.bot', new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def create_message():
    """
    Фикстура для создания тестового сообщения.
    
    Использование:
    ```python
    async def test_something(create_message):
        message = create_message(user_id=123, text="Hello")
        assert message.from_user.id == 123
        assert message.text == "Hello"
    ```
    """
    def _create_message(user_id: int, text: str):
        message = AsyncMock()
        message.from_user.id = user_id
        message.chat.id = user_id
        message.text = text
        return message
    return _create_message


@pytest.fixture
def create_callback_query():
    """
    Фикстура для создания тестового callback query.
    
    Использование:
    ```python
    async def test_something(create_callback_query):
        query = create_callback_query(
            user_id=123,
            data="test_data",
            message_id=456
        )
        assert query.from_user.id == 123
        assert query.data == "test_data"
    ```
    """
    def _create_callback_query(
        user_id: int,
        data: str,
        message_id: int = 1
    ):
        query = AsyncMock()
        query.from_user.id = user_id
        query.message.chat.id = user_id
        query.message.message_id = message_id
        query.data = data
        query.id = f"query_{user_id}_{message_id}"
        return query
    return _create_callback_query


@pytest.fixture
def create_photo_message():
    """
    Фикстура для создания тестового сообщения с фото.
    
    Использование:
    ```python
    async def test_something(create_photo_message):
        message = create_photo_message(
            user_id=123,
            file_id="test_file_id"
        )
        assert message.photo[-1].file_id == "test_file_id"
    ```
    """
    def _create_photo_message(user_id: int, file_id: str):
        message = AsyncMock()
        message.from_user.id = user_id
        message.chat.id = user_id
        
        photo_size = AsyncMock()
        photo_size.file_id = file_id
        photo_size.file_unique_id = f"unique_{file_id}"
        photo_size.width = 100
        photo_size.height = 100
        photo_size.file_size = 1024
        
        message.photo = [photo_size]
        return message
    return _create_photo_message


@pytest.fixture
def create_document_message():
    """
    Фикстура для создания тестового сообщения с документом.
    
    Использование:
    ```python
    async def test_something(create_document_message):
        message = create_document_message(
            user_id=123,
            file_id="test_file_id",
            file_name="test.pdf"
        )
        assert message.document.file_id == "test_file_id"
        assert message.document.file_name == "test.pdf"
    ```
    """
    def _create_document_message(
        user_id: int,
        file_id: str,
        file_name: str
    ):
        message = AsyncMock()
        message.from_user.id = user_id
        message.chat.id = user_id
        
        document = AsyncMock()
        document.file_id = file_id
        document.file_unique_id = f"unique_{file_id}"
        document.file_name = file_name
        document.mime_type = "application/pdf"
        document.file_size = 1024
        
        message.document = document
        return message
    return _create_document_message


@pytest.fixture
def create_voice_message():
    """
    Фикстура для создания тестового голосового сообщения.
    
    Использование:
    ```python
    async def test_something(create_voice_message):
        message = create_voice_message(
            user_id=123,
            file_id="test_file_id",
            duration=60
        )
        assert message.voice.file_id == "test_file_id"
        assert message.voice.duration == 60
    ```
    """
    def _create_voice_message(
        user_id: int,
        file_id: str,
        duration: int = 60
    ):
        message = AsyncMock()
        message.from_user.id = user_id
        message.chat.id = user_id
        
        voice = AsyncMock()
        voice.file_id = file_id
        voice.file_unique_id = f"unique_{file_id}"
        voice.duration = duration
        voice.mime_type = "audio/ogg"
        voice.file_size = 1024
        
        message.voice = voice
        return message
    return _create_voice_message


@pytest.fixture
def create_video_message():
    """
    Фикстура для создания тестового видео сообщения.
    
    Использование:
    ```python
    async def test_something(create_video_message):
        message = create_video_message(
            user_id=123,
            file_id="test_file_id",
            duration=60
        )
        assert message.video.file_id == "test_file_id"
        assert message.video.duration == 60
    ```
    """
    def _create_video_message(
        user_id: int,
        file_id: str,
        duration: int = 60
    ):
        message = AsyncMock()
        message.from_user.id = user_id
        message.chat.id = user_id
        
        video = AsyncMock()
        video.file_id = file_id
        video.file_unique_id = f"unique_{file_id}"
        video.duration = duration
        video.width = 1280
        video.height = 720
        video.mime_type = "video/mp4"
        video.file_size = 1024 * 1024
        
        message.video = video
        return message
    return _create_video_message 