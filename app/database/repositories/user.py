"""
Репозиторий для работы с пользователями
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.repositories.base import BaseRepositoryclass UserRepository(BaseRepository[User]):
    """
    Репозиторий для работы с пользователями
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        # Убеждаемся, что telegram_id является строкой
        if not isinstance(telegram_id, str):
            # Если это не строка, преобразуем в строку
            telegram_id = str(telegram_id)
        
        stmt = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_balance(self, user_id: int) -> Optional[User]:
        """Получить пользователя с балансом"""
        stmt = (
            select(self.model)
            .where(self.model.id == user_id)
            .join(self.model.balance)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_state(self, user_id: int) -> Optional[User]:
        """Получить пользователя с текущим состоянием"""
        stmt = (
            select(self.model)
            .where(self.model.id == user_id)
            .join(self.model.state)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
