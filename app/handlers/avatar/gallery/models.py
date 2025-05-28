"""
Модели данных для галереи аватаров
"""
from typing import Dict, List, Any, Optional
from uuid import UUID
import json
import logging

from app.services.avatar.redis_service import AvatarRedisService

logger = logging.getLogger(__name__)

class GalleryCache:
    """Redis-based кэш галереи для отслеживания состояния"""
    
    def __init__(self):
        self.redis_service = AvatarRedisService()
        self._ttl = 300  # 5 минут TTL для кэша галереи
    
    def _get_avatars_key(self, user_id: int) -> str:
        """Генерирует ключ для кэша аватаров пользователя"""
        return f"gallery_cache:avatars:{user_id}"
    
    def _get_photos_key(self, user_id: int, avatar_id: UUID) -> str:
        """Генерирует ключ для кэша фотогалереи"""
        return f"gallery_cache:photos:{user_id}:{avatar_id}"
    
    async def set_avatars(self, user_id: int, avatars: List, current_idx: int = 0):
        """Сохраняет список аватаров пользователя в Redis"""
        try:
            redis_client = await self.redis_service.get_redis()
            key = self._get_avatars_key(user_id)
            
            # Сериализуем данные (только ID аватаров для экономии памяти)
            cache_data = {
                "avatar_ids": [str(avatar.id) for avatar in avatars],
                "current_idx": current_idx,
                "total_count": len(avatars)
            }
            
            await redis_client.setex(
                key, 
                self._ttl, 
                json.dumps(cache_data)
            )
            
            logger.debug(f"Кэш аватаров сохранен для пользователя {user_id}: {len(avatars)} аватаров")
            
        except Exception as e:
            logger.warning(f"Ошибка сохранения кэша аватаров для пользователя {user_id}: {e}")
    
    async def get_avatars(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает данные аватаров пользователя из Redis"""
        try:
            redis_client = await self.redis_service.get_redis()
            key = self._get_avatars_key(user_id)
            
            data = await redis_client.get(key)
            if data:
                cache_data = json.loads(data)
                logger.debug(f"Кэш аватаров найден для пользователя {user_id}")
                return cache_data
            
            return None
            
        except Exception as e:
            logger.warning(f"Ошибка получения кэша аватаров для пользователя {user_id}: {e}")
            return None
    
    async def update_current_idx(self, user_id: int, idx: int):
        """Обновляет текущий индекс аватара в Redis"""
        try:
            cache_data = await self.get_avatars(user_id)
            if cache_data:
                cache_data["current_idx"] = idx
                
                redis_client = await self.redis_service.get_redis()
                key = self._get_avatars_key(user_id)
                
                await redis_client.setex(
                    key, 
                    self._ttl, 
                    json.dumps(cache_data)
                )
                
                logger.debug(f"Индекс аватара обновлен для пользователя {user_id}: {idx}")
                
        except Exception as e:
            logger.warning(f"Ошибка обновления индекса для пользователя {user_id}: {e}")
    
    async def set_photos(self, user_id: int, avatar_id: UUID, avatar, current_photo_idx: int = 0):
        """Сохраняет данные фотогалереи в Redis"""
        try:
            redis_client = await self.redis_service.get_redis()
            key = self._get_photos_key(user_id, avatar_id)
            
            # Сериализуем только необходимые данные
            cache_data = {
                "avatar_id": str(avatar_id),
                "avatar_name": avatar.name,
                "photos_count": len(avatar.photos) if avatar.photos else 0,
                "current_photo_idx": current_photo_idx
            }
            
            await redis_client.setex(
                key, 
                self._ttl, 
                json.dumps(cache_data)
            )
            
            logger.debug(f"Кэш фотогалереи сохранен для пользователя {user_id}, аватар {avatar_id}")
            
        except Exception as e:
            logger.warning(f"Ошибка сохранения кэша фотогалереи: {e}")
    
    async def get_photos(self, user_id: int, avatar_id: UUID) -> Optional[Dict[str, Any]]:
        """Получает данные фотогалереи из Redis"""
        try:
            redis_client = await self.redis_service.get_redis()
            key = self._get_photos_key(user_id, avatar_id)
            
            data = await redis_client.get(key)
            if data:
                cache_data = json.loads(data)
                logger.debug(f"Кэш фотогалереи найден для пользователя {user_id}, аватар {avatar_id}")
                return cache_data
            
            return None
            
        except Exception as e:
            logger.warning(f"Ошибка получения кэша фотогалереи: {e}")
            return None
    
    async def update_photo_idx(self, user_id: int, avatar_id: UUID, idx: int):
        """Обновляет текущий индекс фото в Redis"""
        try:
            cache_data = await self.get_photos(user_id, avatar_id)
            if cache_data:
                cache_data["current_photo_idx"] = idx
                
                redis_client = await self.redis_service.get_redis()
                key = self._get_photos_key(user_id, avatar_id)
                
                await redis_client.setex(
                    key, 
                    self._ttl, 
                    json.dumps(cache_data)
                )
                
                logger.debug(f"Индекс фото обновлен: пользователь {user_id}, аватар {avatar_id}, индекс {idx}")
                
        except Exception as e:
            logger.warning(f"Ошибка обновления индекса фото: {e}")
    
    async def clear_photos(self, user_id: int, avatar_id: UUID):
        """Очищает кэш фотогалереи из Redis"""
        try:
            redis_client = await self.redis_service.get_redis()
            key = self._get_photos_key(user_id, avatar_id)
            
            await redis_client.delete(key)
            logger.debug(f"Кэш фотогалереи очищен для пользователя {user_id}, аватар {avatar_id}")
            
        except Exception as e:
            logger.warning(f"Ошибка очистки кэша фотогалереи: {e}")
    
    async def clear_user(self, user_id: int):
        """Очищает весь кэш пользователя из Redis"""
        try:
            redis_client = await self.redis_service.get_redis()
            
            # Очищаем кэш аватаров
            avatars_key = self._get_avatars_key(user_id)
            await redis_client.delete(avatars_key)
            
            # Очищаем все кэши фотогалерей пользователя (по паттерну)
            photos_pattern = f"gallery_cache:photos:{user_id}:*"
            keys = await redis_client.keys(photos_pattern)
            if keys:
                await redis_client.delete(*keys)
            
            logger.debug(f"Весь кэш галереи очищен для пользователя {user_id}")
            
        except Exception as e:
            logger.warning(f"Ошибка очистки кэша пользователя {user_id}: {e}")

# Глобальный экземпляр кэша
gallery_cache = GalleryCache() 