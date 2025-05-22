"""
Сервис для работы с аватарами
"""
from typing import Dict, List, Optional
from uuid import UUID

from aisha_v2.app.core.constants import AvatarGender, AvatarStatus
from aisha_v2.app.database.models import Avatar, AvatarPhoto
from aisha_v2.app.database.repositories import AvatarPhotoRepository, AvatarRepository
from aisha_v2.app.services.base import BaseService


class AvatarService(BaseService):
    """
    Сервис для работы с аватарами
    """

    def _setup_repositories(self):
        """Инициализация репозиториев"""
        self.avatar_repo = AvatarRepository(self.session)
        self.photo_repo = AvatarPhotoRepository(self.session)

    async def create_avatar(self, user_id: int) -> Avatar:
        """Создать новый аватар"""
        # Проверяем, нет ли уже черновика
        draft = await self.avatar_repo.get_user_draft_avatar(user_id)
        if draft:
            return draft
        
        # Создаем новый черновик
        return await self.avatar_repo.create({
            "user_id": user_id,
            "status": AvatarStatus.DRAFT,
            "is_draft": True,
            "avatar_data": {}
        })

    async def get_avatar(self, avatar_id: UUID) -> Optional[Avatar]:
        """Получить аватар по ID"""
        return await self.avatar_repo.get_with_photos(avatar_id)

    async def get_user_avatars(self, user_id: int) -> List[Avatar]:
        """Получить все аватары пользователя"""
        return await self.avatar_repo.get_user_avatars(user_id)

    async def get_user_draft_avatar(self, user_id: int) -> Optional[Avatar]:
        """Получить черновик аватара пользователя"""
        return await self.avatar_repo.get_user_draft_avatar(user_id)

    async def update_avatar(self, avatar_id: UUID, data: Dict) -> Optional[Avatar]:
        """Обновить данные аватара"""
        return await self.avatar_repo.update(avatar_id, data)

    async def set_avatar_gender(self, avatar_id: UUID, gender: str) -> Optional[Avatar]:
        """Установить пол аватара"""
        if gender not in [AvatarGender.MALE, AvatarGender.FEMALE]:
            raise ValueError("Invalid gender")
        
        return await self.avatar_repo.update(avatar_id, {
            "gender": gender,
            "avatar_data": {"gender": gender}
        })

    async def set_avatar_name(self, avatar_id: UUID, name: str) -> Optional[Avatar]:
        """Установить имя аватара"""
        return await self.avatar_repo.update(avatar_id, {
            "name": name,
            "avatar_data": {"name": name}
        })

    async def add_photo(self, avatar_id: UUID, minio_key: str) -> AvatarPhoto:
        """Добавить фото к аватару"""
        order = await self.photo_repo.get_next_photo_order(avatar_id)
        return await self.photo_repo.create({
            "avatar_id": avatar_id,
            "minio_key": minio_key,
            "order": order
        })

    async def remove_photo(self, photo_id: UUID) -> bool:
        """Удалить фото"""
        return await self.photo_repo.delete(photo_id)

    async def get_avatar_photos(self, avatar_id: UUID) -> List[AvatarPhoto]:
        """Получить все фото аватара"""
        return await self.photo_repo.get_avatar_photos(avatar_id)

    async def finalize_avatar(self, avatar_id: UUID) -> Optional[Avatar]:
        """Завершить создание аватара"""
        return await self.avatar_repo.update(avatar_id, {
            "is_draft": False,
            "status": AvatarStatus.READY
        })

    async def delete_avatar(self, avatar_id: UUID) -> bool:
        """Удалить аватар"""
        # Сначала удаляем все фото
        photos = await self.get_avatar_photos(avatar_id)
        for photo in photos:
            await self.photo_repo.delete(photo.id)
        
        # Затем удаляем сам аватар
        return await self.avatar_repo.delete(avatar_id)
