"""
Менеджер состояний пользователей на базе Redis.
"""

import logging
from typing import Optional, Dict, Any

from frontend_bot.shared.redis_client import redis_client
from frontend_bot.config import CACHE_TTL

logger = logging.getLogger(__name__)

class RedisStateManager:
    """Менеджер для работы с состояниями пользователей через Redis."""
    
    def __init__(self):
        """Инициализация менеджера состояний."""
        self._redis = redis_client
        self._ttl = CACHE_TTL
        self._prefix = "state:"
    
    def _get_key(self, user_id: str) -> str:
        """Формирует ключ для Redis."""
        return f"{self._prefix}{user_id}"
    
    async def get_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает состояние пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[Dict[str, Any]]: Состояние пользователя или None
        """
        try:
            state = await self._redis.get_json(self._get_key(user_id))
            return state
        except Exception as e:
            logger.error(f"Error getting state for user {user_id}: {e}")
            return None
    
    async def set_state(self, user_id: str, state: Dict[str, Any]) -> None:
        """
        Устанавливает состояние пользователя.
        
        Args:
            user_id: ID пользователя
            state: Новое состояние
        """
        try:
            await self._redis.set_json(
                self._get_key(user_id),
                state,
                expire=self._ttl
            )
        except Exception as e:
            logger.error(f"Error setting state for user {user_id}: {e}")
            raise
    
    async def clear_state(self, user_id: str) -> None:
        """
        Очищает состояние пользователя.
        
        Args:
            user_id: ID пользователя
        """
        try:
            await self._redis.delete(self._get_key(user_id))
        except Exception as e:
            logger.error(f"Error clearing state for user {user_id}: {e}")
            raise
    
    async def cleanup_state(self, user_id: str) -> None:
        """
        Очищает все данные пользователя.
        
        Args:
            user_id: ID пользователя
        """
        await self.clear_state(user_id)

# Глобальный экземпляр менеджера состояний
state_manager = RedisStateManager() 