"""
Redis Storage для aiogram сессий
Поддержка горизонтального масштабирования бота
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from redis.asyncio import Redis
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType

logger = logging.getLogger(__name__)


class RedisStorage(BaseStorage):
    """
    Redis Storage для aiogram с поддержкой кластера
    Хранит состояния пользователей в Redis для синхронизации между экземплярами бота
    """
    
    def __init__(
        self,
        redis: Redis,
        key_builder: Optional[str] = None,
        state_ttl: Optional[int] = None,
        data_ttl: Optional[int] = None,
    ):
        self.redis = redis
        self.key_builder = key_builder or "fsm:{chat}:{user}"
        self.state_ttl = state_ttl or int(os.getenv("AIOGRAM_SESSION_TTL", 3600))  # 1 час по умолчанию
        self.data_ttl = data_ttl or self.state_ttl

    def _make_key(self, key: StorageKey) -> str:
        """Создание ключа для Redis"""
        return self.key_builder.format(
            bot=key.bot_id,
            chat=key.chat_id,
            user=key.user_id,
            thread=key.thread_id or 0,
        )

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        """Установка состояния пользователя"""
        redis_key = self._make_key(key)
        
        if state is None:
            await self.redis.hdel(redis_key, "state")
        else:
            state_name = state.state if hasattr(state, 'state') else str(state)
            await self.redis.hset(redis_key, "state", state_name)
            if self.state_ttl:
                await self.redis.expire(redis_key, self.state_ttl)
        
        logger.debug(f"🔄 Установлено состояние {state} для ключа {redis_key}")

    async def get_state(self, key: StorageKey) -> Optional[str]:
        """Получение состояния пользователя"""
        redis_key = self._make_key(key)
        state = await self.redis.hget(redis_key, "state")
        
        if state:
            state = state.decode() if isinstance(state, bytes) else state
            logger.debug(f"📥 Получено состояние {state} для ключа {redis_key}")
        
        return state

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        """Установка данных пользователя"""
        redis_key = self._make_key(key)
        
        if not data:
            await self.redis.hdel(redis_key, "data")
        else:
            json_data = json.dumps(data, ensure_ascii=False)
            await self.redis.hset(redis_key, "data", json_data)
            if self.data_ttl:
                await self.redis.expire(redis_key, self.data_ttl)
        
        logger.debug(f"💾 Сохранены данные для ключа {redis_key}: {len(data)} элементов")

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        """Получение данных пользователя"""
        redis_key = self._make_key(key)
        data = await self.redis.hget(redis_key, "data")
        
        if data:
            try:
                if isinstance(data, bytes):
                    data = data.decode()
                result = json.loads(data)
                logger.debug(f"📤 Получены данные для ключа {redis_key}: {len(result)} элементов")
                return result
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"❌ Ошибка декодирования данных для {redis_key}: {e}")
                return {}
        
        return {}

    async def update_data(self, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление данных пользователя"""
        current_data = await self.get_data(key)
        current_data.update(data)
        await self.set_data(key, current_data)
        return current_data

    async def close(self) -> None:
        """Закрытие соединения с Redis"""
        await self.redis.close()
        logger.info("🔐 Redis Storage закрыт")

    async def wait_closed(self) -> None:
        """Ожидание закрытия соединения"""
        await self.redis.wait_closed()


async def create_redis_storage() -> RedisStorage:
    """
    Создание Redis Storage для aiogram
    Использует переменные окружения для подключения
    """
    
    # Параметры подключения к Redis
    redis_host = os.getenv("AIOGRAM_SESSION_REDIS_HOST", os.getenv("REDIS_HOST", "localhost"))
    redis_port = int(os.getenv("AIOGRAM_SESSION_REDIS_PORT", os.getenv("REDIS_PORT", 6379)))
    redis_db = int(os.getenv("AIOGRAM_SESSION_REDIS_DB", os.getenv("REDIS_DB", 0)))
    redis_password = os.getenv("AIOGRAM_SESSION_REDIS_PASSWORD", os.getenv("REDIS_PASSWORD"))
    
    # Создание Redis клиента
    redis_client = Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        password=redis_password,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    
    # Проверка подключения
    try:
        await redis_client.ping()
        logger.info(f"✅ Redis Storage подключен: {redis_host}:{redis_port}/{redis_db}")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения Redis Storage: {e}")
        raise
    
    # TTL для сессий
    session_ttl = int(os.getenv("AIOGRAM_SESSION_TTL", 3600))
    
    # Создание storage
    storage = RedisStorage(
        redis=redis_client,
        key_builder="aisha:fsm:{chat}:{user}",
        state_ttl=session_ttl,
        data_ttl=session_ttl,
    )
    
    logger.info(f"🎯 Redis Storage создан с TTL {session_ttl} секунд")
    return storage


# Экземпляр для использования в приложении  
_redis_storage: Optional[RedisStorage] = None


async def get_redis_storage() -> RedisStorage:
    """Получение экземпляра Redis Storage (Singleton)"""
    global _redis_storage
    
    if _redis_storage is None:
        _redis_storage = await create_redis_storage()
    
    return _redis_storage


async def close_redis_storage() -> None:
    """Закрытие Redis Storage"""
    global _redis_storage
    
    if _redis_storage:
        await _redis_storage.close()
        await _redis_storage.wait_closed()
        _redis_storage = None
        logger.info("🔒 Redis Storage закрыт и очищен") 