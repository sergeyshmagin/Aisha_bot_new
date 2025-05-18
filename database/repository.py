"""
Репозиторий для работы с базой данных.
"""

from typing import List, Optional, TypeVar, Generic, Type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Message

T = TypeVar("T")

class BaseRepository(Generic[T]):
    """Базовый класс репозитория."""
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        """
        Инициализация репозитория.
        
        Args:
            session: Сессия базы данных.
            model: Модель базы данных.
        """
        self.session = session
        self.model = model
    
    async def create(self, **kwargs) -> T:
        """
        Создание записи.
        
        Args:
            **kwargs: Параметры для создания записи.
        
        Returns:
            Созданная запись.
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """
        Получение записи по ID.
        
        Args:
            id: ID записи.
        
        Returns:
            Найденная запись или None.
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, id: int, **kwargs) -> Optional[T]:
        """
        Обновление записи.
        
        Args:
            id: ID записи.
            **kwargs: Параметры для обновления.
        
        Returns:
            Обновленная запись или None.
        """
        instance = await self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            await self.session.commit()
            await self.session.refresh(instance)
        return instance
    
    async def delete(self, id: int) -> bool:
        """
        Удаление записи.
        
        Args:
            id: ID записи.
        
        Returns:
            True, если запись удалена, иначе False.
        """
        instance = await self.get_by_id(id)
        if instance:
            await self.session.delete(instance)
            await self.session.commit()
            return True
        return False

class UserRepository(BaseRepository[User]):
    """Репозиторий для работы с пользователями."""
    
    def __init__(self, session: AsyncSession):
        """Инициализация репозитория пользователей."""
        super().__init__(session, User)
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Получение пользователя по telegram_id.
        
        Args:
            telegram_id: ID пользователя в Telegram.
        
        Returns:
            Найденный пользователь или None.
        """
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

class MessageRepository(BaseRepository[Message]):
    """Репозиторий для работы с сообщениями."""
    
    def __init__(self, session: AsyncSession):
        """Инициализация репозитория сообщений."""
        super().__init__(session, Message)
    
    async def get_by_user_id(self, user_id: int) -> List[Message]:
        """
        Получение сообщений пользователя.
        
        Args:
            user_id: ID пользователя.
        
        Returns:
            Список сообщений пользователя.
        """
        result = await self.session.execute(
            select(Message).where(Message.user_id == user_id)
        )
        return result.scalars().all() 