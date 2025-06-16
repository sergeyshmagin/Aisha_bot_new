"""
Состояния FSM для обработчиков галереи с Redis хранением
"""
import json
from aiogram.fsm.state import State, StatesGroup
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel

from app.core.logger import get_logger

logger = get_logger(__name__)


class GalleryStates(StatesGroup):
    """Состояния для галереи изображений"""
    viewing = State()
    deleting = State()


class GalleryFilterStates(StatesGroup):
    """Состояния для фильтров галереи"""
    selecting_filters = State()
    waiting_custom_date = State()
    
    
@dataclass
class GalleryData:
    """Класс для хранения данных галереи в кеше"""
    image_ids: List[str]  # ID изображений в галерее
    current_index: int  # Текущий индекс
    total_count: int  # Общее количество изображений
    user_id: str  # ID пользователя
    filters: Dict  # Примененные фильтры
    

@dataclass  
class GalleryFilterData:
    """Класс для хранения данных фильтров"""
    time_filter: Optional[str] = None  # today, week, month
    size_filters: Set[str] = None  # 1:1, 4:3, 3:4
    status_filters: Set[str] = None  # favorites, recent
    avatar_filters: Set[str] = None  # UUID аватаров
    active: bool = False  # Активны ли фильтры
    
    def __post_init__(self):
        # Инициализируем пустые множества если None
        if self.size_filters is None:
            self.size_filters = set()
        if self.status_filters is None:
            self.status_filters = set()
        if self.avatar_filters is None:
            self.avatar_filters = set()
    
    def clear(self):
        """Очищает все фильтры"""
        self.time_filter = None
        self.size_filters.clear()
        self.status_filters.clear()
        self.avatar_filters.clear()
        self.active = False
    
    def has_filters(self) -> bool:
        """Проверяет, есть ли активные фильтры"""
        return bool(
            self.time_filter or 
            self.size_filters or 
            self.status_filters or 
            self.avatar_filters
        )
    
    def get_summary(self) -> str:
        """Возвращает краткое описание активных фильтров"""
        parts = []
        if self.time_filter:
            time_names = {"today": "Сегодня", "week": "Неделя", "month": "Месяц"}
            parts.append(f"Время: {time_names.get(self.time_filter, self.time_filter)}")
        if self.avatar_filters:
            parts.append(f"Аватары: {len(self.avatar_filters)}")
        if self.size_filters:
            parts.append(f"Размеры: {', '.join(self.size_filters)}")
        if self.status_filters:
            status_names = {"favorites": "Избранные", "recent": "Недавние"}
            status_text = [status_names.get(s, s) for s in self.status_filters]
            parts.append(f"Статус: {', '.join(status_text)}")
        
        return " | ".join(parts) if parts else "Без фильтров"


