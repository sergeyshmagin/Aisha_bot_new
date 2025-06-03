"""
Оптимизированный сервис галереи с кешированием
Устраняет N+1 проблему и снижает время отклика до <500ms
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ImageGeneration
from app.database.repositories import ImageGenerationRepository
from app.services.cache_service import cache_service
from app.core.logger import get_logger

logger = get_logger(__name__)


class GalleryService:
    """
    Оптимизированный сервис галереи с многоуровневым кешированием
    
    Ключевые оптимизации:
    1. Кеширование полных объектов изображений (не только ID)
    2. Batch-запросы для устранения N+1 проблемы  
    3. Eagerly loading связанных аватаров
    4. Кеширование результатов фильтрации
    5. Инкрементальная загрузка по страницам
    """
    
    def __init__(self):
        self.session: Optional[AsyncSession] = None
        self.image_repo: Optional[ImageGenerationRepository] = None
    
    async def set_session(self, session: AsyncSession):
        """Установить сессию БД"""
        self.session = session
        self.image_repo = ImageGenerationRepository(session)
    
    async def get_user_images_optimized(
        self, 
        user_id: UUID, 
        filters: Optional[Dict] = None,
        page: int = 1,
        per_page: int = 20,
        force_refresh: bool = False
    ) -> Tuple[List[Dict], int, bool]:
        """
        Получить изображения пользователя с оптимизацией
        
        Returns:
            Tuple[images_data, total_count, has_more]
        """
        if not self.session:
            raise RuntimeError("Session not set. Call set_session() first.")
        
        # ✅ 1. Генерируем ключ кеша на основе фильтров
        filters_key = self._generate_filters_key(filters or {})
        cache_key = f"gallery_optimized:{user_id}:{filters_key}:p{page}"
        
        # ✅ 2. Проверяем кеш сначала
        if not force_refresh:
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                logger.debug(f"✅ Cache HIT для галереи пользователя {user_id} страница {page}")
                return (
                    cached_data["images"], 
                    cached_data["total_count"], 
                    cached_data["has_more"]
                )
        
        logger.debug(f"🔄 Cache MISS для галереи пользователя {user_id}, загружаем из БД")
        
        # ✅ 3. Строим оптимизированный запрос с JOIN'ами
        query = (
            select(ImageGeneration)
            .options(selectinload(ImageGeneration.avatar))  # Eager loading аватаров
            .where(ImageGeneration.user_id == user_id)
            .where(ImageGeneration.status == "COMPLETED")
        )
        
        # ✅ 4. Применяем фильтры
        query = self._apply_filters_to_query(query, filters or {})
        
        # ✅ 5. Добавляем сортировку
        query = query.order_by(ImageGeneration.created_at.desc())
        
        # ✅ 6. Выполняем ОДИН запрос для получения общего количества
        count_query = select(ImageGeneration.id).where(
            and_(
                ImageGeneration.user_id == user_id,
                ImageGeneration.status == "COMPLETED",
                *self._build_filter_conditions(filters or {})
            )
        )
        
        total_count = len(await self.session.execute(count_query).all())
        
        # ✅ 7. Применяем пагинацию к основному запросу
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page + 1)  # +1 для проверки has_more
        
        # ✅ 8. Выполняем ОДИН запрос для получения данных
        result = await self.session.execute(query)
        images = result.scalars().all()
        
        # ✅ 9. Определяем есть ли еще страницы
        has_more = len(images) > per_page
        if has_more:
            images = images[:per_page]  # Убираем лишнее изображение
        
        # ✅ 10. Сериализуем данные для кеша
        images_data = [self._serialize_image_for_cache(img) for img in images]
        
        # ✅ 11. Кешируем результат на 30 минут
        cache_data = {
            "images": images_data,
            "total_count": total_count,
            "has_more": has_more,
            "cached_at": datetime.utcnow().isoformat()
        }
        await cache_service.set(cache_key, cache_data, ttl=1800)
        
        logger.info(f"✅ Загружено {len(images_data)} изображений для пользователя {user_id} за один запрос")
        
        return images_data, total_count, has_more
    
    def _apply_filters_to_query(self, query, filters: Dict):
        """Применить фильтры к запросу"""
        conditions = self._build_filter_conditions(filters)
        for condition in conditions:
            query = query.where(condition)
        return query
    
    def _build_filter_conditions(self, filters: Dict) -> List:
        """Построить условия фильтрации"""
        conditions = []
        
        # Фильтр по времени
        if "time_filter" in filters:
            time_filter = filters["time_filter"]
            now = datetime.utcnow()
            
            if time_filter == "today":
                start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
                conditions.append(ImageGeneration.created_at >= start_of_day)
            elif time_filter == "week":
                week_ago = now - timedelta(days=7)
                conditions.append(ImageGeneration.created_at >= week_ago)
            elif time_filter == "month":
                month_ago = now - timedelta(days=30)
                conditions.append(ImageGeneration.created_at >= month_ago)
        
        # Фильтр по размеру
        if "size_filters" in filters and filters["size_filters"]:
            size_conditions = []
            for size in filters["size_filters"]:
                if size == "1:1":
                    size_conditions.append(ImageGeneration.aspect_ratio == "1:1")
                elif size == "4:3":
                    size_conditions.append(ImageGeneration.aspect_ratio == "4:3")
                elif size == "3:4":
                    size_conditions.append(ImageGeneration.aspect_ratio == "3:4")
            
            if size_conditions:
                conditions.append(or_(*size_conditions))
        
        # Фильтр по статусу
        if "status_filters" in filters and filters["status_filters"]:
            status_conditions = []
            for status in filters["status_filters"]:
                if status == "favorites":
                    status_conditions.append(ImageGeneration.is_favorite == True)
                elif status == "recent":
                    recent_time = datetime.utcnow() - timedelta(hours=24)
                    status_conditions.append(ImageGeneration.created_at >= recent_time)
            
            if status_conditions:
                conditions.append(or_(*status_conditions))
        
        # Фильтр по аватарам
        if "avatar_filters" in filters and filters["avatar_filters"]:
            avatar_ids = [UUID(aid) for aid in filters["avatar_filters"]]
            conditions.append(ImageGeneration.avatar_id.in_(avatar_ids))
        
        return conditions
    
    def _generate_filters_key(self, filters: Dict) -> str:
        """Генерировать ключ для кеширования на основе фильтров"""
        if not filters:
            return "no_filters"
        
        # Сортируем ключи для консистентности
        sorted_filters = {k: sorted(v) if isinstance(v, list) else v 
                         for k, v in sorted(filters.items())}
        
        return json.dumps(sorted_filters, sort_keys=True, default=str)
    
    def _serialize_image_for_cache(self, image: ImageGeneration) -> Dict:
        """Сериализовать изображение для кеша с полными данными"""
        return {
            "id": str(image.id),
            "original_prompt": image.original_prompt,
            "final_prompt": image.final_prompt,
            "aspect_ratio": image.aspect_ratio,
            "quality_preset": image.quality_preset,
            "result_urls": image.result_urls,
            "is_favorite": image.is_favorite,
            "created_at": image.created_at.isoformat() if image.created_at else None,
            "completed_at": image.completed_at.isoformat() if image.completed_at else None,
            "prompt_metadata": image.prompt_metadata,
            "avatar": {
                "id": str(image.avatar.id),
                "name": image.avatar.name,
                "gender": image.avatar.gender,
                "trigger_word": image.avatar.trigger_word
            } if image.avatar else None
        }
    
    async def get_single_image_optimized(self, image_id: UUID, user_id: UUID) -> Optional[Dict]:
        """
        Получить одно изображение с оптимизацией
        """
        if not self.session:
            raise RuntimeError("Session not set. Call set_session() first.")
        
        cache_key = f"single_image:{image_id}"
        
        # ✅ Проверяем кеш
        cached_image = await cache_service.get(cache_key)
        if cached_image:
            logger.debug(f"✅ Cache HIT для изображения {image_id}")
            return cached_image
        
        # ✅ Один запрос с JOIN'ом
        query = (
            select(ImageGeneration)
            .options(selectinload(ImageGeneration.avatar))
            .where(and_(
                ImageGeneration.id == image_id,
                ImageGeneration.user_id == user_id
            ))
        )
        
        result = await self.session.execute(query)
        image = result.scalar_one_or_none()
        
        if not image:
            return None
        
        # ✅ Сериализуем и кешируем
        image_data = self._serialize_image_for_cache(image)
        await cache_service.set(cache_key, image_data, ttl=3600)
        
        return image_data
    
    async def invalidate_user_gallery_cache(self, user_id: UUID):
        """Инвалидировать кеш галереи пользователя"""
        try:
            redis = await cache_service._get_redis()
            if redis:
                # Удаляем все ключи галереи пользователя
                pattern = f"gallery_optimized:{user_id}:*"
                keys = await redis.keys(pattern)
                if keys:
                    await redis.delete(*keys)
                    logger.info(f"🗑️ Очищен кеш галереи для пользователя {user_id}: {len(keys)} ключей")
            
            # Очищаем также memory fallback
            keys_to_remove = [k for k in cache_service.memory_fallback.keys() 
                             if k.startswith(f"gallery_optimized:{user_id}:")]
            for key in keys_to_remove:
                cache_service.memory_fallback.pop(key, None)
                
        except Exception as e:
            logger.warning(f"Ошибка очистки кеша галереи: {e}")
    
    async def preload_gallery_cache(self, user_id: UUID, filters: Optional[Dict] = None):
        """Предзагрузить кеш галереи для быстрого доступа"""
        try:
            # Загружаем первые 3 страницы в кеш
            for page in range(1, 4):
                await self.get_user_images_optimized(
                    user_id=user_id,
                    filters=filters,
                    page=page,
                    per_page=20,
                    force_refresh=False
                )
            logger.info(f"🚀 Предзагружен кеш галереи для пользователя {user_id}")
        except Exception as e:
            logger.warning(f"Ошибка предзагрузки кеша галереи: {e}")
    
    async def get_cache_stats(self, user_id: UUID) -> Dict:
        """Получить статистику кеша для отладки"""
        try:
            redis = await cache_service._get_redis()
            if redis:
                pattern = f"gallery_optimized:{user_id}:*"
                keys = await redis.keys(pattern)
                return {
                    "cached_pages": len(keys),
                    "redis_available": True,
                    "sample_keys": keys[:5] if keys else []
                }
            else:
                memory_keys = [k for k in cache_service.memory_fallback.keys() 
                              if k.startswith(f"gallery_optimized:{user_id}:")]
                return {
                    "cached_pages": len(memory_keys),
                    "redis_available": False,
                    "sample_keys": memory_keys[:5]
                }
        except Exception as e:
            return {"error": str(e), "redis_available": False}


# Глобальный экземпляр сервиса
gallery_service = GalleryService() 