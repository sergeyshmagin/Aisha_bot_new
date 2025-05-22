"""
Репозиторий для работы с аватарами
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from aisha_v2.app.database.models import Avatar, AvatarPhoto
from aisha_v2.app.database.repositories.base import BaseRepository


class AvatarRepository(BaseRepository[Avatar]):
    """
    Репозиторий для работы с аватарами
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, Avatar)

    async def get_with_photos(self, avatar_id: UUID) -> Optional[Avatar]:
        """Получить аватар с фотографиями"""
        stmt = (
            select(self.model)
            .where(self.model.id == avatar_id)
            .options(selectinload(self.model.photos))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_avatars(self, user_id: int) -> List[Avatar]:
        """Получить все аватары пользователя"""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .options(selectinload(self.model.photos))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_draft_avatar(self, user_id: int) -> Optional[Avatar]:
        """Получить черновик аватара пользователя"""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id, self.model.is_draft.is_(True))
            .options(selectinload(self.model.photos))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


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
            .order_by(self.model.order)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_next_photo_order(self, avatar_id: UUID) -> int:
        """Получить следующий порядковый номер для фото"""
        stmt = (
            select(self.model.order)
            .where(self.model.avatar_id == avatar_id)
            .order_by(self.model.order.desc())
        )
        result = await self.session.execute(stmt)
        max_order = result.scalar_one_or_none()
        return (max_order or 0) + 1
