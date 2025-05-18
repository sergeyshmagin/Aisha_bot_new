"""
Тесты для сервиса баланса.
"""

import pytest
from datetime import datetime
from uuid import UUID

from frontend_bot.services.balance_service import BalanceService
from database.models import UserBalance, Transaction

@pytest.fixture
def balance_service(session):
    """Создает экземпляр сервиса баланса."""
    return BalanceService(session)

@pytest.fixture
def test_balance_data():
    """Создает тестовые данные баланса."""
    return {
        "coins": 100,
        "balance_data": {
            "key1": "value1",
            "key2": "value2"
        }
    }

@pytest.fixture
def test_transaction_data():
    """Создает тестовые данные транзакции."""
    return {
        "amount": 50,
        "type": "deposit",
        "transaction_data": {
            "key1": "value1",
            "key2": "value2"
        }
    }

@pytest.mark.asyncio
async def test_create_balance(balance_service, test_user_data, test_balance_data):
    """Тест создания баланса."""
    # Создаем пользователя
    user = await balance_service.create_user(**test_user_data)
    assert user.id == test_user_data["id"]
    
    # Создаем баланс
    balance = await balance_service.create_balance(
        user_id=user.id,
        **test_balance_data
    )
    
    assert isinstance(balance.id, UUID)
    assert balance.user_id == user.id
    assert balance.coins == test_balance_data["coins"]
    assert balance.balance_data == test_balance_data["balance_data"]
    assert isinstance(balance.created_at, datetime)
    assert isinstance(balance.updated_at, datetime)

@pytest.mark.asyncio
async def test_get_balance(balance_service, test_user_data, test_balance_data):
    """Тест получения баланса."""
    # Создаем пользователя
    user = await balance_service.create_user(**test_user_data)
    
    # Создаем баланс
    balance = await balance_service.create_balance(
        user_id=user.id,
        **test_balance_data
    )
    
    # Получаем баланс
    retrieved_balance = await balance_service.get_balance(balance.id)
    assert retrieved_balance.id == balance.id
    assert retrieved_balance.user_id == user.id
    assert retrieved_balance.coins == test_balance_data["coins"]
    assert retrieved_balance.balance_data == test_balance_data["balance_data"]

@pytest.mark.asyncio
async def test_update_balance(balance_service, test_user_data, test_balance_data):
    """Тест обновления баланса."""
    # Создаем пользователя
    user = await balance_service.create_user(**test_user_data)
    
    # Создаем баланс
    balance = await balance_service.create_balance(
        user_id=user.id,
        **test_balance_data
    )
    
    # Обновляем баланс
    updated_data = {
        "coins": 200,
        "balance_data": {
            "key3": "value3",
            "key4": "value4"
        }
    }
    
    updated_balance = await balance_service.update_balance(
        balance.id,
        **updated_data
    )
    
    assert updated_balance.id == balance.id
    assert updated_balance.user_id == user.id
    assert updated_balance.coins == updated_data["coins"]
    assert updated_balance.balance_data == updated_data["balance_data"]
    assert updated_balance.updated_at > balance.updated_at

@pytest.mark.asyncio
async def test_delete_balance(balance_service, test_user_data, test_balance_data):
    """Тест удаления баланса."""
    # Создаем пользователя
    user = await balance_service.create_user(**test_user_data)
    
    # Создаем баланс
    balance = await balance_service.create_balance(
        user_id=user.id,
        **test_balance_data
    )
    
    # Удаляем баланс
    await balance_service.delete_balance(balance.id)
    
    # Проверяем, что баланс удален
    retrieved_balance = await balance_service.get_balance(balance.id)
    assert retrieved_balance is None

@pytest.mark.asyncio
async def test_get_user_balance(balance_service, test_user_data, test_balance_data):
    """Тест получения баланса пользователя."""
    # Создаем пользователя
    user = await balance_service.create_user(**test_user_data)
    
    # Создаем баланс
    balance = await balance_service.create_balance(
        user_id=user.id,
        **test_balance_data
    )
    
    # Получаем баланс пользователя
    user_balance = await balance_service.get_user_balance(user.id)
    assert user_balance.id == balance.id
    assert user_balance.user_id == user.id
    assert user_balance.coins == test_balance_data["coins"]
    assert user_balance.balance_data == test_balance_data["balance_data"]

