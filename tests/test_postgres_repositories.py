"""
Тесты для репозиториев PostgreSQL.
"""

import pytest
from decimal import Decimal
from frontend_bot.config import INITIAL_BALANCE

@pytest.mark.asyncio
async def test_user_repository_create(user_repository):
    """Тест создания пользователя через репозиторий."""
    user = await user_repository.create(
        telegram_id=987654321,
        username="new_user"
    )
    
    assert user.telegram_id == 987654321
    assert user.username == "new_user"
    assert user.balance is not None
    assert user.balance.coins == Decimal(str(INITIAL_BALANCE))

@pytest.mark.asyncio
async def test_user_repository_get_by_telegram_id(user_repository, test_user):
    """Тест получения пользователя по telegram_id."""
    user = await user_repository.get_by_telegram_id(test_user.telegram_id)
    
    assert user is not None
    assert user.telegram_id == test_user.telegram_id
    assert user.username == test_user.username

@pytest.mark.asyncio
async def test_user_repository_get_or_create(user_repository):
    """Тест get_or_create пользователя."""
    # Создаем нового
    user1 = await user_repository.get_or_create(
        telegram_id=111222333,
        username="test_user_1"
    )
    assert user1.telegram_id == 111222333
    
    # Получаем существующего
    user2 = await user_repository.get_or_create(
        telegram_id=111222333,
        username="test_user_1"
    )
    assert user2.id == user1.id

@pytest.mark.asyncio
async def test_balance_repository_operations(balance_repository, test_user):
    """Тест операций с балансом."""
    # Проверяем начальный баланс
    initial_balance = await balance_repository.get_balance(test_user.id)
    assert initial_balance.coins == Decimal(str(INITIAL_BALANCE))
    
    # Добавляем монеты
    await balance_repository.add_coins(
        user_id=test_user.id,
        amount=Decimal("100.00"),
        description="Test deposit"
    )
    
    # Проверяем баланс
    balance = await balance_repository.get_balance(test_user.id)
    assert balance.coins == Decimal(str(INITIAL_BALANCE)) + Decimal("100.00")
    
    # Списываем монеты
    success = await balance_repository.subtract_coins(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        description="Test withdraw"
    )
    assert success is True
    
    # Проверяем новый баланс
    balance = await balance_repository.get_balance(test_user.id)
    assert balance.coins == Decimal(str(INITIAL_BALANCE)) + Decimal("50.00")
    
    # Пробуем списать больше чем есть
    success = await balance_repository.subtract_coins(
        user_id=test_user.id,
        amount=Decimal("1000.00"),
        description="Test withdraw too much"
    )
    assert success is False
    
    # Проверяем что баланс не изменился
    balance = await balance_repository.get_balance(test_user.id)
    assert balance.coins == Decimal(str(INITIAL_BALANCE)) + Decimal("50.00")

@pytest.mark.asyncio
async def test_balance_repository_transactions(balance_repository, test_user):
    """Тест истории транзакций."""
    # Добавляем несколько транзакций
    await balance_repository.add_coins(
        user_id=test_user.id,
        amount=Decimal("100.00"),
        description="First deposit"
    )
    await balance_repository.subtract_coins(
        user_id=test_user.id,
        amount=Decimal("30.00"),
        description="First withdraw"
    )
    await balance_repository.add_coins(
        user_id=test_user.id,
        amount=Decimal("50.00"),
        description="Second deposit"
    )
    
    # Получаем историю
    transactions = await balance_repository.get_transactions(test_user.id, limit=10)
    
    assert len(transactions) == 3
    assert transactions[0].amount == Decimal("50.00")  # Последняя транзакция
    assert transactions[1].amount == Decimal("-30.00")
    assert transactions[2].amount == Decimal("100.00")

@pytest.mark.asyncio
async def test_state_repository_operations(state_repository, test_user):
    """Тест операций с состоянием."""
    # Устанавливаем начальное состояние
    state_data = {"step": "start", "data": {"name": "test"}}
    state = await state_repository.set_state(test_user.id, state_data)
    
    assert state.user_id == test_user.id
    assert state.state_data == state_data
    
    # Обновляем состояние
    new_data = {"step": "next", "data": {"age": 25}}
    updated_state = await state_repository.update_state(test_user.id, new_data)
    
    assert updated_state is not None
    assert updated_state.state_data["step"] == "next"
    assert updated_state.state_data["data"]["age"] == 25
    assert "name" in updated_state.state_data["data"]  # Старые данные сохранились
    
    # Очищаем состояние
    await state_repository.clear_state(test_user.id)
    state = await state_repository.get_state(test_user.id)
    assert state is None 