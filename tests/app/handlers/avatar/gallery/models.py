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
        """Сохраняет данные фотогалереи в Redis с полным объектом аватара"""
        try:
            redis_client = await self.redis_service.get_redis()
            key = self._get_photos_key(user_id, avatar_id)
            
            # 🚀 ОПТИМИЗАЦИЯ: Сериализуем полный объект аватара с фотографиями
            avatar_data = {
                "id": str(avatar.id),
                "name": avatar.name,
                "user_id": avatar.user_id,
                "gender": avatar.gender,
                "avatar_type": avatar.avatar_type,
                "training_type": avatar.training_type,
                "status": avatar.status,
                "is_main": avatar.is_main,
                "created_at": avatar.created_at.isoformat() if avatar.created_at else None,
                "updated_at": avatar.updated_at.isoformat() if avatar.updated_at else None,
                "photos": []
            }
            
            # Сериализуем фотографии
            if avatar.photos:
                for photo in avatar.photos:
                    photo_data = {
                        "id": str(photo.id),
                        "avatar_id": str(photo.avatar_id),
                        "minio_key": photo.minio_key,
                        "upload_order": photo.upload_order,
                        "width": photo.width,
                        "height": photo.height,
                        "file_size": photo.file_size,
                        "created_at": photo.created_at.isoformat() if photo.created_at else None
                    }
                    avatar_data["photos"].append(photo_data)
            
            cache_data = {
                "avatar": avatar_data,
                "current_photo_idx": current_photo_idx,
                "photos_count": len(avatar.photos) if avatar.photos else 0
            }
            
            # Увеличиваем TTL для полного объекта (10 минут)
            await redis_client.setex(
                key, 
                600,  # 10 минут для полного объекта 
                json.dumps(cache_data)
            )
            
            logger.debug(f"Кэш фотогалереи с полным объектом сохранен для пользователя {user_id}, аватар {avatar_id}")
            
        except Exception as e:
            logger.warning(f"Ошибка сохранения кэша фотогалереи: {e}")
    
    async def get_photos(self, user_id: int, avatar_id: UUID) -> Optional[Dict[str, Any]]:
        """Получает данные фотогалереи из Redis с восстановлением объекта аватара"""
        try:
            redis_client = await self.redis_service.get_redis()
            key = self._get_photos_key(user_id, avatar_id)
            
            data = await redis_client.get(key)
            if data:
                cache_data = json.loads(data)
                
                # 🚀 ОПТИМИЗАЦИЯ: Восстанавливаем объект аватара из кеша
                if "avatar" in cache_data:
                    from app.database.models import Avatar, AvatarPhoto
                    from datetime import datetime
                    from uuid import UUID
                    
                    avatar_data = cache_data["avatar"]
                    
                    # Создаем объект Avatar
                    avatar = Avatar()
                    avatar.id = UUID(avatar_data["id"])
                    avatar.name = avatar_data["name"]
                    avatar.user_id = avatar_data["user_id"]
                    avatar.gender = avatar_data["gender"]
                    avatar.avatar_type = avatar_data["avatar_type"]
                    avatar.training_type = avatar_data["training_type"]
                    avatar.status = avatar_data["status"]
                    avatar.is_main = avatar_data["is_main"]
                    avatar.created_at = datetime.fromisoformat(avatar_data["created_at"]) if avatar_data["created_at"] else None
                    avatar.updated_at = datetime.fromisoformat(avatar_data["updated_at"]) if avatar_data["updated_at"] else None
                    
                    # Восстанавливаем фотографии
                    avatar.photos = []
                    for photo_data in avatar_data["photos"]:
                        photo = AvatarPhoto()
                        photo.id = UUID(photo_data["id"])
                        photo.avatar_id = UUID(photo_data["avatar_id"])
                        photo.minio_key = photo_data["minio_key"]
                        photo.upload_order = photo_data["upload_order"]
                        photo.width = photo_data["width"]
                        photo.height = photo_data["height"]
                        photo.file_size = photo_data["file_size"]
                        photo.created_at = datetime.fromisoformat(photo_data["created_at"]) if photo_data["created_at"] else None
                        avatar.photos.append(photo)
                    
                    # Обновляем кеш с восстановленным объектом
                    cache_data["avatar"] = avatar
                    
                logger.debug(f"Кэш фотогалереи с полным объектом найден для пользователя {user_id}, аватар {avatar_id}")
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
        """Очищает весь кеш пользователя из Redis"""
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
    
    async def invalidate_photo_cache(self, user_id: int, avatar_id: UUID):
        """
        Инвалидирует кеш фотогалереи при изменении фотографий
        Используется при добавлении/удалении фото
        """
        try:
            redis_client = await self.redis_service.get_redis()
            key = self._get_photos_key(user_id, avatar_id)
            await redis_client.delete(key)
            
            logger.debug(f"Кеш фотогалереи инвалидирован для аватара {avatar_id}")
            
        except Exception as e:
            logger.warning(f"Ошибка инвалидации кеша фотогалереи: {e}")
    
    async def extend_cache_ttl(self, user_id: int, avatar_id: UUID, ttl: int = 600):
        """
        Продлевает TTL кеша при активном использовании
        """
        try:
            redis_client = await self.redis_service.get_redis()
            key = self._get_photos_key(user_id, avatar_id)
            
            # Продлеваем TTL если ключ существует
            exists = await redis_client.exists(key)
            if exists:
                await redis_client.expire(key, ttl)
                logger.debug(f"TTL кеша продлен до {ttl}s для аватара {avatar_id}")
                
        except Exception as e:
            logger.warning(f"Ошибка продления TTL кеша: {e}")

# Глобальный экземпляр кэша
gallery_cache = GalleryCache() 