@pytest.mark.asyncio
async def test_create_transaction(balance_service, test_user_data, test_balance_data, test_transaction_data):
    """Тест создания транзакции."""
    # Создаем пользователя
    user = await balance_service.create_user(**test_user_data)
    
    # Создаем баланс
    balance = await balance_service.create_balance(
        user_id=user.id,
        **test_balance_data
    )
    
    # Создаем транзакцию
    transaction = await balance_service.create_transaction(
        user_id=user.id,
        **test_transaction_data
    )
    
    assert isinstance(transaction.id, UUID)
    assert transaction.user_id == user.id
    assert transaction.amount == test_transaction_data["amount"]
    assert transaction.type == test_transaction_data["type"]
    assert transaction.transaction_data == test_transaction_data["transaction_data"]
    assert isinstance(transaction.created_at, datetime)

@pytest.mark.asyncio
async def test_get_transaction(balance_service, test_user_data, test_transaction_data):
    """Тест получения транзакции."""
    # Создаем пользователя
    user = await balance_service.create_user(**test_user_data)
    
    # Создаем транзакцию
    transaction = await balance_service.create_transaction(
        user_id=user.id,
        **test_transaction_data
    )
    
    # Получаем транзакцию
    retrieved_transaction = await balance_service.get_transaction(transaction.id)
    assert retrieved_transaction.id == transaction.id
    assert retrieved_transaction.user_id == user.id
    assert retrieved_transaction.amount == test_transaction_data["amount"]
    assert retrieved_transaction.type == test_transaction_data["type"]
    assert retrieved_transaction.transaction_data == test_transaction_data["transaction_data"]

@pytest.mark.asyncio
async def test_get_user_transactions(balance_service, test_user_data, test_transaction_data):
    """Тест получения транзакций пользователя."""
    # Создаем пользователя
    user = await balance_service.create_user(**test_user_data)
    
    # Создаем транзакции
    transaction1 = await balance_service.create_transaction(
        user_id=user.id,
        **test_transaction_data
    )
    transaction2 = await balance_service.create_transaction(
        user_id=user.id,
        **{**test_transaction_data, "amount": 75, "type": "withdraw"}
    )
    
    # Получаем транзакции пользователя
    user_transactions = await balance_service.get_user_transactions(user.id)
    assert len(user_transactions) == 2
    assert all(isinstance(t.id, UUID) for t in user_transactions)
    assert all(t.user_id == user.id for t in user_transactions)
    assert {t.type for t in user_transactions} == {"deposit", "withdraw"}
    assert {t.amount for t in user_transactions} == {50, 75}

@pytest.mark.asyncio
async def test_get_transactions_by_type(balance_service, test_user_data, test_transaction_data):
    """Тест получения транзакций по типу."""
    # Создаем пользователя
    user = await balance_service.create_user(**test_user_data)
    
    # Создаем транзакции разных типов
    await balance_service.create_transaction(
        user_id=user.id,
        **test_transaction_data
    )
    await balance_service.create_transaction(
        user_id=user.id,
        **{**test_transaction_data, "amount": 75, "type": "withdraw"}
    )
    
    # Получаем транзакции по типу
    deposit_transactions = await balance_service.get_transactions_by_type("deposit")
    assert len(deposit_transactions) == 1
    assert deposit_transactions[0].type == "deposit"
    
    withdraw_transactions = await balance_service.get_transactions_by_type("withdraw")
    assert len(withdraw_transactions) == 1
    assert withdraw_transactions[0].type == "withdraw"

@pytest.mark.asyncio
async def test_get_transactions_by_data(balance_service, test_user_data, test_transaction_data):
    """Тест получения транзакций по данным."""
    # Создаем пользователя
    user = await balance_service.create_user(**test_user_data)
    
    # Создаем транзакции с разными данными
    await balance_service.create_transaction(
        user_id=user.id,
        **test_transaction_data
    )
    await balance_service.create_transaction(
        user_id=user.id,
        **{**test_transaction_data, "amount": 75, "transaction_data": {"key3": "value3"}}
    )
    
    # Получаем транзакции по данным
    transactions_with_key1 = await balance_service.get_transactions_by_data("key1", "value1")
    assert len(transactions_with_key1) == 1
    assert transactions_with_key1[0].transaction_data["key1"] == "value1"
    
    transactions_with_key3 = await balance_service.get_transactions_by_data("key3", "value3")
    assert len(transactions_with_key3) == 1
    assert transactions_with_key3[0].transaction_data["key3"] == "value3" 