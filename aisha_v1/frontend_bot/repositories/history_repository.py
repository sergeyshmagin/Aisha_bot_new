"""
Репозиторий для работы с историей пользователей.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import UserHistory


class UserHistoryRepository:
    """Репозиторий для работы с историей пользователей."""
    
    def __init__(self, session: AsyncSession):
        """Инициализация репозитория.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session
    
    async def create(self, user_id: str, action_type: str, action_data: Dict[str, Any]) -> UserHistory:
        """Создает новую запись в истории пользователя.
        
        Args:
            user_id: ID пользователя
            action_type: Тип действия
            action_data: Данные действия
            
        Returns:
            Созданная запись истории
        """
        history = UserHistory(
            user_id=user_id,
            action_type=action_type,
            action_data=action_data
        )
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history
    
    async def get_by_id(self, history_id: str) -> Optional[UserHistory]:
        """Получает запись истории по ID.
        
        Args:
            history_id: ID записи истории
            
        Returns:
            Запись истории или None, если не найдена
        """
        result = await self.session.execute(
            select(UserHistory).where(UserHistory.id == history_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: str) -> List[UserHistory]:
        """Получает всю историю пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список записей истории
        """
        result = await self.session.execute(
            select(UserHistory).where(UserHistory.user_id == user_id)
        )
        return result.scalars().all()
    
    async def get_by_action_type(self, user_id: str, action_type: str) -> List[UserHistory]:
        """Получает историю пользователя по типу действия.
        
        Args:
            user_id: ID пользователя
            action_type: Тип действия
            
        Returns:
            Список записей истории
        """
        result = await self.session.execute(
            select(UserHistory)
            .where(UserHistory.user_id == user_id)
            .where(UserHistory.action_type == action_type)
        )
        return result.scalars().all()
    
    async def delete(self, history_id: str) -> bool:
        """Удаляет запись истории.
        
        Args:
            history_id: ID записи истории
            
        Returns:
            True, если запись была удалена, иначе False
        """
        history = await self.get_by_id(history_id)
        if history:
            await self.session.delete(history)
            await self.session.commit()
            return True
        return False 