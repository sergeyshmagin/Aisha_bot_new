"""
Репозиторий для работы с состояниями пользователей.
"""

from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from frontend_bot.models.base import UserState

class StateRepository:
    """Репозиторий для работы с состояниями пользователей."""
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.
        
        Args:
            session: Сессия базы данных
        """
        self.session = session
    
    async def get_state(self, user_id: int) -> Optional[UserState]:
        """
        Получает состояние пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[UserState]: Состояние пользователя или None
        """
        result = await self.session.execute(
            select(UserState).where(UserState.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def set_state(self, user_id: int, state_data: Dict[str, Any]) -> UserState:
        """
        Устанавливает состояние пользователя.
        
        Args:
            user_id: ID пользователя
            state_data: Данные состояния
            
        Returns:
            UserState: Обновленное состояние
        """
        state = await self.get_state(user_id)
        if state:
            state.state_data = state_data
        else:
            state = UserState(user_id=user_id, state_data=state_data)
            self.session.add(state)
        
        await self.session.commit()
        return state
    
    async def update_state(self, user_id: int, state_data: Dict[str, Any]) -> Optional[UserState]:
        """
        Обновляет состояние пользователя, сохраняя существующие данные.
        
        Args:
            user_id: ID пользователя
            state_data: Новые данные состояния
            
        Returns:
            Optional[UserState]: Обновленное состояние или None
        """
        state = await self.get_state(user_id)
        if state:
            # Создаем копию текущих данных
            current_data = state.state_data.copy()
            # Обновляем данные, сохраняя существующие
            for key, value in state_data.items():
                if isinstance(value, dict) and key in current_data and isinstance(current_data[key], dict):
                    current_data[key].update(value)
                else:
                    current_data[key] = value
            state.state_data = current_data
            await self.session.commit()
        return state
    
    async def clear_state(self, user_id: int) -> None:
        """
        Очищает состояние пользователя.
        
        Args:
            user_id: ID пользователя
        """
        state = await self.get_state(user_id)
        if state:
            await self.session.delete(state)
            await self.session.commit()
    
    async def get_all_states(self) -> Dict[int, Dict[str, Any]]:
        """
        Получает состояния всех пользователей.
        
        Returns:
            Dict[int, Dict[str, Any]]: Словарь состояний пользователей
        """
        result = await self.session.execute(select(UserState))
        states = result.scalars().all()
        return {state.user_id: state.state_data for state in states} 