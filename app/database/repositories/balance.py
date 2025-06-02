"""
Репозиторий для работы с балансом пользователей
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserBalance
from app.database.repositories.base import BaseRepositoryclass BalanceRepository(BaseRepository[UserBalance]):
    """
    Репозиторий для работы с балансом пользователей
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserBalance)

    async def get_user_balance(self, user_id: int) -> Optional[UserBalance]:
        """Получить баланс пользователя"""
        stmt = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_coins(self, user_id: int, amount: float) -> UserBalance:
        """Добавить монеты пользователю"""
        balance = await self.get_user_balance(user_id)
        if balance:
            return await self.update(balance.id, {"coins": balance.coins + amount})
        return await self.create({"user_id": user_id, "coins": amount})

    async def remove_coins(self, user_id: int, amount: float) -> Optional[UserBalance]:
        """Снять монеты с баланса пользователя"""
        balance = await self.get_user_balance(user_id)
        if balance and balance.coins >= amount:
            return await self.update(balance.id, {"coins": balance.coins - amount})
        return None

    async def has_enough_coins(self, user_id: int, amount: float) -> bool:
        """Проверить, достаточно ли монет у пользователя"""
        balance = await self.get_user_balance(user_id)
        return balance is not None and balance.coins >= amount
