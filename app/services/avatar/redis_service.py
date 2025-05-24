"""
Redis сервис для системы аватаров
Адаптировано из archive/aisha_v1/frontend_bot/services/photo_buffer.py
"""
import base64
import json
import uuid
from typing import Dict, List, Optional, Any
from uuid import UUID
import redis.asyncio as redis

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# TTL политики для различных типов данных
REDIS_TTL = {
    "photo_buffer": 300,        # 5 минут - буфер фото
    "avatar_lock": 600,         # 10 минут - блокировки операций  
    "avatar_status": 3600,      # 1 час - статусы обучения
    "training_progress": 1800,  # 30 минут - прогресс обучения
    "avatar_cache": 300,        # 5 минут - кэш данных аватаров
    "avatar_draft": 1800,       # 30 минут - черновики создания
    "webhook_cache": 600        # 10 минут - кэш webhook данных
}

class AvatarRedisService:
    """
    Redis сервис для системы аватаров
    
    Функциональность:
    - Буферизация фотографий при загрузке
    - Блокировки для защиты от race conditions
    - Кэширование статусов обучения
    - Управление черновиками аватаров
    """
    
    def __init__(self):
        self.logger = logger
        self._redis: Optional[redis.Redis] = None
    
    async def get_redis(self) -> redis.Redis:
        """Получает подключение к Redis"""
        if self._redis is None:
            self._redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                ssl=settings.REDIS_SSL,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                max_connections=settings.REDIS_POOL_SIZE,
                decode_responses=False  # Для работы с binary данными
            )
        return self._redis
    
    async def close(self):
        """Закрывает подключение к Redis"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    # ==================== БУФЕРИЗАЦИЯ ФОТОГРАФИЙ ====================
    
    def _get_photo_buffer_key(self, user_id: int) -> str:
        """Генерирует ключ для буфера фотографий пользователя"""
        return f"photo_buffer:{user_id}"
    
    def _get_photo_buffer_meta_key(self, user_id: int) -> str:
        """Генерирует ключ для метаданных буфера фотографий"""
        return f"photo_buffer:{user_id}:meta"
    
    async def buffer_photo(
        self, 
        user_id: int, 
        photo_bytes: bytes, 
        photo_meta: Dict[str, Any]
    ) -> bool:
        """
        Добавляет фото в буфер пользователя (адаптировано из архива)
        
        Args:
            user_id: ID пользователя
            photo_bytes: Байты фотографии
            photo_meta: Метаданные фото (file_id, width, height, etc.)
            
        Returns:
            bool: Успешность операции
        """
        try:
            redis_client = await self.get_redis()
            buffer_key = self._get_photo_buffer_key(user_id)
            meta_key = self._get_photo_buffer_meta_key(user_id)
            
            # Подготавливаем данные (base64 encoding как в архивной версии)
            photo_data = {
                "photo": base64.b64encode(photo_bytes).decode(),
                "meta": photo_meta,
                "timestamp": photo_meta.get("timestamp")
            }
            
            # Добавляем в буфер (LPUSH для FIFO порядка)
            await redis_client.lpush(buffer_key, json.dumps(photo_data))
            
            # Обновляем метаданные буфера
            buffer_info = {
                "count": await redis_client.llen(buffer_key),
                "last_updated": photo_meta.get("timestamp"),
                "user_id": user_id
            }
            await redis_client.hset(meta_key, mapping=buffer_info)
            
            # Устанавливаем TTL
            await redis_client.expire(buffer_key, REDIS_TTL["photo_buffer"])
            await redis_client.expire(meta_key, REDIS_TTL["photo_buffer"])
            
            logger.info(f"Фото добавлено в буфер пользователя {user_id}, размер буфера: {buffer_info['count']}")
            return True
            
        except Exception as e:
            logger.exception(f"Ошибка буферизации фото для пользователя {user_id}: {e}")
            return False
    
    async def get_buffered_photos(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Получает все фото из буфера пользователя (адаптировано из архива)
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Dict]: Список фотографий с декодированными байтами
        """
        try:
            redis_client = await self.get_redis()
            buffer_key = self._get_photo_buffer_key(user_id)
            
            photos = []
            while True:
                # RPOP для FIFO порядка (добавляли через LPUSH)
                data = await redis_client.rpop(buffer_key)
                if not data:
                    break
                    
                # Декодируем данные
                photo_obj = json.loads(data)
                photo_obj["photo"] = base64.b64decode(photo_obj["photo"])
                photos.append(photo_obj)
            
            logger.info(f"Получено {len(photos)} фото из буфера пользователя {user_id}")
            return photos
            
        except Exception as e:
            logger.exception(f"Ошибка получения буфера фото для пользователя {user_id}: {e}")
            return []
    
    async def get_buffer_info(self, user_id: int) -> Dict[str, Any]:
        """
        Получает информацию о буфере фотографий пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict: Информация о буфере (количество, последнее обновление)
        """
        try:
            redis_client = await self.get_redis()
            buffer_key = self._get_photo_buffer_key(user_id)
            meta_key = self._get_photo_buffer_meta_key(user_id)
            
            # Актуальное количество фото
            count = await redis_client.llen(buffer_key)
            
            # Метаданные из хеша
            meta = await redis_client.hgetall(meta_key)
            
            return {
                "count": count,
                "last_updated": meta.get(b"last_updated", b"").decode() if meta else None,
                "user_id": int(meta.get(b"user_id", 0)) if meta else user_id,
                "has_photos": count > 0
            }
            
        except Exception as e:
            logger.exception(f"Ошибка получения информации о буфере для пользователя {user_id}: {e}")
            return {"count": 0, "has_photos": False, "user_id": user_id}
    
    async def clear_photo_buffer(self, user_id: int) -> bool:
        """
        Очищает буфер фотографий пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: Успешность операции
        """
        try:
            redis_client = await self.get_redis()
            buffer_key = self._get_photo_buffer_key(user_id)
            meta_key = self._get_photo_buffer_meta_key(user_id)
            
            # Удаляем буфер и метаданные
            deleted_count = await redis_client.delete(buffer_key, meta_key)
            
            logger.info(f"Очищен буфер фотографий пользователя {user_id}, удалено ключей: {deleted_count}")
            return deleted_count > 0
            
        except Exception as e:
            logger.exception(f"Ошибка очистки буфера фото для пользователя {user_id}: {e}")
            return False
    
    # ==================== БЛОКИРОВКИ ====================
    
    async def acquire_avatar_lock(self, user_id: int, operation: str = "create") -> Optional[str]:
        """
        Приобретает блокировку для операций с аватаром
        
        Args:
            user_id: ID пользователя
            operation: Тип операции (create, training, etc.)
            
        Returns:
            Optional[str]: Токен блокировки или None
        """
        try:
            redis_client = await self.get_redis()
            lock_key = f"avatar_lock:{user_id}:{operation}"
            
            # Генерируем уникальный токен
            token = str(uuid.uuid4())
            
            # Пытаемся установить блокировку
            if await redis_client.set(lock_key, token, ex=REDIS_TTL["avatar_lock"], nx=True):
                logger.info(f"Блокировка установлена: {lock_key}, токен: {token}")
                return token
            
            logger.warning(f"Не удалось установить блокировку: {lock_key}")
            return None
            
        except Exception as e:
            logger.exception(f"Ошибка установки блокировки для пользователя {user_id}: {e}")
            return None
    
    async def release_avatar_lock(self, user_id: int, token: str, operation: str = "create") -> bool:
        """
        Освобождает блокировку операции с аватаром
        
        Args:
            user_id: ID пользователя
            token: Токен блокировки
            operation: Тип операции
            
        Returns:
            bool: Успешность освобождения
        """
        try:
            redis_client = await self.get_redis()
            lock_key = f"avatar_lock:{user_id}:{operation}"
            
            # Проверяем, что блокировка принадлежит нам
            current_token = await redis_client.get(lock_key)
            if current_token and current_token.decode() == token:
                await redis_client.delete(lock_key)
                logger.info(f"Блокировка освобождена: {lock_key}")
                return True
            
            logger.warning(f"Неверный токен для блокировки: {lock_key}")
            return False
            
        except Exception as e:
            logger.exception(f"Ошибка освобождения блокировки для пользователя {user_id}: {e}")
            return False
    
    # ==================== КЭШИРОВАНИЕ СТАТУСОВ ====================
    
    async def set_avatar_status(self, avatar_id: UUID, status_data: Dict[str, Any]) -> bool:
        """
        Кэширует статус аватара в Redis
        
        Args:
            avatar_id: ID аватара
            status_data: Данные статуса
            
        Returns:
            bool: Успешность операции
        """
        try:
            redis_client = await self.get_redis()
            status_key = f"avatar_status:{avatar_id}"
            
            await redis_client.hset(status_key, mapping=status_data)
            await redis_client.expire(status_key, REDIS_TTL["avatar_status"])
            
            logger.debug(f"Статус аватара {avatar_id} сохранен в кэш")
            return True
            
        except Exception as e:
            logger.exception(f"Ошибка кэширования статуса аватара {avatar_id}: {e}")
            return False
    
    async def get_avatar_status(self, avatar_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Получает закэшированный статус аватара
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            Optional[Dict]: Данные статуса или None
        """
        try:
            redis_client = await self.get_redis()
            status_key = f"avatar_status:{avatar_id}"
            
            status_data = await redis_client.hgetall(status_key)
            if not status_data:
                return None
            
            # Декодируем байты в строки
            decoded_status = {
                k.decode(): v.decode() if isinstance(v, bytes) else v 
                for k, v in status_data.items()
            }
            
            return decoded_status
            
        except Exception as e:
            logger.exception(f"Ошибка получения статуса аватара {avatar_id}: {e}")
            return None
    
    # ==================== УПРАВЛЕНИЕ ЧЕРНОВИКАМИ ====================
    
    async def save_avatar_draft(self, user_id: int, draft_data: Dict[str, Any]) -> bool:
        """
        Сохраняет черновик аватара в Redis
        
        Args:
            user_id: ID пользователя
            draft_data: Данные черновика
            
        Returns:
            bool: Успешность операции
        """
        try:
            redis_client = await self.get_redis()
            draft_key = f"avatar_draft:{user_id}"
            
            await redis_client.hset(draft_key, mapping=draft_data)
            await redis_client.expire(draft_key, REDIS_TTL["avatar_draft"])
            
            logger.debug(f"Черновик аватара пользователя {user_id} сохранен")
            return True
            
        except Exception as e:
            logger.exception(f"Ошибка сохранения черновика аватара для пользователя {user_id}: {e}")
            return False
    
    async def get_avatar_draft(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает черновик аватара пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[Dict]: Данные черновика или None
        """
        try:
            redis_client = await self.get_redis()
            draft_key = f"avatar_draft:{user_id}"
            
            draft_data = await redis_client.hgetall(draft_key)
            if not draft_data:
                return None
            
            # Декодируем байты в строки
            decoded_draft = {
                k.decode(): v.decode() if isinstance(v, bytes) else v 
                for k, v in draft_data.items()
            }
            
            return decoded_draft
            
        except Exception as e:
            logger.exception(f"Ошибка получения черновика аватара для пользователя {user_id}: {e}")
            return None
    
    async def clear_avatar_draft(self, user_id: int) -> bool:
        """
        Очищает черновик аватара пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: Успешность операции
        """
        try:
            redis_client = await self.get_redis()
            draft_key = f"avatar_draft:{user_id}"
            
            deleted = await redis_client.delete(draft_key)
            
            if deleted:
                logger.info(f"Черновик аватара пользователя {user_id} очищен")
            
            return deleted > 0
            
        except Exception as e:
            logger.exception(f"Ошибка очистки черновика аватара для пользователя {user_id}: {e}")
            return False
    
    # ==================== ПРОГРЕСС ОБУЧЕНИЯ ====================
    
    async def set_training_progress(self, avatar_id: UUID, progress: int) -> bool:
        """
        Устанавливает прогресс обучения аватара
        
        Args:
            avatar_id: ID аватара
            progress: Прогресс от 0 до 100
            
        Returns:
            bool: Успешность операции
        """
        try:
            redis_client = await self.get_redis()
            progress_key = f"training_progress:{avatar_id}"
            
            await redis_client.set(progress_key, str(progress))
            await redis_client.expire(progress_key, REDIS_TTL["training_progress"])
            
            logger.debug(f"Прогресс обучения аватара {avatar_id}: {progress}%")
            return True
            
        except Exception as e:
            logger.exception(f"Ошибка установки прогресса обучения аватара {avatar_id}: {e}")
            return False
    
    async def get_training_progress(self, avatar_id: UUID) -> Optional[int]:
        """
        Получает прогресс обучения аватара
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            Optional[int]: Прогресс от 0 до 100 или None
        """
        try:
            redis_client = await self.get_redis()
            progress_key = f"training_progress:{avatar_id}"
            
            progress_str = await redis_client.get(progress_key)
            if progress_str is None:
                return None
            
            return int(progress_str.decode() if isinstance(progress_str, bytes) else progress_str)
            
        except Exception as e:
            logger.exception(f"Ошибка получения прогресса обучения аватара {avatar_id}: {e}")
            return None
    
    # ==================== ОБЩИЕ МЕТОДЫ ОЧИСТКИ ====================
    
    async def clear_user_data(self, user_id: int) -> bool:
        """
        Полностью очищает все данные пользователя из Redis
        Используется при отмене создания аватара или сбросе сессии
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: Успешность операции
        """
        try:
            redis_client = await self.get_redis()
            
            # Паттерны ключей для удаления
            patterns_to_clear = [
                f"photo_buffer:{user_id}*",      # Буфер фотографий
                f"avatar_lock:{user_id}*",       # Блокировки операций
                f"avatar_draft:{user_id}*",      # Черновики аватаров
                f"avatar_cache:{user_id}*",      # Кэшированные данные
            ]
            
            total_deleted = 0
            
            for pattern in patterns_to_clear:
                # Получаем ключи по паттерну
                keys = await redis_client.keys(pattern)
                if keys:
                    # Удаляем ключи
                    deleted_count = await redis_client.delete(*keys)
                    total_deleted += deleted_count
                    logger.debug(f"Удалено {deleted_count} ключей по паттерну {pattern}")
            
            logger.info(f"Очищены все данные пользователя {user_id} из Redis, удалено ключей: {total_deleted}")
            return True
            
        except Exception as e:
            logger.exception(f"Ошибка очистки данных пользователя {user_id} из Redis: {e}")
            return False 