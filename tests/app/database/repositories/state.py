"""
Репозиторий для работы с состояниями пользователей
"""
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserState
from app.database.repositories.base import BaseRepository


class StateRepository(BaseRepository[UserState]):
    """
    Репозиторий для работы с состояниями пользователей
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserState)

    async def get_user_state(self, user_id: int) -> Optional[UserState]:
        """Получить состояние пользователя"""
        stmt = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_state(self, user_id: int, state_data: Dict) -> UserState:
        """Установить состояние пользователя"""
        state = await self.get_user_state(user_id)
        if state:
            return await self.update(state.id, {"state_data": state_data})
        return await self.create({"user_id": user_id, "state_data": state_data})

    async def clear_state(self, user_id: int) -> bool:
        """Очистить состояние пользователя"""
        state = await self.get_user_state(user_id)
        if state:
            return await self.delete(state.id)
        return False
