"""
Репозиторий для работы с генерацией изображений
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, update, func
from sqlalchemy.orm import selectinload

from app.database.models import ImageGeneration, GenerationStatus
from app.database.repositories.base import BaseRepository
from app.utils.datetime_utils import now_utc


class ImageGenerationRepository(BaseRepository[ImageGeneration]):
    """Репозиторий для работы с генерациями изображений"""
    
    def __init__(self, session):
        super().__init__(ImageGeneration, session)
    
    async def get_user_generations(
        self, 
        user_id: UUID, 
        status: Optional[GenerationStatus] = None,
        generation_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ImageGeneration]:
        """Получить генерации пользователя с возможностью фильтрации по типу"""
        query = (
            select(ImageGeneration)
            .options(selectinload(ImageGeneration.avatar))
            .where(ImageGeneration.user_id == user_id)
        )
        
        if status:
            query = query.where(ImageGeneration.status == status)
        
        if generation_type:
            query = query.where(ImageGeneration.generation_type == generation_type)
        
        query = query.order_by(desc(ImageGeneration.created_at))
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_completed_generations(
        self, 
        user_id: UUID,
        generation_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ImageGeneration]:
        """Получить завершенные генерации пользователя с возможностью фильтрации по типу"""
        return await self.get_user_generations(
            user_id=user_id,
            status=GenerationStatus.COMPLETED,
            generation_type=generation_type,
            limit=limit,
            offset=offset
        )
    
    async def count_user_generations(
        self, 
        user_id: UUID, 
        status: Optional[GenerationStatus] = None
    ) -> int:
        """Подсчитать количество генераций пользователя"""
        query = select(ImageGeneration.id).where(ImageGeneration.user_id == user_id)
        
        if status:
            query = query.where(ImageGeneration.status == status)
        
        result = await self.session.execute(query)
        return len(result.all())
    
    async def get_by_id_with_relations(self, generation_id: UUID) -> Optional[ImageGeneration]:
        """Получить генерацию по ID с загруженными связями"""
        query = (
            select(ImageGeneration)
            .options(
                selectinload(ImageGeneration.avatar),
                selectinload(ImageGeneration.template),
                selectinload(ImageGeneration.user)
            )
            .where(ImageGeneration.id == generation_id)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_status(
        self, 
        generation_id: UUID, 
        status: GenerationStatus,
        result_urls: Optional[List[str]] = None,
        error_message: Optional[str] = None
    ) -> Optional[ImageGeneration]:
        """Обновить статус генерации"""
        generation = await self.get_by_id(generation_id)
        if not generation:
            return None
        
        generation.status = status
        
        if result_urls is not None:
            generation.result_urls = result_urls
        
        if error_message is not None:
            generation.error_message = error_message
        
        if status == GenerationStatus.COMPLETED:
            generation.completed_at = now_utc().replace(tzinfo=None)
        
        await self.session.commit()
        return generation
    
    async def toggle_favorite(self, generation_id: UUID) -> Optional[ImageGeneration]:
        """Переключить статус избранного"""
        generation = await self.get_by_id(generation_id)
        if not generation:
            return None
        
        generation.is_favorite = not generation.is_favorite
        await self.session.commit()
        return generation
    
    # 🆕 Методы для работы с типизацией генераций
    
    async def get_user_avatar_generations(
        self, 
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[ImageGeneration]:
        """Получить генерации с аватарами пользователя"""
        return await self.get_completed_generations(
            user_id=user_id,
            generation_type="avatar",
            limit=limit,
            offset=offset
        )
    
    async def get_user_imagen4_generations(
        self, 
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[ImageGeneration]:
        """Получить Imagen 4 генерации пользователя"""
        return await self.get_completed_generations(
            user_id=user_id,
            generation_type="imagen4",
            limit=limit,
            offset=offset
        )
    
    async def get_user_video_generations(
        self, 
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[ImageGeneration]:
        """Получить видео генерации пользователя"""
        return await self.get_completed_generations(
            user_id=user_id,
            generation_type="video",
            limit=limit,
            offset=offset
        )
    
    async def count_user_generations_by_type(
        self, 
        user_id: UUID
    ) -> dict:
        """Подсчитать количество генераций по типам"""
        query = (
            select(
                func.count().label("total"),
                func.sum(case((ImageGeneration.generation_type == "avatar", 1), else_=0)).label("avatar_count"),
                func.sum(case((ImageGeneration.generation_type == "imagen4", 1), else_=0)).label("imagen4_count"),
                func.sum(case((ImageGeneration.generation_type == "video", 1), else_=0)).label("video_count")
            )
            .where(
                ImageGeneration.user_id == user_id,
                ImageGeneration.status == GenerationStatus.COMPLETED
            )
        )
        
        result = await self.session.execute(query)
        row = result.first()
        
        return {
            "total": row.total or 0,
            "avatar_count": row.avatar_count or 0,
            "imagen4_count": row.imagen4_count or 0,
            "video_count": row.video_count or 0
        } 