"""
Асинхронные утилиты для работы с балансом пользователя через PostgreSQL (BalanceRepository).

Использование:
    await get_balance_pg(user_id, session)
    await add_coins_pg(user_id, amount, description, session)
    await subtract_coins_pg(user_id, amount, description, session)
    await get_transactions_pg(user_id, session, limit=10)
    await check_balance_pg(user_id, amount, session)
    await get_total_balance_pg(session)
"""

from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from frontend_bot.repositories.balance_repository import BalanceRepository
from frontend_bot.models.base import Transaction, UserBalance

async def get_balance_pg(user_id: int, session: AsyncSession) -> Optional[UserBalance]:
    """
    Получает баланс пользователя из PostgreSQL.
    """
    repo = BalanceRepository(session)
    return await repo.get_balance(user_id)

async def add_coins_pg(user_id: int, amount: Decimal, description: str, session: AsyncSession) -> None:
    """
    Добавляет монеты пользователю в PostgreSQL.
    """
    repo = BalanceRepository(session)
    await repo.add_coins(user_id, amount, description)

async def subtract_coins_pg(user_id: int, amount: Decimal, description: str, session: AsyncSession) -> bool:
    """
    Списывает монеты у пользователя в PostgreSQL.
    Возвращает True, если успешно, иначе False.
    """
    repo = BalanceRepository(session)
    return await repo.subtract_coins(user_id, amount, description)

async def get_transactions_pg(user_id: int, session: AsyncSession, limit: int = 10) -> List[Transaction]:
    """
    Получает историю транзакций пользователя из PostgreSQL.
    """
    repo = BalanceRepository(session)
    return await repo.get_transactions(user_id, limit)

async def check_balance_pg(user_id: int, amount: Decimal, session: AsyncSession) -> bool:
    """
    Проверяет, достаточно ли средств у пользователя в PostgreSQL.
    """
    repo = BalanceRepository(session)
    return await repo.check_balance(user_id, amount)

async def get_total_balance_pg(session: AsyncSession) -> Decimal:
    """
    Получает общий баланс всех пользователей из PostgreSQL.
    """
    repo = BalanceRepository(session)
    return await repo.get_total_balance() 