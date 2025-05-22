"""
Тесты для индексов PostgreSQL.
"""

import pytest
from sqlalchemy import text
from frontend_bot.models.base import User, UserBalance, UserAvatar, UserState, Transaction
# TODO: Добавить фикстуру или функцию генерации telegram_id для тестов

@pytest.mark.asyncio
async def test_user_indexes(test_session):
    """Тест наличия индексов в таблице users."""
    # Создаем пользователя для проверки индексов
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user_indexes"
    )
    test_session.add(user)
    await test_session.commit()
    
    # Получаем список индексов
    result = await test_session.execute(
        text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'users'
        """)
    )
    indexes = {row[0]: row[1] for row in result}
    
    # Проверяем наличие необходимых индексов
    assert "ix_users_telegram_id" in indexes
    assert "ix_users_username" in indexes
    assert "ix_users_created_at" in indexes

@pytest.mark.asyncio
async def test_user_balance_indexes(test_session):
    """Тест наличия индексов в таблице user_balances."""
    # Создаем пользователя и баланс
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user_balance"
    )
    test_session.add(user)
    await test_session.flush()
    
    balance = UserBalance(
        user_id=user.id,
        coins=100.00
    )
    test_session.add(balance)
    await test_session.commit()
    
    # Получаем список индексов
    result = await test_session.execute(
        text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'user_balances'
        """)
    )
    indexes = {row[0]: row[1] for row in result}
    
    # Проверяем наличие необходимых индексов
    assert "ix_user_balances_user_id" in indexes
    assert "ix_user_balances_updated_at" in indexes

@pytest.mark.asyncio
async def test_user_avatar_indexes(test_session):
    """Тест наличия индексов в таблице user_avatars."""
    # Создаем пользователя и аватар
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user_avatar"
    )
    test_session.add(user)
    await test_session.flush()
    
    avatar = UserAvatar(
        user_id=user.id,
        avatar_data={
            "name": "Test Avatar",
            "status": "ready"
        }
    )
    test_session.add(avatar)
    await test_session.commit()
    
    # Получаем список индексов
    result = await test_session.execute(
        text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'user_avatars'
        """)
    )
    indexes = {row[0]: row[1] for row in result}
    
    # Проверяем наличие необходимых индексов
    assert "ix_user_avatars_user_id" in indexes
    assert "ix_user_avatars_created_at" in indexes

@pytest.mark.asyncio
async def test_user_state_indexes(test_session):
    """Тест наличия индексов в таблице user_states."""
    # Создаем пользователя и состояние
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user_state"
    )
    test_session.add(user)
    await test_session.flush()
    
    state = UserState(
        user_id=user.id,
        state_data={"current_state": "main_menu"}
    )
    test_session.add(state)
    await test_session.commit()
    
    # Получаем список индексов
    result = await test_session.execute(
        text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'user_states'
        """)
    )
    indexes = {row[0]: row[1] for row in result}
    
    # Проверяем наличие необходимых индексов
    assert "ix_user_states_user_id" in indexes
    assert "ix_user_states_updated_at" in indexes

@pytest.mark.asyncio
async def test_transaction_indexes(test_session):
    """Тест наличия индексов в таблице transactions."""
    # Создаем пользователя и транзакцию
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user_transaction"
    )
    test_session.add(user)
    await test_session.flush()
    
    transaction = Transaction(
        user_id=user.id,
        amount=100.00,
        type="deposit",
        description="Test transaction"
    )
    test_session.add(transaction)
    await test_session.commit()
    
    # Получаем список индексов
    result = await test_session.execute(
        text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'transactions'
        """)
    )
    indexes = {row[0]: row[1] for row in result}
    
    # Проверяем наличие необходимых индексов
    assert "ix_transactions_user_id" in indexes
    assert "ix_transactions_type" in indexes
    assert "ix_transactions_created_at" in indexes

@pytest.mark.asyncio
async def test_index_usage(test_session):
    """Тест использования индексов в запросах."""
    # Создаем пользователя
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user_index_usage"
    )
    test_session.add(user)
    await test_session.commit()
    
    # Проверяем использование индекса при поиске по telegram_id
    result = await test_session.execute(
        text("""
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT * FROM users WHERE telegram_id = :telegram_id
        """),
        {"telegram_id": user.telegram_id}
    )
    plan = result.scalar()
    
    # Проверяем, что используется индекс
    assert any(
        node.get("Node Type") == "Index Scan" 
        and "ix_users_telegram_id" in node.get("Index Name", "")
        for node in plan[0]["Plan"].get("Plans", [])
    )

@pytest.mark.asyncio
async def test_composite_indexes(test_session):
    """Тест составных индексов."""
    # Создаем пользователя и транзакции
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user_composite"
    )
    test_session.add(user)
    await test_session.flush()
    
    # Создаем несколько транзакций
    for i in range(3):
        transaction = Transaction(
            user_id=user.id,
            amount=100.00 + i,
            type="deposit",
            description=f"Test transaction {i}"
        )
        test_session.add(transaction)
    await test_session.commit()
    
    # Получаем список индексов
    result = await test_session.execute(
        text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'transactions'
        """)
    )
    indexes = {row[0]: row[1] for row in result}
    
    # Проверяем наличие составных индексов
    composite_indexes = [
        name for name, definition in indexes.items()
        if "CREATE INDEX" in definition and "," in definition
    ]
    assert len(composite_indexes) > 0
    
    # Проверяем использование составного индекса
    result = await test_session.execute(
        text("""
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT * FROM transactions 
        WHERE user_id = :user_id AND type = 'deposit'
        ORDER BY created_at DESC
        """),
        {"user_id": user.id}
    )
    plan = result.scalar()
    
    # Проверяем, что используется составной индекс
    assert any(
        node.get("Node Type") == "Index Scan" 
        and any(idx in node.get("Index Name", "") for idx in composite_indexes)
        for node in plan[0]["Plan"].get("Plans", [])
    ) 