class GalleryStateManager:
    """Менеджер состояний галереи с Redis хранением"""
    
    def __init__(self):
        self._cache_service = None
    
    async def _get_cache_service(self):
        """Ленивый импорт cache_service для избежания циклических зависимостей"""
        if self._cache_service is None:
            from app.services.cache_service import cache_service
            self._cache_service = cache_service
        return self._cache_service
    
    # =============== ФИЛЬТРЫ ПОЛЬЗОВАТЕЛЕЙ ===============
    
    async def get_user_filters(self, user_id: int) -> GalleryFilterData:
        """Получить фильтры пользователя из Redis"""
        try:
            cache_service = await self._get_cache_service()
            key = f"gallery_filters:{user_id}"
            
            data = await cache_service.get(key)
            if data:
                # Восстанавливаем объект из JSON
                filter_data = GalleryFilterData(
                    time_filter=data.get("time_filter"),
                    size_filters=set(data.get("size_filters", [])),
                    status_filters=set(data.get("status_filters", [])),
                    avatar_filters=set(data.get("avatar_filters", [])),
                    active=data.get("active", False)
                )
                logger.debug(f"✅ Фильтры пользователя {user_id} загружены из Redis")
                return filter_data
            
            # Возвращаем пустые фильтры если не найдены
            return GalleryFilterData()
            
        except Exception as e:
            logger.warning(f"Ошибка загрузки фильтров пользователя {user_id}: {e}")
            return GalleryFilterData()
    
    async def set_user_filters(self, user_id: int, filter_data: GalleryFilterData, ttl: int = 3600):
        """Сохранить фильтры пользователя в Redis (1 час TTL)"""
        try:
            cache_service = await self._get_cache_service()
            key = f"gallery_filters:{user_id}"
            
            # Сериализуем в JSON-совместимый формат
            data = {
                "time_filter": filter_data.time_filter,
                "size_filters": list(filter_data.size_filters),
                "status_filters": list(filter_data.status_filters),
                "avatar_filters": list(filter_data.avatar_filters),
                "active": filter_data.active,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await cache_service.set(key, data, ttl)
            logger.debug(f"✅ Фильтры пользователя {user_id} сохранены в Redis")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения фильтров пользователя {user_id}: {e}")
    
    async def clear_user_filters(self, user_id: int):
        """Очистить фильтры пользователя"""
        try:
            cache_service = await self._get_cache_service()
            key = f"gallery_filters:{user_id}"
            await cache_service.delete(key)
            logger.debug(f"🗑️ Фильтры пользователя {user_id} очищены")
            
        except Exception as e:
            logger.warning(f"Ошибка очистки фильтров пользователя {user_id}: {e}")
    
    # =============== ДАННЫЕ ГАЛЕРЕИ ===============
    
    async def get_gallery_data(self, cache_key: str) -> Optional[GalleryData]:
        """Получить данные галереи по ключу кеша"""
        try:
            cache_service = await self._get_cache_service()
            
            data = await cache_service.get(cache_key)
            if data:
                gallery_data = GalleryData(
                    image_ids=data["image_ids"],
                    current_index=data["current_index"], 
                    total_count=data["total_count"],
                    user_id=data["user_id"],
                    filters=data.get("filters", {})
                )
                logger.debug(f"✅ Данные галереи {cache_key} загружены из Redis")
                return gallery_data
            
            return None
            
        except Exception as e:
            logger.warning(f"Ошибка загрузки данных галереи {cache_key}: {e}")
            return None
    
    async def set_gallery_data(self, cache_key: str, gallery_data: GalleryData, ttl: int = 1800):
        """Сохранить данные галереи в Redis (30 минут TTL)"""
        try:
            cache_service = await self._get_cache_service()
            
            data = {
                "image_ids": gallery_data.image_ids,
                "current_index": gallery_data.current_index,
                "total_count": gallery_data.total_count,
                "user_id": gallery_data.user_id,
                "filters": gallery_data.filters,
                "cached_at": datetime.utcnow().isoformat()
            }
            
            await cache_service.set(cache_key, data, ttl)
            logger.debug(f"✅ Данные галереи {cache_key} сохранены в Redis")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения данных галереи {cache_key}: {e}")
    
    async def update_gallery_index(self, cache_key: str, new_index: int):
        """Обновить текущий индекс в данных галереи"""
        try:
            gallery_data = await self.get_gallery_data(cache_key)
            if gallery_data:
                gallery_data.current_index = new_index
                await self.set_gallery_data(cache_key, gallery_data)
                logger.debug(f"✅ Индекс галереи {cache_key} обновлен: {new_index}")
            
        except Exception as e:
            logger.error(f"Ошибка обновления индекса галереи {cache_key}: {e}")
    
    async def delete_gallery_data(self, cache_key: str):
        """Удалить данные галереи"""
        try:
            cache_service = await self._get_cache_service()
            await cache_service.delete(cache_key)
            logger.debug(f"🗑️ Данные галереи {cache_key} удалены")
            
        except Exception as e:
            logger.warning(f"Ошибка удаления данных галереи {cache_key}: {e}")
    
    # =============== СЛУЖЕБНЫЕ МЕТОДЫ ===============
    
    async def cleanup_old_gallery_data(self, user_id: str, keep_recent_hours: int = 24):
        """Очистка старых данных галереи пользователя (автоматическая garbage collection)"""
        try:
            cache_service = await self._get_cache_service()
            
            # Это требует реализации pattern search в cache_service
            # Пока оставляем как заглушку для будущей реализации
            logger.info(f"🧹 Планируется очистка старых данных галереи для пользователя {user_id}")
            
        except Exception as e:
            logger.warning(f"Ошибка очистки старых данных галереи: {e}")
    
    async def get_cache_stats(self) -> Dict:
        """Получить статистику кеша галереи"""
        try:
            cache_service = await self._get_cache_service()
            return await cache_service.get_cache_stats()
        except Exception as e:
            logger.warning(f"Ошибка получения статистики кеша: {e}")
            return {"error": str(e)}


# Глобальный менеджер состояний
gallery_state_manager = GalleryStateManager()

# LEGACY: Удалено. Используйте gallery_state_manager для всех операций с состоянием галереи
# Deprecated переменные удалены в пользу Redis-based решения 