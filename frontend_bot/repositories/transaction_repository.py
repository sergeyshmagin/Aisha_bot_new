"""
Репозиторий для работы с транзакциями.
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database.models import Transaction

class TransactionRepository:
    """Репозиторий для работы с транзакциями."""
    
    def __init__(self, session: AsyncSession):
        """Инициализация репозитория.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session
    
    async def create(self, transaction: Transaction) -> Transaction:
        """Создание новой транзакции.
        
        Args:
            transaction: Объект транзакции для создания
            
        Returns:
            Transaction: Созданная транзакция с ID
        """
        self.session.add(transaction)
        await self.session.flush()
        await self.session.refresh(transaction)
        return transaction
    
    async def get_by_id(self, transaction_id: int) -> Transaction:
        """Получение транзакции по ID.
        
        Args:
            transaction_id: ID транзакции
            
        Returns:
            Transaction: Найденная транзакция или None
        """
        result = await self.session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_transactions(self, user_id: int) -> List[Transaction]:
        """Получение всех транзакций пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Transaction]: Список транзакций пользователя,
            отсортированный по времени создания (новые сверху)
        """
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(desc(Transaction.created_at))
        )
        return result.scalars().all()
    
    async def update(self, transaction: Transaction) -> Transaction:
        """Обновление транзакции.
        
        Args:
            transaction: Объект транзакции для обновления
            
        Returns:
            Transaction: Обновленная транзакция
        """
        await self.session.flush()
        await self.session.refresh(transaction)
        return transaction
    
    async def delete(self, transaction: Transaction) -> None:
        """Удаление транзакции.
        
        Args:
            transaction: Объект транзакции для удаления
        """
        await self.session.delete(transaction)
        await self.session.flush() 