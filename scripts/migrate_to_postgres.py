"""
Скрипт для миграции данных из Redis в PostgreSQL.
"""

import asyncio
import logging
from typing import Dict, Any

from frontend_bot.database.db import init_db, get_session
from frontend_bot.repositories.user_repository import UserRepository
from frontend_bot.repositories.state_repository import StateRepository
from frontend_bot.repositories.balance_repository import BalanceRepository
from frontend_bot.shared.redis_client import redis_client
from frontend_bot.config import INITIAL_BALANCE

logger = logging.getLogger(__name__)

async def migrate_users(redis_client, user_repo: UserRepository) -> Dict[str, int]:
    """
    Мигрирует пользователей из Redis в PostgreSQL.
    
    Args:
        redis_client: Клиент Redis
        user_repo: Репозиторий пользователей
        
    Returns:
        Dict[str, int]: Словарь соответствия telegram_id -> user_id
    """
    # Получаем всех пользователей из Redis
    user_keys = await redis_client.keys("user:*")
    user_mapping = {}
    
    for key in user_keys:
        try:
            user_data = await redis_client.get_json(key)
            telegram_id = int(key.split(":")[1])
            
            # Создаем пользователя в PostgreSQL
            user = await user_repo.get_or_create(
                telegram_id=telegram_id,
                username=user_data.get("username")
            )
            user_mapping[str(telegram_id)] = user.id
            
            logger.info(f"Migrated user {telegram_id}")
        except Exception as e:
            logger.error(f"Error migrating user {key}: {e}")
    
    return user_mapping

async def migrate_states(redis_client, state_repo: StateRepository, user_mapping: Dict[str, int]) -> None:
    """
    Мигрирует состояния из Redis в PostgreSQL.
    
    Args:
        redis_client: Клиент Redis
        state_repo: Репозиторий состояний
        user_mapping: Словарь соответствия telegram_id -> user_id
    """
    state_keys = await redis_client.keys("state:*")
    
    for key in state_keys:
        try:
            state_data = await redis_client.get_json(key)
            telegram_id = key.split(":")[1]
            
            if telegram_id in user_mapping:
                user_id = user_mapping[telegram_id]
                await state_repo.set_state(user_id, state_data)
                logger.info(f"Migrated state for user {telegram_id}")
        except Exception as e:
            logger.error(f"Error migrating state {key}: {e}")

async def migrate_balances(redis_client, balance_repo: BalanceRepository, user_mapping: Dict[str, int]) -> None:
    """
    Мигрирует балансы из Redis в PostgreSQL.
    
    Args:
        redis_client: Клиент Redis
        balance_repo: Репозиторий балансов
        user_mapping: Словарь соответствия telegram_id -> user_id
    """
    balance_keys = await redis_client.keys("balance:*")
    
    for key in balance_keys:
        try:
            balance_data = await redis_client.get_json(key)
            telegram_id = key.split(":")[1]
            
            if telegram_id in user_mapping:
                user_id = user_mapping[telegram_id]
                coins = balance_data.get("coins", INITIAL_BALANCE)
                await balance_repo.add_coins(
                    user_id=user_id,
                    amount=coins,
                    description="Migration from Redis"
                )
                logger.info(f"Migrated balance for user {telegram_id}")
        except Exception as e:
            logger.error(f"Error migrating balance {key}: {e}")

async def main():
    """Основная функция миграции."""
    try:
        # Инициализируем базу данных
        await init_db()
        
        # Подключаемся к Redis
        await redis_client.init()
        
        async with get_session() as session:
            # Создаем репозитории
            user_repo = UserRepository(session)
            state_repo = StateRepository(session)
            balance_repo = BalanceRepository(session)
            
            # Мигрируем данные
            user_mapping = await migrate_users(redis_client, user_repo)
            await migrate_states(redis_client, state_repo, user_mapping)
            await migrate_balances(redis_client, balance_repo, user_mapping)
            
            logger.info("Migration completed successfully")
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await redis_client.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) 