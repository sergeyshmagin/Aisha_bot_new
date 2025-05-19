"""
Репозиторий для работы с аватарами пользователей.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import UserAvatar


class UserAvatarRepository:
    """Репозиторий для работы с аватарами пользователей."""
    
    def __init__(self, session: AsyncSession):
        """Инициализация репозитория.
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session
    
    async def create(self, user_id: str, avatar_data: Dict[str, Any]) -> UserAvatar:
        """Создает новый аватар пользователя.
        
        Args:
            user_id: ID пользователя
            avatar_data: Данные аватара
            
        Returns:
            Созданный аватар
        """
        avatar = UserAvatar(
            user_id=user_id,
            avatar_data=avatar_data
        )
        self.session.add(avatar)
        await self.session.commit()
        await self.session.refresh(avatar)
        return avatar
    
    async def get_by_id(self, avatar_id: str) -> Optional[UserAvatar]:
        """Получает аватар по ID.
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            Аватар или None, если не найден
        """
        avatar_id = str(avatar_id)  # Унификация типа
        result = await self.session.execute(
            select(UserAvatar).where(UserAvatar.id == avatar_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: str) -> List[UserAvatar]:
        """Получает все аватары пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Список аватаров
        """
        result = await self.session.execute(
            select(UserAvatar).where(UserAvatar.user_id == user_id)
        )
        return result.scalars().all()
    
    async def update(self, avatar_id: str, avatar_data: Dict[str, Any]) -> Optional[UserAvatar]:
        """Обновляет данные аватара.
        
        Args:
            avatar_id: ID аватара
            avatar_data: Новые данные аватара
            
        Returns:
            Обновленный аватар или None, если не найден
        """
        avatar = await self.get_by_id(avatar_id)
        if avatar:
            avatar.avatar_data = avatar_data
            await self.session.commit()
            await self.session.refresh(avatar)
        return avatar
    
    async def delete(self, avatar_id: str) -> bool:
        """Удаляет аватар.
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            True, если аватар был удален, иначе False
        """
        avatar = await self.get_by_id(avatar_id)
        if avatar:
            await self.session.delete(avatar)
            await self.session.commit()
            return True
        return False 