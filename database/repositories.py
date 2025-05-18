"""
Репозитории для работы с базой данных.
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import uuid
import logging

from .models import (
    Base, UserProfile, UserState, UserBalance,
    UserAvatar, UserTranscript, Transaction, UserHistory
)

logger = logging.getLogger(__name__)

class BaseRepository:
    """Базовый класс для всех репозиториев."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self):
        """Сохраняет изменения в базе данных."""
        try:
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Ошибка при сохранении: {e}")
            raise

    async def rollback(self):
        """Откатывает изменения в базе данных."""
        await self.session.rollback()

    async def paginate(self, query, page: int = 1, per_page: int = 20) -> Tuple[List[Any], int]:
        """Добавляет пагинацию к запросу."""
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        items = (await self.session.execute(
            query.offset((page - 1) * per_page).limit(per_page)
        )).scalars().all()
        return items, total


class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями."""

    async def create(self, telegram_id: int, first_name: str, last_name: Optional[str] = None,
                    username: Optional[str] = None, language_code: Optional[str] = None) -> UserProfile:
        """Создает нового пользователя."""
        try:
            user = UserProfile(
                user_id=telegram_id,
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                language_code=language_code
            )
            self.session.add(user)
            await self.commit()
            return user
        except IntegrityError:
            await self.rollback()
            return await self.get_by_telegram_id(telegram_id)

    async def get_by_telegram_id(self, telegram_id: int, load_related: bool = False) -> Optional[UserProfile]:
        """Получает пользователя по telegram_id."""
        query = select(UserProfile).where(UserProfile.telegram_id == telegram_id)
        
        if load_related:
            query = query.options(
                selectinload(UserProfile.state),
                selectinload(UserProfile.balance),
                selectinload(UserProfile.avatars),
                selectinload(UserProfile.transcripts),
                selectinload(UserProfile.transactions),
                selectinload(UserProfile.history)
            )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, telegram_id: int, **kwargs) -> Optional[UserProfile]:
        """Обновляет данные пользователя."""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            await self.commit()
        return user


class UserStateRepository(BaseRepository):
    """Репозиторий для работы с состоянием пользователя."""

    async def get_by_user_id(self, user_id: int) -> Optional[UserState]:
        """Получает состояние пользователя."""
        result = await self.session.execute(
            select(UserState)
            .where(UserState.user_id == user_id)
            .options(joinedload(UserState.user))
        )
        return result.scalar_one_or_none()

    async def update_state(self, user_id: int, state_data: Dict[str, Any]) -> UserState:
        """Обновляет состояние пользователя."""
        state = await self.get_by_user_id(user_id)
        if not state:
            state = UserState(user_id=user_id, state_data=state_data)
            self.session.add(state)
        else:
            state.state_data.update(state_data)
            state.updated_at = datetime.utcnow()
        await self.commit()
        return state


class UserBalanceRepository(BaseRepository):
    """Репозиторий для работы с балансом пользователя."""

    async def get_by_user_id(self, user_id: int) -> Optional[UserBalance]:
        """Получает баланс пользователя."""
        result = await self.session.execute(
            select(UserBalance)
            .where(UserBalance.user_id == user_id)
            .options(joinedload(UserBalance.user))
        )
        return result.scalar_one_or_none()

    async def update_balance(self, user_id: int, amount: float) -> UserBalance:
        """Обновляет баланс пользователя атомарно."""
        # Используем SELECT FOR UPDATE для блокировки строки
        async with self.session.begin_nested():
            result = await self.session.execute(
                select(UserBalance)
                .where(UserBalance.user_id == user_id)
                .with_for_update()
            )
            balance = result.scalar_one_or_none()
            
            if not balance:
                balance = UserBalance(user_id=user_id, coins=amount)
                self.session.add(balance)
            else:
                new_balance = balance.coins + amount
                if new_balance < 0:
                    raise ValueError("Недостаточно средств")
                balance.coins = new_balance
                balance.updated_at = datetime.utcnow()
            
            await self.commit()
            return balance


class UserAvatarRepository(BaseRepository):
    """Репозиторий для работы с аватарами пользователя."""

    async def create(self, user_id: int, avatar_data: Dict[str, Any]) -> UserAvatar:
        """Создает новый аватар."""
        avatar = UserAvatar(
            user_id=user_id,
            avatar_data=avatar_data
        )
        self.session.add(avatar)
        await self.commit()
        return avatar

    async def get_by_id(self, avatar_id: uuid.UUID) -> Optional[UserAvatar]:
        """Получает аватар по ID."""
        result = await self.session.execute(
            select(UserAvatar)
            .where(UserAvatar.id == avatar_id)
            .options(joinedload(UserAvatar.user))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int, page: int = 1, per_page: int = 20) -> Tuple[List[UserAvatar], int]:
        """Получает все аватары пользователя с пагинацией."""
        query = (
            select(UserAvatar)
            .where(UserAvatar.user_id == user_id)
            .order_by(UserAvatar.created_at.desc())
        )
        return await self.paginate(query, page, per_page)


class UserTranscriptRepository(BaseRepository):
    """Репозиторий для работы с транскриптами пользователя."""

    async def create(self, user_id: int, transcript_data: Dict[str, Any]) -> UserTranscript:
        """Создает новый транскрипт."""
        transcript = UserTranscript(
            user_id=user_id,
            transcript_data=transcript_data
        )
        self.session.add(transcript)
        await self.commit()
        return transcript

    async def get_by_id(self, transcript_id: uuid.UUID) -> Optional[UserTranscript]:
        """Получает транскрипт по ID."""
        result = await self.session.execute(
            select(UserTranscript)
            .where(UserTranscript.id == transcript_id)
            .options(joinedload(UserTranscript.user))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int, page: int = 1, per_page: int = 20) -> Tuple[List[UserTranscript], int]:
        """Получает все транскрипты пользователя с пагинацией."""
        query = (
            select(UserTranscript)
            .where(UserTranscript.user_id == user_id)
            .order_by(UserTranscript.created_at.desc())
        )
        return await self.paginate(query, page, per_page)


class TransactionRepository(BaseRepository):
    """Репозиторий для работы с транзакциями."""

    async def create(self, user_id: int, amount: float, type: str,
                    description: Optional[str] = None) -> Transaction:
        """Создает новую транзакцию."""
        if type not in ('credit', 'debit'):
            raise ValueError("Недопустимый тип транзакции")
            
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type=type,
            description=description
        )
        self.session.add(transaction)
        await self.commit()
        return transaction

    async def get_by_user_id(self, user_id: int, page: int = 1, per_page: int = 20) -> Tuple[List[Transaction], int]:
        """Получает все транзакции пользователя с пагинацией."""
        query = (
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
        )
        return await self.paginate(query, page, per_page)


class UserHistoryRepository(BaseRepository):
    """Репозиторий для работы с историей пользователя."""

    VALID_ACTION_TYPES = {
        'avatar_created', 'transcript_created',
        'balance_updated', 'transaction_created'
    }

    async def create(self, user_id: int, action_type: str,
                    action_data: Dict[str, Any]) -> UserHistory:
        """Создает новую запись в истории."""
        if action_type not in self.VALID_ACTION_TYPES:
            raise ValueError(f"Недопустимый тип действия. Допустимые типы: {self.VALID_ACTION_TYPES}")
            
        history = UserHistory(
            user_id=user_id,
            action_type=action_type,
            action_data=action_data
        )
        self.session.add(history)
        await self.commit()
        return history

    async def get_by_user_id(self, user_id: int, page: int = 1, per_page: int = 20) -> Tuple[List[UserHistory], int]:
        """Получает всю историю пользователя с пагинацией."""
        query = (
            select(UserHistory)
            .where(UserHistory.user_id == user_id)
            .order_by(UserHistory.created_at.desc())
        )
        return await self.paginate(query, page, per_page) 