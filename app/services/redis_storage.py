"""
Redis хранилище для временных данных платной транскрипции
"""
import pickle
import base64
from typing import Any, Dict, Optional, Tuple
from datetime import timedelta

from app.core.logger import get_logger
from app.core.di import get_redis_client

logger = get_logger(__name__)


class AudioDataRedisStorage:
    """Redis хранилище для временных аудио данных"""
    
    def __init__(self):
        self.key_prefix = "aisha:paid_transcription:audio:"
        self.default_ttl = 3600  # 1 час
    
    async def store_audio_data(
        self, 
        user_id: int, 
        audio_data: bytes, 
        file_info: Dict[str, Any], 
        quote: Dict[str, Any],
        ttl_seconds: int = None
    ) -> bool:
        """
        Сохраняет данные аудио во временном хранилище Redis
        
        Args:
            user_id: ID пользователя
            audio_data: Аудио данные
            file_info: Информация о файле
            quote: Расценки на транскрибацию
            ttl_seconds: Время жизни в секундах
            
        Returns:
            bool: True если успешно сохранено
        """
        try:
            redis_client = await get_redis_client()
            
            # Формируем ключ
            key = f"{self.key_prefix}{user_id}"
            
            # Формируем данные для сохранения
            data = {
                'audio_data': base64.b64encode(audio_data).decode('utf-8'),
                'file_info': file_info,
                'quote': quote
            }
            
            # Сериализуем данные
            serialized_data = pickle.dumps(data)
            
            # Сохраняем в Redis с TTL
            ttl = ttl_seconds or self.default_ttl
            await redis_client.setex(key, ttl, serialized_data)
            
            logger.info(f"Аудио данные сохранены в Redis для пользователя {user_id}, TTL: {ttl}s")
            return True
            
        except Exception as e:
            logger.exception(f"Ошибка сохранения аудио данных в Redis: {e}")
            return False
    
    async def retrieve_audio_data(self, user_id: int) -> Tuple[Optional[bytes], Optional[Dict], Optional[Dict]]:
        """
        Извлекает данные аудио из Redis
        
        Args:
            user_id: ID пользователя
            
        Returns:
            tuple: (audio_data, file_info, quote) или (None, None, None)
        """
        try:
            redis_client = await get_redis_client()
            
            # Формируем ключ
            key = f"{self.key_prefix}{user_id}"
            
            # Получаем данные из Redis
            serialized_data = await redis_client.get(key)
            
            if not serialized_data:
                logger.info(f"Аудио данные не найдены в Redis для пользователя {user_id}")
                return None, None, None
            
            # Десериализуем данные
            data = pickle.loads(serialized_data)
            
            # Декодируем аудио данные
            audio_data = base64.b64decode(data['audio_data'])
            file_info = data['file_info']
            quote = data['quote']
            
            logger.info(f"Аудио данные извлечены из Redis для пользователя {user_id}")
            return audio_data, file_info, quote
            
        except Exception as e:
            logger.exception(f"Ошибка извлечения аудио данных из Redis: {e}")
            return None, None, None
    
    async def clear_audio_data(self, user_id: int) -> bool:
        """
        Удаляет данные аудио из Redis
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если успешно удалено
        """
        try:
            redis_client = await get_redis_client()
            
            # Формируем ключ
            key = f"{self.key_prefix}{user_id}"
            
            # Удаляем из Redis
            deleted_count = await redis_client.delete(key)
            
            if deleted_count > 0:
                logger.info(f"Аудио данные удалены из Redis для пользователя {user_id}")
            else:
                logger.info(f"Аудио данные не найдены для удаления для пользователя {user_id}")
            
            return deleted_count > 0
            
        except Exception as e:
            logger.exception(f"Ошибка удаления аудио данных из Redis: {e}")
            return False
    
    async def get_ttl(self, user_id: int) -> Optional[int]:
        """
        Получает оставшееся время жизни аудио данных
        
        Args:
            user_id: ID пользователя
            
        Returns:
            int: Оставшееся время в секундах или None
        """
        try:
            redis_client = await get_redis_client()
            
            # Формируем ключ
            key = f"{self.key_prefix}{user_id}"
            
            # Получаем TTL
            ttl = await redis_client.ttl(key)
            
            if ttl == -2:  # Ключ не существует
                return None
            elif ttl == -1:  # Ключ существует без TTL
                return -1
            else:
                return ttl
                
        except Exception as e:
            logger.exception(f"Ошибка получения TTL аудио данных: {e}")
            return None 