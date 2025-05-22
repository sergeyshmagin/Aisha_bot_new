"""
Тесты для конкурентных операций.
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from frontend_bot.repositories.balance_repository import BalanceRepository
from frontend_bot.repositories.transaction_repository import TransactionRepository
from database.models import Transaction, TransactionType
from decimal import Decimal

class TestConcurrentOperations:
    """Тесты для конкурентных операций."""
    
    @pytest.fixture
    async def balance_repository(self, test_session: AsyncSession) -> BalanceRepository:
        """Создает репозиторий балансов."""
        return BalanceRepository(test_session)
    
    @pytest.fixture
    async def transaction_repository(self, test_session: AsyncSession) -> TransactionRepository:
        """Создает репозиторий транзакций."""
        return TransactionRepository(test_session)
    
    async def test_concurrent_deposits(self, balance_repository: BalanceRepository, test_user):
        """Тест конкурентных пополнений."""
        # Создаем начальный баланс
        initial_balance = await balance_repository.create(
            user_id=test_user.id,
            coins=Decimal("100.00")
        )
        
        # Создаем несколько конкурентных пополнений
        async def deposit(amount: Decimal):
            return await balance_repository.add_coins(test_user.id, amount)
        
        # Запускаем конкурентные пополнения
        tasks = [
            deposit(Decimal("50.00")),
            deposit(Decimal("30.00")),
            deposit(Decimal("20.00"))
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Проверяем финальный баланс
        final_balance = await balance_repository.get_balance(test_user.id)
        assert final_balance.coins == Decimal("200.00")  # 100 + 50 + 30 + 20
    
    async def test_concurrent_withdrawals(self, balance_repository: BalanceRepository, test_user):
        """Тест конкурентных списаний."""
        # Создаем начальный баланс
        initial_balance = await balance_repository.create(
            user_id=test_user.id,
            coins=Decimal("100.00")
        )
        
        # Создаем несколько конкурентных списаний
        async def withdraw(amount: Decimal):
            return await balance_repository.deduct_coins(test_user.id, amount)
        
        # Запускаем конкурентные списания
        tasks = [
            withdraw(Decimal("30.00")),
            withdraw(Decimal("20.00")),
            withdraw(Decimal("10.00"))
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Проверяем финальный баланс
        final_balance = await balance_repository.get_balance(test_user.id)
        assert final_balance.coins == Decimal("40.00")  # 100 - 30 - 20 - 10
    
    async def test_concurrent_mixed_operations(self, 
                                             balance_repository: BalanceRepository,
                                             transaction_repository: TransactionRepository,
                                             test_user):
        """Тест смешанных конкурентных операций."""
        # Создаем начальный баланс
        initial_balance = await balance_repository.create(
            user_id=test_user.id,
            coins=Decimal("100.00")
        )
        
        # Создаем конкурентные операции
        async def deposit(amount: Decimal):
            transaction = Transaction(
                user_id=test_user.id,
                amount=amount,
                type=TransactionType.DEPOSIT,
                description=f"Deposit {amount}"
            )
            await transaction_repository.create(transaction)
            return await balance_repository.add_coins(test_user.id, amount)
        
        async def withdraw(amount: Decimal):
            transaction = Transaction(
                user_id=test_user.id,
                amount=amount,
                type=TransactionType.WITHDRAWAL,
                description=f"Withdrawal {amount}"
            )
            await transaction_repository.create(transaction)
            return await balance_repository.deduct_coins(test_user.id, amount)
        
        # Запускаем смешанные операции
        tasks = [
            deposit(Decimal("50.00")),
            withdraw(Decimal("30.00")),
            deposit(Decimal("20.00")),
            withdraw(Decimal("10.00"))
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Проверяем финальный баланс
        final_balance = await balance_repository.get_balance(test_user.id)
        assert final_balance.coins == Decimal("130.00")  # 100 + 50 - 30 + 20 - 10
        
        # Проверяем транзакции
        transactions = await transaction_repository.get_user_transactions(test_user.id)
        assert len(transactions) == 4
        
        # Проверяем, что все транзакции уникальны
        transaction_descriptions = {t.description for t in transactions}
        assert len(transaction_descriptions) == 4
    
    async def test_concurrent_insufficient_funds(self, balance_repository: BalanceRepository, test_user):
        """Тест конкурентных списаний при недостаточном балансе."""
        # Создаем начальный баланс
        initial_balance = await balance_repository.create(
            user_id=test_user.id,
            coins=Decimal("100.00")
        )
        
        # Создаем конкурентные списания, превышающие баланс
        async def withdraw(amount: Decimal):
            try:
                return await balance_repository.deduct_coins(test_user.id, amount)
            except ValueError:
                return None
        
        # Запускаем конкурентные списания
        tasks = [
            withdraw(Decimal("80.00")),
            withdraw(Decimal("50.00")),
            withdraw(Decimal("30.00"))
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Проверяем, что только одно списание прошло успешно
        successful_withdrawals = [r for r in results if r is not None]
        assert len(successful_withdrawals) == 1
        
        # Проверяем финальный баланс
        final_balance = await balance_repository.get_balance(test_user.id)
        assert final_balance.coins == Decimal("20.00")  # 100 - 80 (только одно списание прошло) 