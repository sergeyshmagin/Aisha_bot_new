"""
Сервис для работы с аватарами
"""
from typing import Dict, List, Optional, Tuple
from uuid import UUID

# from app.core.constants import AvatarStatus  # Используем строковые значения напрямую
from app.database.models import Avatar, AvatarPhoto, AvatarGender, AvatarType, AvatarTrainingType
from app.database.repositories import AvatarPhotoRepository, AvatarRepository
from app.services.base import BaseService
from app.core.logger import get_logger

logger = get_logger(__name__)


class AvatarService(BaseService):
    """
    Сервис для работы с аватарами
    """

    def _setup_repositories(self):
        """Инициализация репозиториев"""
        self.avatar_repo = AvatarRepository(self.session)
        self.photo_repo = AvatarPhotoRepository(self.session)

    async def create_avatar(
        self, 
        user_id: int, 
        name: str = None, 
        gender = None, 
        avatar_type = None, 
        training_type = None
    ) -> Avatar:
        """Создать новый аватар с параметрами"""
        # Проверяем, нет ли уже черновика
        draft = await self.avatar_repo.get_user_draft_avatar(user_id)
        if draft:
            return draft
        
        # Извлекаем значения правильно (принудительно как uppercase строки для БД)
        gender_value = str(gender.value).upper() if hasattr(gender, 'value') else str(gender).upper()
        avatar_type_value = str(avatar_type.value).upper() if hasattr(avatar_type, 'value') else str(avatar_type).upper()
        training_type_value = str(training_type.value).upper() if hasattr(training_type, 'value') else str(training_type).upper()
        
        # Создаем новый черновик с параметрами
        avatar_data = {}
        if name:
            avatar_data["name"] = name
        if gender:
            avatar_data["gender"] = gender_value
        if training_type:
            avatar_data["training_type"] = training_type_value
        
        data_for_repo = {
            "user_id": user_id,
            "name": name or "Новый аватар",
            "gender": gender_value,
            "avatar_type": avatar_type_value,
            "training_type": training_type_value,
            "status": "DRAFT",  # Передаём uppercase строковое значение
            "is_draft": True,
            "avatar_data": avatar_data,
            # Принудительно передаем все enum поля как uppercase строки
            "fal_priority": "QUALITY",
            "finetune_type": "LORA",
        }
        
        return await self.avatar_repo.create(data_for_repo)

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
        if gender.lower() not in ["male", "female"]:
            raise ValueError("Invalid gender")
        
        # Конвертируем в uppercase для БД
        gender_upper = gender.upper()
        
        return await self.avatar_repo.update(avatar_id, {
            "gender": gender_upper,
            "avatar_data": {"gender": gender.lower()}  # В avatar_data храним lowercase для удобства
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

    async def get_avatar_photos(self, avatar_id: UUID, page: int = 1, per_page: int = None) -> Tuple[List[AvatarPhoto], int]:
        """
        Получить все фото аватара с пагинацией (совместимо с новой системой)
        
        Args:
            avatar_id: ID аватара
            page: Номер страницы (не используется пока)
            per_page: Количество на странице (не используется пока)
            
        Returns:
            Tuple[List[AvatarPhoto], int]: Список фотографий и общее количество
        """
        # Для обратной совместимости возвращаем все фото и их количество
        photos = await self.photo_repo.get_avatar_photos(avatar_id)
        return photos, len(photos)

    async def finalize_avatar(self, avatar_id: UUID) -> Optional[Avatar]:
        """Завершить создание аватара"""
        return await self.avatar_repo.update(avatar_id, {
            "is_draft": False,
            "status": "READY_FOR_TRAINING"  # Передаём uppercase строковое значение
        })

    async def delete_avatar_completely(self, avatar_id: UUID) -> bool:
        """
        Полностью удаляет аватар с фотографиями, файлами из MinIO и очисткой кешей
        Используется при отмене создания аватара
        """
        try:
            # Получаем все фотографии аватара
            photos, _ = await self.get_avatar_photos(avatar_id)
            
            # Удаляем файлы из MinIO
            from app.services.storage import StorageService
            storage = StorageService()
            
            for photo in photos:
                try:
                    if photo.minio_key:
                        await storage.delete_file("avatars", photo.minio_key)
                        logger.debug(f"Удален файл из MinIO: {photo.minio_key}")
                except Exception as e:
                    logger.warning(f"Ошибка при удалении файла {photo.minio_key} из MinIO: {e}")
            
            # Удаляем записи о фотографиях из БД
            for photo in photos:
                await self.photo_repo.delete(photo.id)
            
            # Удаляем сам аватар из БД
            result = await self.avatar_repo.delete(avatar_id)
            
            # Коммитим транзакцию
            await self.session.commit()
            
            logger.info(f"Аватар {avatar_id} полностью удален с {len(photos)} фотографиями")
            return result
            
        except Exception as e:
            await self.session.rollback()
            logger.exception(f"Ошибка при полном удалении аватара {avatar_id}: {e}")
            raise
    
    async def delete_avatar(self, avatar_id: UUID) -> bool:
        """
        Алиас для delete_avatar_completely для обратной совместимости
        
        Args:
            avatar_id: ID аватара для удаления
            
        Returns:
            bool: Результат удаления
        """
        logger.warning(f"Используется устаревший метод delete_avatar для {avatar_id}. Рекомендуется использовать delete_avatar_completely")
        return await self.delete_avatar_completely(avatar_id)

    async def delete_avatar_photo(self, photo_id: UUID) -> bool:
        """
        Удаляет фото аватара через PhotoUploadService
        
        Args:
            photo_id: ID фотографии
            
        Returns:
            bool: Результат удаления
        """
        try:
            from app.services.avatar.photo_service import PhotoUploadService
            
            # Получаем фото чтобы узнать user_id
            photo = await self.photo_repo.get(photo_id)
            if not photo:
                logger.warning(f"Фото {photo_id} не найдено для удаления")
                return False
            
            # Используем PhotoUploadService для удаления с правильной логикой
            photo_service = PhotoUploadService(self.session)
            result = await photo_service.delete_photo(photo_id, photo.user_id)
            
            logger.info(f"Фото {photo_id} удалено из аватара")
            return result
            
        except Exception as e:
            logger.exception(f"Ошибка при удалении фото аватара {photo_id}: {e}")
            raise 