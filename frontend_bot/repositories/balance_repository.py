"""
Репозиторий для работы с балансом пользователей.
"""

from typing import Optional, List
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from frontend_bot.models.base import UserBalance, Transaction
from frontend_bot.config import MIN_BALANCE

class BalanceRepository:
    """Репозиторий для работы с балансом пользователей."""
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.
        
        Args:
            session: Сессия базы данных
        """
        self.session = session
    
    async def get_balance(self, user_id: int) -> Optional[UserBalance]:
        """
        Получает баланс пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[UserBalance]: Баланс пользователя или None
        """
        result = await self.session.execute(
            select(UserBalance).where(UserBalance.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def add_coins(self, user_id: int, amount: Decimal, description: str) -> None:
        """
        Добавляет монеты пользователю.
        
        Args:
            user_id: ID пользователя
            amount: Количество монет
            description: Описание транзакции
        """
        balance = await self.get_balance(user_id)
        if balance:
            balance.coins += amount
            
            # Создаем запись о транзакции
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                type="deposit",
                description=description
            )
            self.session.add(transaction)
            
            await self.session.commit()
    
    async def subtract_coins(self, user_id: int, amount: Decimal, description: str) -> bool:
        """
        Списывает монеты у пользователя.
        
        Args:
            user_id: ID пользователя
            amount: Количество монет
            description: Описание транзакции
            
        Returns:
            bool: True если списание успешно, False если недостаточно средств
        """
        balance = await self.get_balance(user_id)
        if balance and balance.coins >= amount:
            balance.coins -= amount
            
            # Создаем запись о транзакции
            transaction = Transaction(
                user_id=user_id,
                amount=-amount,
                type="withdraw",
                description=description
            )
            self.session.add(transaction)
            
            await self.session.commit()
            return True
        return False
    
    async def get_transactions(self, user_id: int, limit: int = 10) -> List[Transaction]:
        """
        Получает историю транзакций пользователя.
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество транзакций
            
        Returns:
            List[Transaction]: Список транзакций
        """
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def check_balance(self, user_id: int, amount: Decimal) -> bool:
        """
        Проверяет, достаточно ли средств у пользователя.
        
        Args:
            user_id: ID пользователя
            amount: Требуемая сумма
            
        Returns:
            bool: True если достаточно средств, False если нет
        """
        balance = await self.get_balance(user_id)
        return balance is not None and balance.coins >= amount
    
    async def get_total_balance(self) -> Decimal:
        """
        Получает общий баланс всех пользователей.
        
        Returns:
            Decimal: Общий баланс
        """
        result = await self.session.execute(
            select(UserBalance.coins)
        )
        balances = result.scalars().all()
        return sum(balances) if balances else Decimal('0') 