"""
Ультрабыстрый кеш галереи изображений
Оптимизированное кеширование для быстрого отображения
"""
import asyncio
import json
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime, timedelta

from app.core.logger import get_logger
from app.core.di import get_redis

logger = get_logger(__name__)


class UltraFastGalleryCache:
    """Ультрабыстрый кеш для галереи изображений"""
    
    def __init__(self):
        self.redis = None
        self._cache_ttl = 3600  # 1 час
        self._user_cache_prefix = "gallery:user:"
        self._generation_cache_prefix = "gallery:gen:"
        self._session_prefix = "gallery:session:"
        self._state_prefix = "gallery:state:"
        self._image_prefix = "gallery:image:"
    
    async def _get_redis(self):
        """Получает Redis клиент"""
        if not self.redis:
            self.redis = await get_redis()
        return self.redis
    
    async def cache_user_gallery(self, user_id: UUID, generations: List[Dict[str, Any]]) -> bool:
        """
        Кеширует галерею пользователя
        
        Args:
            user_id: ID пользователя
            generations: Список генераций
            
        Returns:
            bool: True если успешно закешировано
        """
        try:
            redis = await self._get_redis()
            cache_key = f"{self._user_cache_prefix}{user_id}"
            
            # Сериализуем данные
            cache_data = {
                "generations": generations,
                "cached_at": datetime.now().isoformat(),
                "count": len(generations)
            }
            
            # Сохраняем в Redis
            await redis.hset(cache_key, mapping={
                "data": str(cache_data),
                "timestamp": datetime.now().timestamp()
            })
            
            # Устанавливаем TTL
            await redis.expire(cache_key, self._cache_ttl)
            
            logger.info(f"[Gallery Cache] Закешировано {len(generations)} генераций для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка кеширования галереи пользователя {user_id}: {e}")
            return False
    
    async def get_cached_user_gallery(self, user_id: UUID) -> Optional[List[Dict[str, Any]]]:
        """
        Получает закешированную галерею пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[List]: Список генераций или None
        """
        try:
            redis = await self._get_redis()
            cache_key = f"{self._user_cache_prefix}{user_id}"
            
            # Проверяем существование кеша
            if not await redis.exists(cache_key):
                return None
            
            # Получаем данные
            cached_data = await redis.hget(cache_key, "data")
            if not cached_data:
                return None
            
            # Парсим данные (в реальности лучше использовать JSON)
            cache_info = eval(cached_data)  # Упрощенно для примера
            generations = cache_info.get("generations", [])
            
            logger.info(f"[Gallery Cache] Получено {len(generations)} генераций из кеша для пользователя {user_id}")
            return generations
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка получения кеша галереи пользователя {user_id}: {e}")
            return None
    
    async def invalidate_user_cache(self, user_id: UUID) -> bool:
        """
        Инвалидирует кеш пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если успешно инвалидировано
        """
        try:
            redis = await self._get_redis()
            cache_key = f"{self._user_cache_prefix}{user_id}"
            
            deleted = await redis.delete(cache_key)
            
            if deleted:
                logger.info(f"[Gallery Cache] Инвалидирован кеш галереи пользователя {user_id}")
            
            return bool(deleted)
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка инвалидации кеша пользователя {user_id}: {e}")
            return False
    
    async def cache_generation_details(self, generation_id: UUID, details: Dict[str, Any]) -> bool:
        """
        Кеширует детали генерации
        
        Args:
            generation_id: ID генерации
            details: Детали генерации
            
        Returns:
            bool: True если успешно закешировано
        """
        try:
            redis = await self._get_redis()
            cache_key = f"{self._generation_cache_prefix}{generation_id}"
            
            # Сохраняем детали
            await redis.hset(cache_key, mapping={
                "details": str(details),
                "timestamp": datetime.now().timestamp()
            })
            
            # Устанавливаем TTL
            await redis.expire(cache_key, self._cache_ttl)
            
            return True
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка кеширования деталей генерации {generation_id}: {e}")
            return False
    
    async def set_session_data(self, user_id: UUID, session_data: Dict[str, Any]) -> bool:
        """
        Сохраняет сессионные данные пользователя
        
        Args:
            user_id: ID пользователя
            session_data: Данные сессии
            
        Returns:
            bool: True если успешно сохранено
        """
        try:
            redis = await self._get_redis()
            session_key = f"{self._session_prefix}{user_id}"
            
            # Сериализуем данные в JSON
            json_data = json.dumps(session_data, default=str)
            
            # Сохраняем в Redis
            await redis.setex(session_key, self._cache_ttl, json_data)
            
            logger.debug(f"[Gallery Cache] Сохранены сессионные данные для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка сохранения сессионных данных пользователя {user_id}: {e}")
            return False
    
    async def cache_user_data(self, user_id: UUID, user_data: Any) -> bool:
        """
        Кеширует данные пользователя
        
        Args:
            user_id: ID пользователя
            user_data: Данные пользователя
            
        Returns:
            bool: True если успешно закешировано
        """
        try:
            redis = await self._get_redis()
            cache_key = f"{self._user_cache_prefix}data:{user_id}"
            
            # Сериализуем пользователя
            user_dict = {
                "id": str(user_data.id),
                "telegram_id": user_data.telegram_id,
                "username": user_data.username,
                "first_name": user_data.first_name,
                "cached_at": datetime.now().isoformat()
            }
            
            json_data = json.dumps(user_dict)
            await redis.setex(cache_key, self._cache_ttl, json_data)
            
            logger.debug(f"[Gallery Cache] Закешированы данные пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка кеширования данных пользователя {user_id}: {e}")
            return False
    
    async def get_user_gallery_state(self, user_id: UUID) -> Optional[int]:
        """
        Получает сохраненное состояние галереи пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[int]: Индекс текущего изображения или None
        """
        try:
            redis = await self._get_redis()
            state_key = f"{self._state_prefix}{user_id}"
            
            state_data = await redis.get(state_key)
            if state_data:
                return int(state_data)
            return None
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка получения состояния галереи пользователя {user_id}: {e}")
            return None
    
    async def set_user_gallery_state(self, user_id: UUID, img_index: int) -> bool:
        """
        Сохраняет состояние галереи пользователя
        
        Args:
            user_id: ID пользователя
            img_index: Индекс текущего изображения
            
        Returns:
            bool: True если успешно сохранено
        """
        try:
            redis = await self._get_redis()
            state_key = f"{self._state_prefix}{user_id}"
            
            await redis.setex(state_key, self._cache_ttl, str(img_index))
            
            logger.debug(f"[Gallery Cache] Сохранено состояние галереи пользователя {user_id}, индекс: {img_index}")
            return True
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка сохранения состояния галереи пользователя {user_id}: {e}")
            return False
    
    async def get_user_images(self, user_id: UUID) -> Optional[List]:
        """
        Получает закешированные изображения пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[List]: Список изображений или None
        """
        try:
            redis = await self._get_redis()
            cache_key = f"{self._user_cache_prefix}images:{user_id}"
            
            cached_data = await redis.get(cache_key)
            if cached_data:
                # В реальности здесь должна быть более сложная десериализация
                # объектов ImageGeneration, но для простоты возвращаем None
                # чтобы всегда делать свежий запрос к БД
                pass
            
            return None
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка получения изображений пользователя {user_id}: {e}")
            return None
    
    async def set_user_images(self, user_id: UUID, images: List) -> bool:
        """
        Кеширует изображения пользователя
        
        Args:
            user_id: ID пользователя
            images: Список изображений
            
        Returns:
            bool: True если успешно закешировано
        """
        try:
            redis = await self._get_redis()
            cache_key = f"{self._user_cache_prefix}images:{user_id}"
            
            # Упрощенное кеширование - просто сохраняем количество
            await redis.setex(cache_key, 900, str(len(images)))  # 15 минут
            
            logger.debug(f"[Gallery Cache] Закешировано {len(images)} изображений для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка кеширования изображений пользователя {user_id}: {e}")
            return False
    
    async def get_cached_image(self, image_url: str) -> Optional[bytes]:
        """
        Получает закешированное изображение
        
        Args:
            image_url: URL изображения
            
        Returns:
            Optional[bytes]: Данные изображения или None
        """
        try:
            redis = await self._get_redis()
            
            # Создаем ключ кеша из URL (безопасно)
            import hashlib
            url_hash = hashlib.md5(image_url.encode()).hexdigest()
            cache_key = f"{self._generation_cache_prefix}image:{url_hash}"
            
            # Получаем данные изображения
            image_data = await redis.get(cache_key)
            if image_data:
                logger.debug(f"[Gallery Cache] Изображение найдено в кеше: {len(image_data)} байт")
                return image_data
            
            return None
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка получения изображения из кеша: {e}")
            return None
    
    async def set_cached_image(self, image_url: str, image_data: bytes) -> bool:
        """
        Кеширует изображение
        
        Args:
            image_url: URL изображения
            image_data: Данные изображения
            
        Returns:
            bool: True если успешно закешировано
        """
        try:
            redis = await self._get_redis()
            
            # Создаем ключ кеша из URL (безопасно)
            import hashlib
            url_hash = hashlib.md5(image_url.encode()).hexdigest()
            cache_key = f"{self._generation_cache_prefix}image:{url_hash}"
            
            # Кешируем на 2 часа (MinIO URLs обычно живут больше)
            await redis.setex(cache_key, 7200, image_data)
            
            logger.debug(f"[Gallery Cache] Изображение закешировано: {len(image_data)} байт")
            return True
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка кеширования изображения: {e}")
            return False
    
    async def clear_all_cache(self, user_id: UUID) -> bool:
        """
        Очищает весь кеш пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если успешно очищено
        """
        try:
            redis = await self._get_redis()
            
            # Собираем все ключи пользователя
            patterns = [
                f"{self._user_cache_prefix}{user_id}*",
                f"{self._session_prefix}{user_id}",
                f"{self._state_prefix}{user_id}",
                f"{self._generation_cache_prefix}{user_id}*"
            ]
            
            deleted_count = 0
            for pattern in patterns:
                async for key in redis.scan_iter(match=pattern):
                    await redis.delete(key)
                    deleted_count += 1
            
            logger.info(f"[Gallery Cache] Очищено {deleted_count} ключей кеша для пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.exception(f"[Gallery Cache] Ошибка очистки кеша пользователя {user_id}: {e}")
            return False


# Глобальный экземпляр кеша
ultra_gallery_cache = UltraFastGalleryCache() 