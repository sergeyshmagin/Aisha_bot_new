"""
Тесты для транзакций PostgreSQL.
"""

import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from frontend_bot.models.base import User, UserBalance, UserAvatar, UserState, Transaction
from tests.conftest import generate_telegram_id
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select

@pytest.mark.asyncio
async def test_transaction_rollback(test_session):
    """Тест отката транзакции при ошибке."""
    telegram_id = generate_telegram_id()
    
    # Начинаем транзакцию
    async with test_session.begin():
        # Создаем пользователя
        user = User(
            telegram_id=telegram_id,
            username="test_user_rollback"
        )
        test_session.add(user)
        await test_session.flush()
        
        # Пробуем создать дубликат (должно вызвать ошибку)
        with pytest.raises(IntegrityError):
            duplicate_user = User(
                telegram_id=telegram_id,
                username="test_user_rollback_2"
            )
            test_session.add(duplicate_user)
            await test_session.flush()
    
    # Проверяем, что транзакция откатилась
    result = await test_session.execute(text("SELECT * FROM users WHERE telegram_id = :telegram_id"), {"telegram_id": telegram_id})
    assert result.first() is None

@pytest.mark.asyncio
async def test_cascade_delete(test_session):
    """Тест каскадного удаления связанных записей."""
    # Создаем пользователя
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user"
    )
    test_session.add(user)
    await test_session.flush()
    
    # Создаем связанные записи
    balance = UserBalance(
        user_id=user.id,
        coins=Decimal("100.00")
    )
    test_session.add(balance)
    
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
    
    state = UserState(
        user_id=user.id,
        state_data={"current_state": "main_menu"}
    )
    test_session.add(state)
    
    transaction = Transaction(
        user_id=user.id,
        amount=Decimal("50.00"),
        type="deposit",
        description="Test deposit"
    )
    test_session.add(transaction)
    
    await test_session.commit()
    
    # Удаляем пользователя
    await test_session.delete(user)
    await test_session.commit()
    
    # Проверяем, что все связанные записи удалены
    result = await test_session.execute(
        select(UserBalance).where(UserBalance.user_id == user.id)
    )
    assert result.first() is None
    
    result = await test_session.execute(
        select(UserAvatar).where(UserAvatar.user_id == user.id)
    )
    assert result.first() is None
    
    result = await test_session.execute(
        select(UserState).where(UserState.user_id == user.id)
    )
    assert result.first() is None
    
    result = await test_session.execute(
        select(Transaction).where(Transaction.user_id == user.id)
    )
    assert result.first() is None

@pytest.mark.asyncio
async def test_concurrent_transactions(test_engine):
    """Тест конкурентных транзакций."""
    # Создаем две отдельные сессии
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session1, async_session() as session2:
        # Создаем пользователя в первой сессии
        user = User(
            telegram_id=generate_telegram_id(),
            username="concurrent_user_1"
        )
        session1.add(user)
        await session1.flush()
        
        # Создаем баланс в первой сессии
        balance = UserBalance(
            user_id=user.id,
            coins=Decimal("100.00")
        )
        session1.add(balance)
        await session1.commit()
        
        # Проверяем баланс во второй сессии
        result = await session2.execute(text("SELECT coins FROM user_balances WHERE user_id = :user_id"), {"user_id": user.id})
        assert result.scalar() == Decimal("100.00")
        
        # Обновляем баланс во второй сессии
        await session2.execute(text("UPDATE user_balances SET coins = :coins WHERE user_id = :user_id"), {"coins": Decimal("200.00"), "user_id": user.id})
        await session2.commit()
        
        # Проверяем финальное состояние в первой сессии
        result = await session1.execute(text("SELECT coins FROM user_balances WHERE user_id = :user_id"), {"user_id": user.id})
        assert result.scalar() == Decimal("200.00")

@pytest.mark.asyncio
async def test_transaction_isolation(test_engine):
    """Тест изоляции транзакций."""
    # Создаем две отдельные сессии
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session1, async_session() as session2:
        # Создаем пользователя в первой сессии
        user = User(
            telegram_id=generate_telegram_id(),
            username="isolation_test_user"
        )
        session1.add(user)
        await session1.flush()
        
        # Создаем баланс в первой сессии
        balance = UserBalance(
            user_id=user.id,
            coins=Decimal("100.00")
        )
        session1.add(balance)
        await session1.flush()
        
        # Проверяем, что изменения не видны во второй сессии
        result = await session2.execute(text("SELECT coins FROM user_balances WHERE user_id = :user_id"), {"user_id": user.id})
        assert result.scalar() is None
        
        # Коммитим изменения в первой сессии
        await session1.commit()
        
        # Теперь изменения должны быть видны во второй сессии
        result = await session2.execute(text("SELECT coins FROM user_balances WHERE user_id = :user_id"), {"user_id": user.id})
        assert result.scalar() == Decimal("100.00") 