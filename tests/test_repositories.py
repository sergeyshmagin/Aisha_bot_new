"""
Тесты для репозиториев.
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from frontend_bot.repositories.user_repository import UserRepository
from frontend_bot.repositories.state_repository import StateRepository
from frontend_bot.repositories.balance_repository import BalanceRepository
from frontend_bot.repositories.avatar_repository import UserAvatarRepository
from frontend_bot.repositories.transcript_repository import UserTranscriptRepository
from frontend_bot.repositories.transaction_repository import TransactionRepository
from frontend_bot.repositories.history_repository import UserHistoryRepository


@pytest.fixture
async def async_engine():
    """Создает тестовый движок SQLAlchemy."""
    engine = create_async_engine(
        "postgresql+asyncpg://aisha_user:test_password@localhost:5432/aisha_test",
        echo=True
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Создает тестовую сессию SQLAlchemy."""
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def user_repository(async_session):
    """Создает репозиторий пользователей."""
    return UserRepository(async_session)


@pytest.fixture
def user_state_repository(async_session):
    """Создает репозиторий состояний пользователей."""
    return StateRepository(async_session)


@pytest.fixture
def user_balance_repository(async_session):
    """Создает репозиторий балансов пользователей."""
    return BalanceRepository(async_session)


@pytest.fixture
def user_avatar_repository(async_session):
    """Создает репозиторий аватаров пользователей."""
    return UserAvatarRepository(async_session)


@pytest.fixture
def user_transcript_repository(async_session):
    """Создает репозиторий транскриптов пользователей."""
    return UserTranscriptRepository(async_session)


@pytest.fixture
def transaction_repository(async_session):
    """Создает репозиторий транзакций."""
    return TransactionRepository(async_session)


@pytest.fixture
def user_history_repository(async_session):
    """Создает репозиторий истории пользователей."""
    return UserHistoryRepository(async_session)


@pytest.mark.asyncio
async def test_user_repository(user_repository):
    """Тестирует репозиторий пользователей."""
    # Создание пользователя
    user = await user_repository.create(
        telegram_id=123456789,
        first_name="Test",
        last_name="User",
        username="testuser",
        language_code="ru"
    )
    assert user.telegram_id == 123456789
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.username == "testuser"
    assert user.language_code == "ru"

    # Получение пользователя
    user = await user_repository.get_by_telegram_id(123456789)
    assert user is not None
    assert user.telegram_id == 123456789

    # Обновление пользователя
    user = await user_repository.update(123456789, first_name="Updated")
    assert user.first_name == "Updated"


@pytest.mark.asyncio
async def test_user_state_repository(user_state_repository, user_repository):
    """Тестирует репозиторий состояний пользователей."""
    # Создание пользователя
    user = await user_repository.create(
        telegram_id=123456789,
        first_name="Test"
    )

    # Обновление состояния
    state = await user_state_repository.update_state(
        user.user_id,
        {"state": "test", "data": {"key": "value"}}
    )
    assert state.user_id == user.user_id
    assert state.state_data["state"] == "test"
    assert state.state_data["data"]["key"] == "value"

    # Получение состояния
    state = await user_state_repository.get_by_user_id(user.user_id)
    assert state is not None
    assert state.state_data["state"] == "test"


@pytest.mark.asyncio
async def test_user_balance_repository(user_balance_repository, user_repository):
    """Тестирует репозиторий балансов пользователей."""
    # Создание пользователя
    user = await user_repository.create(
        telegram_id=123456789,
        first_name="Test"
    )

    # Обновление баланса
    balance = await user_balance_repository.update_balance(user.user_id, 100.0)
    assert balance.user_id == user.user_id
    assert balance.coins == 100.0

    # Получение баланса
    balance = await user_balance_repository.get_by_user_id(user.user_id)
    assert balance is not None
    assert balance.coins == 100.0


@pytest.mark.asyncio
async def test_user_avatar_repository(user_avatar_repository, user_repository):
    """Тестирует репозиторий аватаров пользователей."""
    # Создание пользователя
    user = await user_repository.create(
        telegram_id=123456789,
        first_name="Test"
    )

    # Создание аватара
    avatar_data = {
        "original_path": "/path/to/original.jpg",
        "processed_path": "/path/to/processed.jpg",
        "metadata": {"size": 1024, "format": "jpg"}
    }
    avatar = await user_avatar_repository.create(user.user_id, avatar_data)
    assert avatar.user_id == user.user_id
    assert avatar.avatar_data == avatar_data

    # Получение аватара по ID
    avatar = await user_avatar_repository.get_by_id(avatar.id)
    assert avatar is not None
    assert avatar.avatar_data == avatar_data

    # Получение всех аватаров пользователя
    avatars = await user_avatar_repository.get_by_user_id(user.user_id)
    assert len(avatars) == 1
    assert avatars[0].avatar_data == avatar_data


@pytest.mark.asyncio
async def test_user_transcript_repository(user_transcript_repository, user_repository):
    """Тестирует репозиторий транскриптов пользователей."""
    # Создание пользователя
    user = await user_repository.create(
        telegram_id=123456789,
        first_name="Test"
    )

    # Создание транскрипта
    transcript_data = {
        "original_path": "/path/to/audio.mp3",
        "transcript_path": "/path/to/transcript.txt",
        "metadata": {"duration": 60, "format": "mp3"}
    }
    transcript = await user_transcript_repository.create(user.user_id, transcript_data)
    assert transcript.user_id == user.user_id
    assert transcript.transcript_data == transcript_data

    # Получение транскрипта по ID
    transcript = await user_transcript_repository.get_by_id(transcript.id)
    assert transcript is not None
    assert transcript.transcript_data == transcript_data

    # Получение всех транскриптов пользователя
    transcripts = await user_transcript_repository.get_by_user_id(user.user_id)
    assert len(transcripts) == 1
    assert transcripts[0].transcript_data == transcript_data


@pytest.mark.asyncio
async def test_transaction_repository(transaction_repository, user_repository):
    """Тестирует репозиторий транзакций."""
    # Создание пользователя
    user = await user_repository.create(
        telegram_id=123456789,
        first_name="Test"
    )

    # Создание транзакции
    transaction = await transaction_repository.create(
        user.user_id,
        100.0,
        "credit",
        "Test transaction"
    )
    assert transaction.user_id == user.user_id
    assert transaction.amount == 100.0
    assert transaction.type == "credit"
    assert transaction.description == "Test transaction"

    # Получение всех транзакций пользователя
    transactions = await transaction_repository.get_by_user_id(user.user_id)
    assert len(transactions) == 1
    assert transactions[0].amount == 100.0


@pytest.mark.asyncio
async def test_user_history_repository(user_history_repository, user_repository):
    """Тестирует репозиторий истории пользователей."""
    # Создание пользователя
    user = await user_repository.create(
        telegram_id=123456789,
        first_name="Test"
    )

    # Создание записи в истории
    action_data = {
        "action": "test_action",
        "details": {"key": "value"}
    }
    history = await user_history_repository.create(
        user.user_id,
        "test_action",
        action_data
    )
    assert history.user_id == user.user_id
    assert history.action_type == "test_action"
    assert history.action_data == action_data

    # Получение всей истории пользователя
    history_entries = await user_history_repository.get_by_user_id(user.user_id)
    assert len(history_entries) == 1
    assert history_entries[0].action_type == "test_action" 