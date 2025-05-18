"""
Репозиторий для работы с пользователями.
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from frontend_bot.models.base import User, UserBalance
from frontend_bot.config import settings

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
    
    async def create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
        phone_number: Optional[str] = None,
        is_bot: bool = False,
        is_premium: Optional[bool] = None,
        last_active_at: Optional[datetime] = None,
        is_blocked: bool = False,
        settings: Optional[dict] = None,
        extra_data: Optional[dict] = None,
    ) -> User:
        """
        Создает нового пользователя с расширенными полями.
        """
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            phone_number=phone_number,
            is_bot=is_bot,
            is_premium=is_premium,
            last_active_at=last_active_at,
            is_blocked=is_blocked,
            settings=settings,
            extra_data=extra_data,
        )
        self.session.add(user)
        await self.session.flush()
        # Создаем начальный баланс
        balance = UserBalance(user_id=user.id, coins=settings.INITIAL_BALANCE if settings else 0)
        self.session.add(balance)
        await self.session.commit()
        return user
    
    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        language_code: Optional[str] = None,
        phone_number: Optional[str] = None,
        is_bot: bool = False,
        is_premium: Optional[bool] = None,
        last_active_at: Optional[datetime] = None,
        is_blocked: bool = False,
        settings: Optional[dict] = None,
        extra_data: Optional[dict] = None,
    ) -> User:
        """
        Получает пользователя или создает нового с расширенными полями.
        """
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            user = await self.create(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
                phone_number=phone_number,
                is_bot=is_bot,
                is_premium=is_premium,
                last_active_at=last_active_at,
                is_blocked=is_blocked,
                settings=settings,
                extra_data=extra_data,
            )
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
    
    async def update_if_changed(
        self,
        user: User,
        username: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
    ) -> None:
        """
        Обновляет username, first_name, last_name пользователя, если они изменились.
        """
        updated = False
        if user.username != username:
            user.username = username
            updated = True
        if user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if user.last_name != last_name:
            user.last_name = last_name
            updated = True
        if updated:
            await self.session.commit() 