"""
Универсальный сервис кеширования с Redis
Оптимизирует частые запросы к БД и внешним API
"""
import json
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from uuid import UUID

from app.core.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Универсальный сервис кеширования на Redis
    
    Основные области применения:
    1. Пользовательские данные и настройки
    2. Конфигурации и промпты
    3. Статусы FAL AI тренировок
    4. Галереи изображений  
    5. Метаданные аватаров
    """
    
    def __init__(self):
        self.redis = None
        self.memory_fallback = {}  # Fallback для случаев недоступности Redis
        
    async def _get_redis(self):
        """Ленивая инициализация Redis клиента"""
        if self.redis is None:
            try:
                # Ленивый импорт для избежания циклических зависимостей
                from app.core.di import get_redis
                self.redis = await get_redis()
                # Проверяем соединение
                await self.redis.ping()
                logger.debug("✅ Redis соединение установлено")
            except Exception as e:
                logger.warning(f"⚠️ Redis недоступен, использую memory fallback: {e}")
                self.redis = None
        return self.redis
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Получить значение из кеша"""
        try:
            redis = await self._get_redis()
            if redis:
                value = await redis.get(key)
                if value:
                    return json.loads(value)
            
            # Fallback на memory
            return self.memory_fallback.get(key, default)
            
        except Exception as e:
            logger.warning(f"Ошибка чтения кеша {key}: {e}")
            return self.memory_fallback.get(key, default)
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Установить значение в кеш с TTL"""
        try:
            serialized = json.dumps(value, default=str)  # default=str для UUID и datetime
            
            redis = await self._get_redis()
            if redis:
                await redis.setex(key, ttl, serialized)
            
            # Дублируем в memory fallback
            self.memory_fallback[key] = value
            
        except Exception as e:
            logger.warning(f"Ошибка записи кеша {key}: {e}")
            # Сохраняем только в memory
            self.memory_fallback[key] = value
    
    async def delete(self, key: str):
        """Удалить ключ из кеша"""
        try:
            redis = await self._get_redis()
            if redis:
                await redis.delete(key)
            
            self.memory_fallback.pop(key, None)
            
        except Exception as e:
            logger.warning(f"Ошибка удаления кеша {key}: {e}")
            self.memory_fallback.pop(key, None)
    
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        try:
            redis = await self._get_redis()
            if redis:
                return bool(await redis.exists(key))
            
            return key in self.memory_fallback
            
        except Exception as e:
            logger.warning(f"Ошибка проверки кеша {key}: {e}")
            return key in self.memory_fallback
    
    async def expire(self, key: str, ttl: int):
        """Установить TTL для существующего ключа"""
        try:
            redis = await self._get_redis()
            if redis:
                await redis.expire(key, ttl)
                
        except Exception as e:
            logger.warning(f"Ошибка установки TTL {key}: {e}")
    
    # ======================== ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ ========================
    
    async def cache_user(self, telegram_id: Union[str, int], user_data: Dict, ttl: int = 1800):
        """Кешировать данные пользователя (30 минут)"""
        key = f"user:{telegram_id}"
        await self.set(key, user_data, ttl)
    
    async def get_cached_user(self, telegram_id: Union[str, int]) -> Optional[Dict]:
        """Получить пользователя из кеша"""
        key = f"user:{telegram_id}"
        return await self.get(key)
    
    async def cache_user_balance(self, user_id: Union[str, UUID], balance: float, ttl: int = 600):
        """Кешировать баланс пользователя (10 минут)"""
        key = f"balance:{user_id}"
        await self.set(key, {"balance": balance, "updated_at": datetime.utcnow()}, ttl)
    
    async def get_cached_balance(self, user_id: Union[str, UUID]) -> Optional[float]:
        """Получить баланс из кеша"""
        key = f"balance:{user_id}"
        data = await self.get(key)
        return data.get("balance") if data else None
    
    # ======================== АВАТАРЫ И FAL AI ========================
    
    async def cache_fal_status(self, request_id: str, status_data: Dict, ttl: int = 300):
        """Кешировать статус FAL AI запроса (5 минут)"""
        key = f"fal_status:{request_id}"
        await self.set(key, status_data, ttl)
    
    async def get_cached_fal_status(self, request_id: str) -> Optional[Dict]:
        """Получить статус FAL AI из кеша"""
        key = f"fal_status:{request_id}"
        return await self.get(key)
    
    async def cache_avatar_metadata(self, avatar_id: UUID, metadata: Dict, ttl: int = 3600):
        """Кешировать метаданные аватара (1 час)"""
        key = f"avatar_meta:{avatar_id}"
        await self.set(key, metadata, ttl)
    
    async def get_cached_avatar_metadata(self, avatar_id: UUID) -> Optional[Dict]:
        """Получить метаданные аватара из кеша"""
        key = f"avatar_meta:{avatar_id}"
        return await self.get(key)
    
    async def cache_user_avatars_list(self, user_id: Union[str, UUID], avatar_ids: List[str], ttl: int = 1800):
        """Кешировать список аватаров пользователя (30 минут)"""
        key = f"user_avatars:{user_id}"
        await self.set(key, {"avatar_ids": avatar_ids, "cached_at": datetime.utcnow()}, ttl)
    
    async def get_cached_user_avatars_list(self, user_id: Union[str, UUID]) -> Optional[List[str]]:
        """Получить список аватаров пользователя из кеша"""
        key = f"user_avatars:{user_id}"
        data = await self.get(key)
        return data.get("avatar_ids") if data else None
    
    # ======================== ПРОМПТЫ И КОНФИГУРАЦИИ ========================
    
    async def cache_prompt_template(self, template_name: str, prompt_content: str, ttl: int = 86400):
        """Кешировать шаблон промпта (24 часа)"""
        key = f"prompt_template:{template_name}"
        await self.set(key, prompt_content, ttl)
    
    async def get_cached_prompt_template(self, template_name: str) -> Optional[str]:
        """Получить шаблон промпта из кеша"""
        key = f"prompt_template:{template_name}"
        return await self.get(key)
    
    async def cache_keyboard_config(self, keyboard_name: str, config: Dict, ttl: int = 43200):
        """Кешировать конфигурацию клавиатуры (12 часов)"""
        key = f"keyboard:{keyboard_name}"
        await self.set(key, config, ttl)
    
    async def get_cached_keyboard_config(self, keyboard_name: str) -> Optional[Dict]:
        """Получить конфигурацию клавиатуры из кеша"""
        key = f"keyboard:{keyboard_name}"
        return await self.get(key)
    
    # ======================== ТРАНСКРИПТЫ И АУДИО ========================
    
    async def cache_transcript_metadata(self, transcript_id: UUID, metadata: Dict, ttl: int = 7200):
        """Кешировать метаданные транскрипта (2 часа)"""
        key = f"transcript_meta:{transcript_id}"
        await self.set(key, metadata, ttl)
    
    async def get_cached_transcript_metadata(self, transcript_id: UUID) -> Optional[Dict]:
        """Получить метаданные транскрипта из кеша"""
        key = f"transcript_meta:{transcript_id}"
        return await self.get(key)
    
    async def cache_user_transcripts_count(self, user_id: Union[str, UUID], count: int, ttl: int = 1800):
        """Кешировать количество транскриптов пользователя (30 минут)"""
        key = f"user_transcripts_count:{user_id}"
        await self.set(key, {"count": count, "cached_at": datetime.utcnow()}, ttl)
    
    async def get_cached_user_transcripts_count(self, user_id: Union[str, UUID]) -> Optional[int]:
        """Получить количество транскриптов пользователя из кеша"""
        key = f"user_transcripts_count:{user_id}"
        data = await self.get(key)
        return data.get("count") if data else None
    
    # ======================== ИЗОБРАЖЕНИЯ И ГАЛЕРЕЯ ========================
    
    async def cache_user_images_metadata(self, user_id: Union[str, UUID], images_data: List[Dict], ttl: int = 3600):
        """Кешировать метаданные изображений пользователя (1 час)"""
        key = f"user_images_meta:{user_id}"
        await self.set(key, {"images": images_data, "cached_at": datetime.utcnow()}, ttl)
    
    async def get_cached_user_images_metadata(self, user_id: Union[str, UUID]) -> Optional[List[Dict]]:
        """Получить метаданные изображений пользователя из кеша"""
        key = f"user_images_meta:{user_id}"
        data = await self.get(key)
        return data.get("images") if data else None
    
    async def cache_filtered_images(self, user_id: Union[str, UUID], filters_key: str, image_ids: List[str], ttl: int = 1800):
        """Кешировать результаты фильтрации изображений (30 минут)"""
        key = f"filtered_images:{user_id}:{filters_key}"
        await self.set(key, {"image_ids": image_ids, "cached_at": datetime.utcnow()}, ttl)
    
    async def get_cached_filtered_images(self, user_id: Union[str, UUID], filters_key: str) -> Optional[List[str]]:
        """Получить отфильтрованные изображения из кеша"""
        key = f"filtered_images:{user_id}:{filters_key}"
        data = await self.get(key)
        return data.get("image_ids") if data else None
    
    # ======================== СИСТЕМНЫЕ КЕШИ ========================
    
    async def cache_api_response(self, api_name: str, endpoint: str, params_hash: str, response: Dict, ttl: int = 1800):
        """Кешировать ответ внешнего API (30 минут)"""
        key = f"api_response:{api_name}:{endpoint}:{params_hash}"
        await self.set(key, response, ttl)
    
    async def get_cached_api_response(self, api_name: str, endpoint: str, params_hash: str) -> Optional[Dict]:
        """Получить ответ API из кеша"""
        key = f"api_response:{api_name}:{endpoint}:{params_hash}"
        return await self.get(key)
    
    async def cache_database_query_result(self, query_hash: str, result: Any, ttl: int = 600):
        """Кешировать результат запроса к БД (10 минут)"""
        key = f"db_query:{query_hash}"
        await self.set(key, result, ttl)
    
    async def get_cached_database_query_result(self, query_hash: str) -> Any:
        """Получить результат запроса к БД из кеша"""
        key = f"db_query:{query_hash}"
        return await self.get(key)
    
    # ======================== СЛУЖЕБНЫЕ МЕТОДЫ ========================
    
    async def flush_user_cache(self, user_id: Union[str, UUID]):
        """Очистить весь кеш пользователя"""
        patterns = [
            f"user:{user_id}",
            f"balance:{user_id}",
            f"user_avatars:{user_id}", 
            f"user_transcripts_count:{user_id}",
            f"user_images_meta:{user_id}",
            f"filtered_images:{user_id}:*"
        ]
        
        for pattern in patterns:
            if "*" in pattern:
                # Для паттернов с * нужно найти все ключи
                try:
                    redis = await self._get_redis()
                    if redis:
                        keys = await redis.keys(pattern)
                        if keys:
                            await redis.delete(*keys)
                except Exception as e:
                    logger.warning(f"Ошибка очистки кеша по паттерну {pattern}: {e}")
            else:
                await self.delete(pattern)
    
    async def get_cache_stats(self) -> Dict:
        """Получить статистику использования кеша"""
        try:
            redis = await self._get_redis()
            if redis:
                info = await redis.info("memory")
                return {
                    "redis_available": True,
                    "used_memory": info.get("used_memory_human", "Unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "memory_fallback_keys": len(self.memory_fallback)
                }
            else:
                return {
                    "redis_available": False,
                    "memory_fallback_keys": len(self.memory_fallback)
                }
        except Exception as e:
            logger.warning(f"Ошибка получения статистики кеша: {e}")
            return {
                "redis_available": False,
                "error": str(e),
                "memory_fallback_keys": len(self.memory_fallback)
            }


# Глобальный экземпляр сервиса кеширования
cache_service = CacheService() 