"""
Менеджер кеша сессий галереи
Управление состоянием пользовательских сессий просмотра
"""
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.core.logger import get_logger
from app.core.di import get_redis

logger = get_logger(__name__)


class SessionCacheManager:
    """Менеджер кеша сессий галереи"""
    
    def __init__(self):
        self.redis = None
        self._session_ttl = 1800  # 30 минут
        self._session_prefix = "gallery:session:"
    
    async def _get_redis(self):
        """Получает Redis клиент"""
        if not self.redis:
            self.redis = await get_redis()
        return self.redis
    
    async def save_session_state(self, user_id: UUID, session_data: Dict[str, Any]) -> bool:
        """
        Сохраняет состояние сессии пользователя
        
        Args:
            user_id: ID пользователя
            session_data: Данные сессии
            
        Returns:
            bool: True если успешно сохранено
        """
        try:
            redis = await self._get_redis()
            session_key = f"{self._session_prefix}{user_id}"
            
            # Добавляем метаданные
            session_data.update({
                "last_updated": datetime.now().isoformat(),
                "user_id": str(user_id)
            })
            
            # Сохраняем в Redis
            await redis.hset(session_key, mapping={
                "data": str(session_data),
                "timestamp": datetime.now().timestamp()
            })
            
            # Устанавливаем TTL
            await redis.expire(session_key, self._session_ttl)
            
            logger.info(f"[Session Cache] Сохранено состояние сессии для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.exception(f"[Session Cache] Ошибка сохранения сессии пользователя {user_id}: {e}")
            return False
    
    async def get_session_state(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Получает состояние сессии пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[Dict]: Данные сессии или None
        """
        try:
            redis = await self._get_redis()
            session_key = f"{self._session_prefix}{user_id}"
            
            # Проверяем существование сессии
            if not await redis.exists(session_key):
                return None
            
            # Получаем данные
            session_data = await redis.hget(session_key, "data")
            if not session_data:
                return None
            
            # Парсим данные (упрощенно)
            session_info = eval(session_data)
            
            logger.info(f"[Session Cache] Получено состояние сессии для пользователя {user_id}")
            return session_info
            
        except Exception as e:
            logger.exception(f"[Session Cache] Ошибка получения сессии пользователя {user_id}: {e}")
            return None
    
    async def clear_session(self, user_id: UUID) -> bool:
        """
        Очищает сессию пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если успешно очищено
        """
        try:
            redis = await self._get_redis()
            session_key = f"{self._session_prefix}{user_id}"
            
            deleted = await redis.delete(session_key)
            
            if deleted:
                logger.info(f"[Session Cache] Очищена сессия пользователя {user_id}")
            
            return bool(deleted)
            
        except Exception as e:
            logger.exception(f"[Session Cache] Ошибка очистки сессии пользователя {user_id}: {e}")
            return False 