"""
Основной модуль управления генерациями изображений
"""
import asyncio
from typing import List, Optional
from uuid import UUID

from app.core.database import get_session
from app.core.logger import get_logger
from app.database.models import Avatar, ImageGeneration, GenerationStatus

logger = get_logger(__name__)


class GenerationManager:
    """Управление CRUD операциями генераций"""
    
    def __init__(self):
        pass
    
    async def get_user_generations(
        self, 
        user_id: UUID, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[ImageGeneration]:
        """
        Получает генерации пользователя
        
        Args:
            user_id: ID пользователя
            limit: Лимит записей
            offset: Смещение
            
        Returns:
            List[ImageGeneration]: Список генераций
        """
        async with get_session() as session:
            from sqlalchemy import select
            
            stmt = (
                select(ImageGeneration)
                .where(ImageGeneration.user_id == user_id)
                .order_by(ImageGeneration.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            
            result = await session.execute(stmt)
            generations = result.scalars().all()
            
            logger.info(f"Получено {len(generations)} генераций для пользователя {user_id}")
            return list(generations)
    
    async def get_generation_by_id(self, generation_id: UUID) -> Optional[ImageGeneration]:
        """
        Получает генерацию по ID
        
        Args:
            generation_id: ID генерации
            
        Returns:
            Optional[ImageGeneration]: Генерация или None
        """
        async with get_session() as session:
            from sqlalchemy import select
            
            stmt = select(ImageGeneration).where(ImageGeneration.id == generation_id)
            result = await session.execute(stmt)
            generation = result.scalar_one_or_none()
            
            if generation:
                logger.info(f"Найдена генерация {generation_id}")
            else:
                logger.warning(f"Генерация {generation_id} не найдена")
                
            return generation
    
    async def get_generations_by_ids(self, generation_ids: List[UUID]) -> List[ImageGeneration]:
        """
        Получает генерации по списку ID
        
        Args:
            generation_ids: Список ID генераций
            
        Returns:
            List[ImageGeneration]: Список найденных генераций
        """
        if not generation_ids:
            return []
        
        async with get_session() as session:
            from sqlalchemy import select
            
            stmt = (
                select(ImageGeneration)
                .where(ImageGeneration.id.in_(generation_ids))
                .order_by(ImageGeneration.created_at.desc())
            )
            
            result = await session.execute(stmt)
            generations = result.scalars().all()
            
            logger.info(f"Найдено {len(generations)} из {len(generation_ids)} запрошенных генераций")
            return list(generations)
    
    async def save_generation(self, generation: ImageGeneration):
        """
        Сохраняет новую генерацию в БД
        
        Args:
            generation: Объект генерации
        """
        async with get_session() as session:
            session.add(generation)
            await session.commit()
            await session.refresh(generation)
            logger.info(f"Сохранена генерация {generation.id}")
    
    async def update_generation(self, generation: ImageGeneration):
        """
        Обновляет существующую генерацию
        
        Args:
            generation: Объект генерации
        """
        async with get_session() as session:
            await session.merge(generation)
            await session.commit()
            logger.info(f"Обновлена генерация {generation.id}")
    
    async def delete_generation(self, generation_id: UUID) -> bool:
        """
        Удаляет генерацию из БД
        
        Args:
            generation_id: ID генерации
            
        Returns:
            bool: True если успешно удалено
        """
        try:
            async with get_session() as session:
                from sqlalchemy import select, delete
                
                # Получаем генерацию для логирования
                stmt = select(ImageGeneration).where(ImageGeneration.id == generation_id)
                result = await session.execute(stmt)
                generation = result.scalar_one_or_none()
                
                if not generation:
                    logger.warning(f"Генерация {generation_id} не найдена для удаления")
                    return False
                
                # Удаляем генерацию
                delete_stmt = delete(ImageGeneration).where(ImageGeneration.id == generation_id)
                await session.execute(delete_stmt)
                await session.commit()
                
                logger.info(f"Генерация {generation_id} успешно удалена")
                return True
                
        except Exception as e:
            logger.exception(f"Ошибка удаления генерации {generation_id}: {e}")
            return False
    
    async def toggle_favorite(self, generation_id: UUID, user_id: UUID) -> bool:
        """
        Переключает статус избранного для генерации
        
        Args:
            generation_id: ID генерации
            user_id: ID пользователя (для проверки прав)
            
        Returns:
            bool: Новый статус избранного
        """
        try:
            async with get_session() as session:
                from sqlalchemy import select
                
                # Получаем генерацию
                stmt = select(ImageGeneration).where(
                    ImageGeneration.id == generation_id,
                    ImageGeneration.user_id == user_id
                )
                result = await session.execute(stmt)
                generation = result.scalar_one_or_none()
                
                if not generation:
                    logger.warning(f"Генерация {generation_id} не найдена или не принадлежит пользователю {user_id}")
                    return False
                
                # Переключаем статус
                generation.is_favorite = not generation.is_favorite
                await session.commit()
                
                logger.info(f"Генерация {generation_id} {'добавлена в избранное' if generation.is_favorite else 'удалена из избранного'}")
                return generation.is_favorite
                
        except Exception as e:
            logger.exception(f"Ошибка переключения избранного для генерации {generation_id}: {e}")
            return False
    
    async def get_avatar(self, avatar_id: UUID, user_id: UUID) -> Optional[Avatar]:
        """
        Получает аватар пользователя
        
        Args:
            avatar_id: ID аватара
            user_id: ID пользователя
            
        Returns:
            Optional[Avatar]: Аватар или None
        """
        async with get_session() as session:
            from sqlalchemy import select
            
            stmt = select(Avatar).where(
                Avatar.id == avatar_id,
                Avatar.user_id == user_id
            )
            result = await session.execute(stmt)
            avatar = result.scalar_one_or_none()
            
            if avatar:
                logger.info(f"Найден аватар {avatar_id} для пользователя {user_id}")
            else:
                logger.warning(f"Аватар {avatar_id} не найден для пользователя {user_id}")
                
            return avatar
    
    def is_avatar_ready_for_generation(self, avatar: Avatar) -> bool:
        """
        Проверяет готовность аватара к генерации
        
        Args:
            avatar: Аватар для проверки
            
        Returns:
            bool: True если аватар готов
        """
        return avatar.status == "completed"
    
    def get_avatar_status_message(self, avatar: Avatar) -> str:
        """
        Возвращает понятное сообщение о статусе аватара
        
        Args:
            avatar: Аватар
            
        Returns:
            str: Сообщение об ошибке для пользователя
        """
        status_messages = {
            "draft": f"Аватар '{avatar.name}' еще не готов - находится в статусе черновика",
            "photos_uploading": f"Аватар '{avatar.name}' еще загружает фотографии",
            "ready_for_training": f"Аватар '{avatar.name}' готов к обучению, но обучение еще не запущено",
            "training": f"Аватар '{avatar.name}' в процессе обучения. Попробуйте позже",
            "error": f"При обучении аватара '{avatar.name}' произошла ошибка",
            "cancelled": f"Обучение аватара '{avatar.name}' было отменено",
        }
        
        return status_messages.get(
            avatar.status, 
            f"Аватар '{avatar.name}' не готов к генерации (статус: {avatar.status})"
        )
    
    def build_final_prompt(self, original_prompt: str, avatar: Avatar) -> str:
        """
        Строит финальный промпт с учетом аватара
        
        Args:
            original_prompt: Оригинальный промпт
            avatar: Аватар
            
        Returns:
            str: Финальный промпт
        """
        # Добавляем триггер-слово для аватара
        trigger_word = f"<{avatar.trigger_word}>" if avatar.trigger_word else ""
        
        if trigger_word:
            final_prompt = f"{trigger_word} {original_prompt}"
        else:
            final_prompt = original_prompt
        
        logger.info(f"Построен финальный промпт для аватара {avatar.id}: '{final_prompt[:100]}...'")
        return final_prompt 