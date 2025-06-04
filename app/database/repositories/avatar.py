"""
Репозиторий для работы с аватарами
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update, func, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Avatar, AvatarPhoto
from app.database.repositories.base import BaseRepository


class AvatarRepository(BaseRepository[Avatar]):
    """
    Репозиторий для работы с аватарами
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, Avatar)

    async def get_with_photos(self, avatar_id: UUID) -> Optional[Avatar]:
        """Получить аватар с фотографиями (отсортированными по порядку загрузки)"""
        stmt = (
            select(self.model)
            .where(self.model.id == avatar_id)
            .options(selectinload(self.model.photos))
        )
        result = await self.session.execute(stmt)
        avatar = result.scalar_one_or_none()
        
        # Сортируем фотографии по порядку загрузки
        if avatar and avatar.photos:
            avatar.photos.sort(key=lambda photo: photo.upload_order)
        
        return avatar

    async def get_user_avatars(self, user_id: UUID) -> List[Avatar]:
        """Получить все аватары пользователя (с фотографиями, отсортированными по порядку загрузки)"""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .options(selectinload(self.model.photos))
        )
        result = await self.session.execute(stmt)
        avatars = list(result.scalars().all())
        
        # Сортируем фотографии по порядку загрузки
        for avatar in avatars:
            if avatar.photos:
                avatar.photos.sort(key=lambda photo: photo.upload_order)
        
        return avatars

    async def get_user_draft_avatar(self, user_id: UUID) -> Optional[Avatar]:
        """Получить черновик аватара пользователя (с фотографиями, отсортированными по порядку загрузки)"""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id, cast(self.model.status, String) == "draft")
            .options(selectinload(self.model.photos))
        )
        result = await self.session.execute(stmt)
        avatar = result.scalar_one_or_none()
        
        # Сортируем фотографии по порядку загрузки
        if avatar and avatar.photos:
            avatar.photos.sort(key=lambda photo: photo.upload_order)
        
        return avatar

    async def get_main_avatar(self, user_id: UUID) -> Optional[Avatar]:
        """Получить основной аватар пользователя (с фотографиями, отсортированными по порядку загрузки)"""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id, self.model.is_main.is_(True))
            .options(selectinload(self.model.photos))
        )
        result = await self.session.execute(stmt)
        avatar = result.scalar_one_or_none()
        
        # Сортируем фотографии по порядку загрузки
        if avatar and avatar.photos:
            avatar.photos.sort(key=lambda photo: photo.upload_order)
        
        return avatar

    async def clear_main_avatar(self, user_id: UUID) -> None:
        """
        Убирает флаг is_main у ВСЕХ аватаров пользователя
        
        ⚠️ ВАЖНО: Этот метод обеспечивает, что у пользователя не будет основных аватаров.
        Используется перед установкой нового основного аватара.
        
        Args:
            user_id: ID пользователя
        """
        stmt = (
            update(self.model)
            .where(self.model.user_id == user_id)
            .values(is_main=False)
        )
        await self.session.execute(stmt)

    async def count_main_avatars(self, user_id: UUID) -> int:
        """
        Подсчитывает количество основных аватаров у пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            int: Количество основных аватаров (должно быть 0 или 1)
        """
        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.user_id == user_id,
                self.model.is_main.is_(True)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_user_avatars_with_photos(self, user_id: UUID) -> List[Avatar]:
        """Получить все завершенные аватары пользователя с фотографиями (отсортированными по порядку загрузки)"""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                cast(self.model.status, String) != "draft"
            )
            .options(selectinload(self.model.photos))
            .order_by(self.model.is_main.desc(), self.model.created_at.desc())
        )
        result = await self.session.execute(stmt)
        avatars = list(result.scalars().all())
        
        # Сортируем фотографии по порядку загрузки для корректного отображения превью
        for avatar in avatars:
            if avatar.photos:
                avatar.photos.sort(key=lambda photo: photo.upload_order)
        
        return avatars


class AvatarPhotoRepository(BaseRepository[AvatarPhoto]):
    """
    Репозиторий для работы с фотографиями аватаров
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, AvatarPhoto)

    async def get_avatar_photos(self, avatar_id: UUID) -> List[AvatarPhoto]:
        """Получить все фотографии аватара"""
        stmt = (
            select(self.model)
            .where(self.model.avatar_id == avatar_id)
            .order_by(self.model.upload_order)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_next_photo_order(self, avatar_id: UUID) -> int:
        """Получить следующий порядковый номер для фото"""
        stmt = (
            select(self.model.upload_order)
            .where(self.model.avatar_id == avatar_id)
            .order_by(self.model.upload_order.desc())
        )
        result = await self.session.execute(stmt)
        max_order = result.scalar_one_or_none()
        return (max_order or 0) + 1
