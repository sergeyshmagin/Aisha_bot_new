"""
Репозиторий для работы с пользователями.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from frontend_bot.models.base import User, UserBalance
from frontend_bot.config import INITIAL_BALANCE

class UserRepository:
    """Репозиторий для работы с пользователями."""
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация репозитория.
        
        Args:
            session: Сессия базы данных
        """
        self.session = session
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Получает пользователя по Telegram ID.
        
        Args:
            telegram_id: ID пользователя в Telegram
            
        Returns:
            Optional[User]: Пользователь или None
        """
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, telegram_id: int, username: Optional[str] = None) -> User:
        """
        Создает нового пользователя.
        
        Args:
            telegram_id: ID пользователя в Telegram
            username: Имя пользователя в Telegram
            
        Returns:
            User: Созданный пользователь
        """
        user = User(telegram_id=telegram_id, username=username)
        self.session.add(user)
        await self.session.flush()
        
        # Создаем начальный баланс
        balance = UserBalance(user_id=user.id, coins=INITIAL_BALANCE)
        self.session.add(balance)
        
        await self.session.commit()
        return user
    
    async def get_or_create(self, telegram_id: int, username: Optional[str] = None) -> User:
        """
        Получает пользователя или создает нового.
        
        Args:
            telegram_id: ID пользователя в Telegram
            username: Имя пользователя в Telegram
            
        Returns:
            User: Пользователь
        """
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            user = await self.create(telegram_id, username)
        return user
    
    async def update_username(self, user_id: int, username: str) -> None:
        """
        Обновляет имя пользователя.
        
        Args:
            user_id: ID пользователя
            username: Новое имя пользователя
        """
        user = await self.session.get(User, user_id)
        if user:
            user.username = username
            await self.session.commit()
    
    async def get_all(self) -> List[User]:
        """
        Получает всех пользователей.
        
        Returns:
            List[User]: Список пользователей
        """
        result = await self.session.execute(select(User))
        return result.scalars().all()
    
    async def delete(self, user_id: int) -> None:
        """
        Удаляет пользователя.
        
        Args:
            user_id: ID пользователя
        """
        user = await self.session.get(User, user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit() 