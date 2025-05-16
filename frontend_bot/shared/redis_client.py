"""
Асинхронный Redis клиент для управления состояниями FSM, кэширования и очередей задач.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError

from frontend_bot.config import (
    REDIS_DB,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
)

logger = logging.getLogger(__name__)

class RedisClient:
    """Асинхронный Redis клиент с поддержкой пула соединений."""
    
    def __init__(self):
        """Инициализация Redis клиента."""
        self._pool = ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
            max_connections=10,
            retry_on_timeout=True,
            health_check_interval=30
        )
        self._client: Optional[Redis] = None
        
    async def init(self) -> None:
        """Инициализация соединения с Redis."""
        if not self._client:
            try:
                self._client = Redis(connection_pool=self._pool)
                await self._client.ping()
                logger.info("Redis connection established")
            except RedisError as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._client = None
                raise
                
    async def close(self) -> None:
        """Закрытие соединения с Redis."""
        if self._client:
            try:
                await self._client.close()
                logger.info("Redis connection closed")
            except RedisError as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._client = None
            
    async def _ensure_connection(self) -> None:
        """Проверка и восстановление соединения при необходимости."""
        if not self._client:
            await self.init()
        try:
            await self._client.ping()
        except RedisError:
            self._client = None
            await self.init()
            
    async def get(self, key: str) -> Optional[str]:
        """Получение значения по ключу."""
        await self._ensure_connection()
        try:
            return await self._client.get(key)
        except RedisError as e:
            logger.error(f"Error getting key {key}: {e}")
            raise
        
    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None
    ) -> bool:
        """Установка значения по ключу с опциональным TTL."""
        await self._ensure_connection()
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return await self._client.set(key, value, ex=expire)
        except RedisError as e:
            logger.error(f"Error setting key {key}: {e}")
            raise
        
    async def delete(self, key: str) -> bool:
        """Удаление ключа."""
        await self._ensure_connection()
        try:
            return bool(await self._client.delete(key))
        except RedisError as e:
            logger.error(f"Error deleting key {key}: {e}")
            raise
        
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа."""
        await self._ensure_connection()
        try:
            return bool(await self._client.exists(key))
        except RedisError as e:
            logger.error(f"Error checking existence of key {key}: {e}")
            raise
        
    async def ttl(self, key: str) -> int:
        """Получение TTL ключа в секундах."""
        await self._ensure_connection()
        try:
            return await self._client.ttl(key)
        except RedisError as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            raise
        
    async def incr(self, key: str) -> int:
        """Инкремент значения."""
        await self._ensure_connection()
        try:
            return await self._client.incr(key)
        except RedisError as e:
            logger.error(f"Error incrementing key {key}: {e}")
            raise
        
    async def decr(self, key: str) -> int:
        """Декремент значения."""
        await self._ensure_connection()
        try:
            return await self._client.decr(key)
        except RedisError as e:
            logger.error(f"Error decrementing key {key}: {e}")
            raise
        
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Получение значения из хэш-таблицы."""
        await self._ensure_connection()
        try:
            return await self._client.hget(name, key)
        except RedisError as e:
            logger.error(f"Error getting hash field {key} from {name}: {e}")
            raise
        
    async def hset(
        self,
        name: str,
        key: str,
        value: str
    ) -> int:
        """Установка значения в хэш-таблицу."""
        await self._ensure_connection()
        try:
            return await self._client.hset(name, key, value)
        except RedisError as e:
            logger.error(f"Error setting hash field {key} in {name}: {e}")
            raise
        
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Получение всех значений из хэш-таблицы."""
        await self._ensure_connection()
        try:
            return await self._client.hgetall(name)
        except RedisError as e:
            logger.error(f"Error getting all hash fields from {name}: {e}")
            raise
        
    async def hdel(self, name: str, *keys: str) -> int:
        """Удаление ключей из хэш-таблицы."""
        await self._ensure_connection()
        try:
            return await self._client.hdel(name, *keys)
        except RedisError as e:
            logger.error(f"Error deleting hash fields from {name}: {e}")
            raise
        
    async def publish(self, channel: str, message: str) -> int:
        """Публикация сообщения в канал."""
        await self._ensure_connection()
        try:
            return await self._client.publish(channel, message)
        except RedisError as e:
            logger.error(f"Error publishing to channel {channel}: {e}")
            raise
        
    async def subscribe(self, *channels: str):
        """Подписка на каналы."""
        await self._ensure_connection()
        try:
            pubsub = self._client.pubsub()
            await pubsub.subscribe(*channels)
            return pubsub
        except RedisError as e:
            logger.error(f"Error subscribing to channels {channels}: {e}")
            raise
        
    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Сохранение JSON-данных."""
        try:
            return await self.set(
                key,
                json.dumps(value),
                expire=expire
            )
        except (TypeError, ValueError) as e:
            logger.error(f"Error serializing JSON for key {key}: {e}")
            raise
        
    async def get_json(self, key: str) -> Optional[Any]:
        """Получение JSON-данных."""
        try:
            data = await self.get(key)
            return json.loads(data) if data else None
        except (TypeError, ValueError) as e:
            logger.error(f"Error deserializing JSON for key {key}: {e}")
            raise

    async def delete_pattern(self, pattern: str) -> int:
        """Удаляет все ключи, соответствующие шаблону."""
        await self._ensure_connection()
        try:
            keys = await self._client.keys(pattern)
            if keys:
                return await self._client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Error deleting keys by pattern {pattern}: {e}")
            raise

    # Методы для работы со списками
    async def rpush(self, name: str, *values: str) -> int:
        """Добавление элементов в конец списка."""
        await self._ensure_connection()
        try:
            return await self._client.rpush(name, *values)
        except RedisError as e:
            logger.error(f"Error pushing to list {name}: {e}")
            raise

    async def lpush(self, name: str, *values: str) -> int:
        """Добавление элементов в начало списка."""
        await self._ensure_connection()
        try:
            return await self._client.lpush(name, *values)
        except RedisError as e:
            logger.error(f"Error pushing to list {name}: {e}")
            raise

    async def rpop(self, name: str) -> Optional[str]:
        """Извлечение элемента с конца списка."""
        await self._ensure_connection()
        try:
            return await self._client.rpop(name)
        except RedisError as e:
            logger.error(f"Error popping from list {name}: {e}")
            raise

    async def lpop(self, name: str) -> Optional[str]:
        """Извлечение элемента с начала списка."""
        await self._ensure_connection()
        try:
            return await self._client.lpop(name)
        except RedisError as e:
            logger.error(f"Error popping from list {name}: {e}")
            raise

    async def lrange(self, name: str, start: int, end: int) -> List[str]:
        """Получение диапазона элементов из списка."""
        await self._ensure_connection()
        try:
            return await self._client.lrange(name, start, end)
        except RedisError as e:
            logger.error(f"Error getting range from list {name}: {e}")
            raise

    async def llen(self, name: str) -> int:
        """Получение длины списка."""
        await self._ensure_connection()
        try:
            return await self._client.llen(name)
        except RedisError as e:
            logger.error(f"Error getting length of list {name}: {e}")
            raise

    async def lrem(self, name: str, count: int, value: str) -> int:
        """Удаление элементов из списка."""
        await self._ensure_connection()
        try:
            return await self._client.lrem(name, count, value)
        except RedisError as e:
            logger.error(f"Error removing from list {name}: {e}")
            raise

    async def rpoplpush(self, src: str, dst: str) -> Optional[str]:
        """Атомарное перемещение элемента из одного списка в другой."""
        await self._ensure_connection()
        try:
            return await self._client.rpoplpush(src, dst)
        except RedisError as e:
            logger.error(f"Error moving element from {src} to {dst}: {e}")
            raise

# Глобальный экземпляр Redis клиента
redis_client = RedisClient() 