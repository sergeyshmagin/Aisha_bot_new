"""
Основной сервис для управления аватарами
"""
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload

from ...core.config import settings
from ...core.logger import get_logger
from ...database.models import (
    Avatar, AvatarPhoto, User, 
    AvatarStatus, AvatarType, AvatarGender
)
from ..base import BaseService

logger = get_logger(__name__)


class AvatarService(BaseService):
    """
    Основной сервис для управления аватарами.
    
    Функции:
    - Создание и настройка аватаров
    - Управление жизненным циклом
    - Статистика и аналитика
    - Контроль лимитов пользователя
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.session = session

    async def create_avatar(
        self, 
        user_id: UUID, 
        name: str, 
        avatar_type: AvatarType,
        gender: AvatarGender,
        **kwargs
    ) -> Avatar:
        """
        Создает новый аватар
        
        Args:
            user_id: ID пользователя
            name: Имя аватара
            avatar_type: Тип аватара
            gender: Пол аватара
            **kwargs: Дополнительные параметры
            
        Returns:
            Avatar: Созданный аватар
            
        Raises:
            ValueError: При превышении лимитов или других ошибках
        """
        try:
            # Проверяем лимиты пользователя
            await self._check_user_limits(user_id)
            
            # Проверяем уникальность имени для пользователя
            await self._check_name_uniqueness(user_id, name)
            
            # Создаем аватар
            avatar = Avatar(
                user_id=user_id,
                name=name.strip(),
                avatar_type=avatar_type,
                gender=gender,
                status=AvatarStatus.DRAFT,
                fal_mode=kwargs.get('fal_mode', settings.FAL_DEFAULT_MODE),
                fal_iterations=kwargs.get('fal_iterations', settings.FAL_DEFAULT_ITERATIONS),
                fal_priority=kwargs.get('fal_priority', settings.FAL_DEFAULT_PRIORITY),
                trigger_word=kwargs.get('trigger_word', settings.FAL_TRIGGER_WORD),
                lora_rank=kwargs.get('lora_rank', settings.FAL_LORA_RANK),
                avatar_data={
                    'creation_source': 'bot_v2',
                    'created_ip': kwargs.get('ip_address'),
                },
                training_config={
                    'auto_generate_preview': settings.AUTO_GENERATE_PREVIEW,
                    'enable_nsfw_detection': settings.ENABLE_NSFW_DETECTION,
                    'enable_face_detection': settings.ENABLE_FACE_DETECTION,
                }
            )
            
            self.session.add(avatar)
            await self.session.commit()
            await self.session.refresh(avatar)
            
            logger.info(
                f"Создан аватар {avatar.id} для пользователя {user_id}: "
                f"name='{name}', type={avatar_type.value}, gender={gender.value}"
            )
            
            return avatar
            
        except Exception as e:
            await self.session.rollback()
            logger.exception(f"Ошибка при создании аватара: {e}")
            raise

    async def get_user_avatars(
        self, 
        user_id: UUID, 
        status: Optional[AvatarStatus] = None,
        limit: int = 50
    ) -> List[Avatar]:
        """
        Получает список аватаров пользователя
        
        Args:
            user_id: ID пользователя
            status: Фильтр по статусу (опционально)
            limit: Максимальное количество результатов
            
        Returns:
            List[Avatar]: Список аватаров
        """
        try:
            query = select(Avatar).where(Avatar.user_id == user_id)
            
            if status:
                query = query.where(Avatar.status == status)
                
            query = (
                query.options(selectinload(Avatar.photos))
                .order_by(Avatar.created_at.desc())
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            avatars = result.scalars().all()
            
            logger.debug(f"Найдено {len(avatars)} аватаров для пользователя {user_id}")
            return avatars
            
        except Exception as e:
            logger.exception(f"Ошибка при получении аватаров: {e}")
            raise

    async def get_avatar_by_id(self, avatar_id: UUID) -> Optional[Avatar]:
        """
        Получает аватар по ID
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            Optional[Avatar]: Аватар или None
        """
        try:
            query = (
                select(Avatar)
                .where(Avatar.id == avatar_id)
                .options(selectinload(Avatar.photos))
            )
            
            result = await self.session.execute(query)
            avatar = result.scalar_one_or_none()
            
            return avatar
            
        except Exception as e:
            logger.exception(f"Ошибка при получении аватара {avatar_id}: {e}")
            raise

    async def update_avatar_status(
        self, 
        avatar_id: UUID, 
        status: AvatarStatus,
        progress: Optional[int] = None,
        **metadata
    ) -> bool:
        """
        Обновляет статус аватара
        
        Args:
            avatar_id: ID аватара
            status: Новый статус
            progress: Прогресс обучения (0-100)
            **metadata: Дополнительные метаданные
            
        Returns:
            bool: True если обновлено успешно
        """
        try:
            update_data = {"status": status, "updated_at": datetime.utcnow()}
            
            # Обновляем прогресс
            if progress is not None:
                update_data["training_progress"] = max(0, min(100, progress))
            
            # Устанавливаем временные метки
            if status == AvatarStatus.TRAINING:
                update_data["training_started_at"] = datetime.utcnow()
            elif status == AvatarStatus.COMPLETED:
                update_data["training_completed_at"] = datetime.utcnow()
                update_data["training_progress"] = 100
            
            # Обновляем метаданные
            if metadata:
                stmt = select(Avatar.avatar_data).where(Avatar.id == avatar_id)
                result = await self.session.execute(stmt)
                current_data = result.scalar() or {}
                current_data.update(metadata)
                update_data["avatar_data"] = current_data
            
            stmt = (
                update(Avatar)
                .where(Avatar.id == avatar_id)
                .values(**update_data)
            )
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            success = result.rowcount > 0
            if success:
                logger.info(f"Обновлен статус аватара {avatar_id}: {status.value}")
            else:
                logger.warning(f"Аватар {avatar_id} не найден для обновления статуса")
            
            return success
            
        except Exception as e:
            await self.session.rollback()
            logger.exception(f"Ошибка при обновлении статуса аватара {avatar_id}: {e}")
            raise

    async def delete_avatar(self, avatar_id: UUID, user_id: UUID) -> bool:
        """
        Удаляет аватар (с проверкой владельца)
        
        Args:
            avatar_id: ID аватара
            user_id: ID пользователя (для проверки прав)
            
        Returns:
            bool: True если удален успешно
        """
        try:
            # Проверяем существование и права
            avatar = await self.get_avatar_by_id(avatar_id)
            if not avatar or avatar.user_id != user_id:
                logger.warning(f"Попытка удалить чужой аватар {avatar_id} пользователем {user_id}")
                return False
            
            # Удаляем (каскадное удаление фотографий настроено в модели)
            await self.session.delete(avatar)
            await self.session.commit()
            
            logger.info(f"Удален аватар {avatar_id} пользователя {user_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.exception(f"Ошибка при удалении аватара {avatar_id}: {e}")
            raise

    async def get_avatar_statistics(self, avatar_id: UUID) -> Dict[str, Any]:
        """
        Получает статистику по аватару
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            Dict[str, Any]: Статистика аватара
        """
        try:
            avatar = await self.get_avatar_by_id(avatar_id)
            if not avatar:
                return {}
            
            # Подсчитываем статистику
            photos_count = len(avatar.photos)
            
            # Время обучения
            training_duration = None
            if avatar.training_started_at and avatar.training_completed_at:
                training_duration = (
                    avatar.training_completed_at - avatar.training_started_at
                ).total_seconds()
            
            stats = {
                "id": str(avatar.id),
                "name": avatar.name,
                "status": avatar.status.value,
                "type": avatar.avatar_type.value,
                "gender": avatar.gender.value,
                "photos_count": photos_count,
                "generations_count": avatar.generations_count,
                "training_progress": avatar.training_progress,
                "training_duration_seconds": training_duration,
                "created_at": avatar.created_at.isoformat(),
                "updated_at": avatar.updated_at.isoformat(),
                "training_config": avatar.training_config,
                "finetune_id": avatar.finetune_id,
            }
            
            return stats
            
        except Exception as e:
            logger.exception(f"Ошибка при получении статистики аватара {avatar_id}: {e}")
            raise

    async def update_photos_count(self, avatar_id: UUID) -> bool:
        """
        Обновляет счетчик фотографий в аватаре
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            bool: True если обновлено успешно
        """
        try:
            # Подсчитываем актуальное количество фотографий
            count_query = (
                select(func.count(AvatarPhoto.id))
                .where(AvatarPhoto.avatar_id == avatar_id)
            )
            result = await self.session.execute(count_query)
            photos_count = result.scalar() or 0
            
            # Обновляем счетчик
            stmt = (
                update(Avatar)
                .where(Avatar.id == avatar_id)
                .values(photos_count=photos_count, updated_at=datetime.utcnow())
            )
            
            await self.session.execute(stmt)
            await self.session.commit()
            
            logger.debug(f"Обновлен счетчик фотографий для аватара {avatar_id}: {photos_count}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.exception(f"Ошибка при обновлении счетчика фотографий {avatar_id}: {e}")
            raise

    async def _check_user_limits(self, user_id: UUID) -> None:
        """
        Проверяет лимиты пользователя на создание аватаров
        
        Args:
            user_id: ID пользователя
            
        Raises:
            ValueError: При превышении лимитов
        """
        # Подсчитываем активные аватары
        count_query = (
            select(func.count(Avatar.id))
            .where(
                Avatar.user_id == user_id,
                Avatar.status != AvatarStatus.CANCELLED
            )
        )
        result = await self.session.execute(count_query)
        avatars_count = result.scalar() or 0
        
        if avatars_count >= settings.AVATAR_MAX_PHOTOS_PER_USER:
            raise ValueError(
                f"Превышен лимит аватаров: {avatars_count}/{settings.AVATAR_MAX_PHOTOS_PER_USER}"
            )

    async def _check_name_uniqueness(self, user_id: UUID, name: str) -> None:
        """
        Проверяет уникальность имени аватара для пользователя
        
        Args:
            user_id: ID пользователя
            name: Имя аватара
            
        Raises:
            ValueError: При дублировании имени
        """
        existing_query = (
            select(Avatar.id)
            .where(
                Avatar.user_id == user_id,
                Avatar.name == name.strip(),
                Avatar.status != AvatarStatus.CANCELLED
            )
        )
        result = await self.session.execute(existing_query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValueError(f"Аватар с именем '{name}' уже существует") 