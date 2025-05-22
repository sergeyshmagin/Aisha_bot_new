"""
Тесты для транзакций.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Transaction, TransactionType
from frontend_bot.repositories.transaction_repository import TransactionRepository
from frontend_bot.repositories.balance_repository import BalanceRepository
from decimal import Decimal

class TestTransactions:
    """Тесты для транзакций."""
    
    @pytest.fixture
    async def transaction_repository(self, test_session: AsyncSession) -> TransactionRepository:
        """Создает репозиторий транзакций."""
        return TransactionRepository(test_session)
    
    @pytest.fixture
    async def balance_repository(self, test_session: AsyncSession) -> BalanceRepository:
        """Создает репозиторий балансов."""
        return BalanceRepository(test_session)
    
    async def test_create_transaction(self, transaction_repository: TransactionRepository, test_user):
        """Тест создания транзакции."""
        transaction = Transaction(
            user_id=test_user.id,
            amount=Decimal("50.00"),
            type=TransactionType.DEPOSIT,
            description="Test deposit"
        )
        created_transaction = await transaction_repository.create(transaction)
        
        assert created_transaction.id is not None
        assert created_transaction.user_id == test_user.id
        assert created_transaction.amount == Decimal("50.00")
        assert created_transaction.type == TransactionType.DEPOSIT
        assert created_transaction.description == "Test deposit"
    
    async def test_get_user_transactions(self, transaction_repository: TransactionRepository, test_user):
        """Тест получения транзакций пользователя."""
        # Создаем несколько транзакций
        transactions = [
            Transaction(
                user_id=test_user.id,
                amount=Decimal("50.00"),
                type=TransactionType.DEPOSIT,
                description="Deposit 1"
            ),
            Transaction(
                user_id=test_user.id,
                amount=Decimal("30.00"),
                type=TransactionType.WITHDRAWAL,
                description="Withdrawal 1"
            ),
            Transaction(
                user_id=test_user.id,
                amount=Decimal("20.00"),
                type=TransactionType.DEPOSIT,
                description="Deposit 2"
            )
        ]
        
        for transaction in transactions:
            await transaction_repository.create(transaction)
        
        # Получаем все транзакции пользователя
        user_transactions = await transaction_repository.get_user_transactions(test_user.id)
        assert len(user_transactions) == 3
        
        # Проверяем сортировку по времени (новые сверху)
        assert user_transactions[0].description == "Deposit 2"
        assert user_transactions[1].description == "Withdrawal 1"
        assert user_transactions[2].description == "Deposit 1"
    
    async def test_transaction_with_balance_update(self, 
                                                 transaction_repository: TransactionRepository,
                                                 balance_repository: BalanceRepository,
                                                 test_user):
        """Тест транзакции с обновлением баланса."""
        # Создаем начальный баланс
        initial_balance = await balance_repository.create(
            user_id=test_user.id,
            coins=Decimal("100.00")
        )
        
        # Создаем транзакцию пополнения
        deposit = Transaction(
            user_id=test_user.id,
            amount=Decimal("50.00"),
            type=TransactionType.DEPOSIT,
            description="Test deposit"
        )
        await transaction_repository.create(deposit)
        
        # Обновляем баланс
        updated_balance = await balance_repository.add_coins(test_user.id, Decimal("50.00"))
        assert updated_balance.coins == Decimal("150.00")
        
        # Создаем транзакцию списания
        withdrawal = Transaction(
            user_id=test_user.id,
            amount=Decimal("30.00"),
            type=TransactionType.WITHDRAWAL,
            description="Test withdrawal"
        )
        await transaction_repository.create(withdrawal)
        
        # Обновляем баланс
        final_balance = await balance_repository.deduct_coins(test_user.id, Decimal("30.00"))
        assert final_balance.coins == Decimal("120.00")
        
        # Проверяем историю транзакций
        transactions = await transaction_repository.get_user_transactions(test_user.id)
        assert len(transactions) == 2
        assert transactions[0].type == TransactionType.WITHDRAWAL
        assert transactions[1].type == TransactionType.DEPOSIT 