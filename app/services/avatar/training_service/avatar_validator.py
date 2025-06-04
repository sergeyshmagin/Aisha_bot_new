"""
Валидация аватаров и фотографий для обучения
Выделено из app/services/avatar/training_service.py для соблюдения правила ≤500 строк
"""
from typing import List
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.database.models import Avatar, AvatarPhoto, AvatarStatus

logger = logging.getLogger(__name__)


class AvatarValidator:
    """Валидация аватаров и фотографий для обучения"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_avatar_for_training(self, avatar_id: UUID) -> Avatar:
        """
        Получает аватар и проверяет готовность к обучению
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            Avatar: Аватар готовый к обучению
            
        Raises:
            ValueError: При ошибках валидации
        """
        query = select(Avatar).where(Avatar.id == avatar_id)
        result = await self.session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            raise ValueError(f"Аватар {avatar_id} не найден")
        
        # Проверяем статус
        if avatar.status not in [AvatarStatus.READY_FOR_TRAINING, AvatarStatus.PHOTOS_UPLOADING]:
            raise ValueError(f"Аватар {avatar_id} не готов к обучению (статус: {avatar.status})")
        
        # Проверяем что уже не обучается
        if avatar.finetune_id and avatar.status == AvatarStatus.TRAINING.value:
            raise ValueError(f"Аватар {avatar_id} уже обучается (finetune_id: {avatar.finetune_id})")
        
        return avatar
    
    async def get_avatar_photo_urls(self, avatar_id: UUID) -> List[str]:
        """
        Получает URL фотографий аватара из MinIO
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            List[str]: Список URL фотографий
            
        Raises:
            ValueError: При недостаточном количестве фотографий
        """
        query = (
            select(AvatarPhoto.minio_key)
            .where(AvatarPhoto.avatar_id == avatar_id)
            .order_by(AvatarPhoto.upload_order)
        )
        
        result = await self.session.execute(query)
        minio_keys = result.scalars().all()
        
        # Проверяем минимальное количество фотографий
        if len(minio_keys) < settings.AVATAR_MIN_PHOTOS:
            raise ValueError(
                f"Недостаточно фотографий для обучения: {len(minio_keys)}/{settings.AVATAR_MIN_PHOTOS}"
            )
        
        # Конвертируем MinIO ключи в полные URL
        # В нашем случае minio_key уже содержит полный путь к объекту
        photo_urls = [minio_key for minio_key in minio_keys]
        
        logger.info(f"[TRAINING] Найдено {len(photo_urls)} фотографий для аватара {avatar_id}")
        return photo_urls
    
    async def validate_training_readiness(self, avatar_id: UUID) -> bool:
        """
        Проверяет готовность аватара к обучению
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            bool: True если аватар готов к обучению
        """
        try:
            avatar = await self.get_avatar_for_training(avatar_id)
            photo_urls = await self.get_avatar_photo_urls(avatar_id)
            
            # Дополнительные проверки
            if not avatar.name or len(avatar.name.strip()) == 0:
                logger.warning(f"[VALIDATION] Аватар {avatar_id} не имеет имени")
                return False
            
            if not avatar.gender:
                logger.warning(f"[VALIDATION] Аватар {avatar_id} не имеет указанного пола")
                return False
            
            if not avatar.training_type:
                logger.warning(f"[VALIDATION] Аватар {avatar_id} не имеет типа обучения")
                return False
            
            logger.info(f"[VALIDATION] Аватар {avatar_id} готов к обучению")
            return True
            
        except ValueError as e:
            logger.warning(f"[VALIDATION] Аватар {avatar_id} не готов к обучению: {e}")
            return False
        except Exception as e:
            logger.exception(f"[VALIDATION] Ошибка валидации аватара {avatar_id}: {e}")
            return False 