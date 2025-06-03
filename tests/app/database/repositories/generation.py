"""
Репозиторий для работы с генерациями изображений
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.database.models.generation import ImageGeneration, GenerationStatus
from app.database.repositories.base import BaseRepository


class ImageGenerationRepository(BaseRepository[ImageGeneration]):
    """Репозиторий для работы с генерациями изображений"""
    
    def __init__(self, session):
        super().__init__(ImageGeneration, session)
    
    async def get_user_generations(
        self, 
        user_id: UUID, 
        status: Optional[GenerationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ImageGeneration]:
        """Получить генерации пользователя"""
        query = (
            select(ImageGeneration)
            .options(selectinload(ImageGeneration.avatar))
            .where(ImageGeneration.user_id == user_id)
        )
        
        if status:
            query = query.where(ImageGeneration.status == status)
        
        query = query.order_by(desc(ImageGeneration.created_at))
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_completed_generations(
        self, 
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[ImageGeneration]:
        """Получить завершенные генерации пользователя"""
        return await self.get_user_generations(
            user_id=user_id,
            status=GenerationStatus.COMPLETED,
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
            from datetime import datetime
            generation.completed_at = datetime.utcnow()
        
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