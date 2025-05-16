"""
Тесты для моделей PostgreSQL.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy import text
from frontend_bot.models.base import User, UserBalance, UserAvatar, UserState, Transaction
from tests.conftest import generate_telegram_id

@pytest.mark.asyncio
async def test_user_creation(test_session):
    """Тест создания пользователя."""
    telegram_id = generate_telegram_id()
    user = User(
        telegram_id=telegram_id,
        username="test_user"
    )
    test_session.add(user)
    await test_session.flush()
    
    assert user.telegram_id == telegram_id
    assert user.username == "test_user"
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)

@pytest.mark.asyncio
async def test_user_balance_creation(test_session):
    """Тест создания баланса пользователя."""
    # Создаем пользователя
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user"
    )
    test_session.add(user)
    await test_session.flush()
    
    # Создаем баланс
    balance = UserBalance(
        user_id=user.id,
        coins=Decimal("100.00")
    )
    test_session.add(balance)
    await test_session.flush()
    
    assert balance.user_id == user.id
    assert balance.coins == Decimal("100.00")
    assert isinstance(balance.created_at, datetime)
    assert isinstance(balance.updated_at, datetime)

@pytest.mark.asyncio
async def test_user_avatar_creation(test_session):
    """Тест создания аватара пользователя."""
    # Создаем пользователя
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user"
    )
    test_session.add(user)
    await test_session.flush()
    
    # Создаем аватар
    avatar = UserAvatar(
        user_id=user.id,
        avatar_data={
            "name": "Test Avatar",
            "gender": "male",
            "image_path": "/path/to/avatar.jpg",
            "gen_params": {"style": "realistic"},
            "status": "ready"
        }
    )
    test_session.add(avatar)
    await test_session.flush()
    
    assert avatar.user_id == user.id
    assert avatar.avatar_data["name"] == "Test Avatar"
    assert avatar.avatar_data["gender"] == "male"
    assert isinstance(avatar.created_at, datetime)
    assert isinstance(avatar.updated_at, datetime)

@pytest.mark.asyncio
async def test_user_state_creation(test_session):
    """Тест создания состояния пользователя."""
    # Создаем пользователя
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user"
    )
    test_session.add(user)
    await test_session.flush()
    
    # Создаем состояние
    state = UserState(
        user_id=user.id,
        state_data={
            "current_state": "main_menu",
            "last_action": "start",
            "context": {"message_id": 123}
        }
    )
    test_session.add(state)
    await test_session.flush()
    
    assert state.user_id == user.id
    assert state.state_data["current_state"] == "main_menu"
    assert isinstance(state.created_at, datetime)
    assert isinstance(state.updated_at, datetime)

@pytest.mark.asyncio
async def test_transaction_creation(test_session):
    """Тест создания транзакции."""
    # Создаем пользователя
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user"
    )
    test_session.add(user)
    await test_session.flush()
    
    # Создаем транзакцию
    transaction = Transaction(
        user_id=user.id,
        amount=Decimal("50.00"),
        type="deposit",
        description="Test deposit"
    )
    test_session.add(transaction)
    await test_session.flush()
    
    assert transaction.user_id == user.id
    assert transaction.amount == Decimal("50.00")
    assert transaction.type == "deposit"
    assert transaction.description == "Test deposit"
    assert isinstance(transaction.created_at, datetime) 