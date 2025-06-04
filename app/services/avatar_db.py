"""
Сервис для работы с аватарами
"""
from typing import Dict, List, Optional, Tuple
from uuid import UUID

# from app.core.constants import AvatarStatus  # Используем строковые значения напрямую
from app.database.models import Avatar, AvatarPhoto, AvatarGender, AvatarType, AvatarTrainingType
from app.database.repositories import AvatarPhotoRepository, AvatarRepository
from app.services.base import BaseService
from app.services.cache_service import cache_service
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
        user_id: UUID, 
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
            "status": "DRAFT",  # ✅ ИСПРАВЛЕНО: используем uppercase как в архиве
            "avatar_data": avatar_data,
            # Принудительно передаем все enum поля как uppercase строки
            "fal_priority": "QUALITY",
            "finetune_type": "LORA",
        }
        
        # ✅ Создаем аватар без is_draft - поле удалено из БД
        logger.info(f"[CREATE_AVATAR] data_for_repo содержит: {list(data_for_repo.keys())}")
        
        avatar = await self.avatar_repo.create(data_for_repo)
        
        # ✅ Сбрасываем кеш списка аватаров пользователя
        if avatar:
            await cache_service.delete(f"user_avatars:{user_id}")
        
        return avatar

    async def get_avatar(self, avatar_id: UUID) -> Optional[Avatar]:
        """
        Получает аватар по ID с фотографиями и кешированием
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            Optional[Avatar]: Аватар с фотографиями или None
        """
        try:
            # ✅ Проверяем кеш метаданных
            cached_metadata = await cache_service.get_cached_avatar_metadata(avatar_id)
            
            avatar = await self.avatar_repo.get_with_photos(avatar_id)
            
            # ✅ Кешируем метаданные аватара
            if avatar:
                metadata = {
                    "id": str(avatar.id),
                    "user_id": avatar.user_id,
                    "name": avatar.name,
                    "gender": avatar.gender,
                    "avatar_type": avatar.avatar_type,
                    "training_type": avatar.training_type,
                    "status": avatar.status,
                    "photos_count": len(avatar.photos) if avatar.photos else 0,
                    "generations_count": avatar.generations_count,
                    "is_main": avatar.is_main,
                    "created_at": avatar.created_at,
                    "updated_at": avatar.updated_at
                }
                await cache_service.cache_avatar_metadata(avatar_id, metadata)
            
            return avatar
        except Exception as e:
            logger.exception(f"Ошибка при получении аватара {avatar_id}: {e}")
            raise

    async def get_user_avatars(self, user_id: UUID) -> List[Avatar]:
        """Получить все аватары пользователя с кешированием"""
        # ✅ Проверяем кеш списка аватаров
        cached_avatar_ids = await cache_service.get_cached_user_avatars_list(user_id)
        if cached_avatar_ids:
            # Восстанавливаем аватары по ID (можно оптимизировать bulk запросом)
            avatars = []
            for avatar_id in cached_avatar_ids:
                avatar = await self.avatar_repo.get(UUID(avatar_id))
                if avatar:
                    avatars.append(avatar)
            return avatars
        
        # ✅ Если не в кеше, запрашиваем из БД
        avatars = await self.avatar_repo.get_user_avatars(user_id)
        
        # ✅ Кешируем список ID аватаров
        if avatars:
            avatar_ids = [str(avatar.id) for avatar in avatars]
            await cache_service.cache_user_avatars_list(user_id, avatar_ids)
        
        return avatars

    async def get_user_draft_avatar(self, user_id: UUID) -> Optional[Avatar]:
        """Получить черновик аватара пользователя"""
        return await self.avatar_repo.get_user_draft_avatar(user_id)

    async def update_avatar(self, avatar_id: UUID, data: Dict) -> Optional[Avatar]:
        """Обновить данные аватара"""
        avatar = await self.avatar_repo.update(avatar_id, data)
        
        # ✅ Сбрасываем кеш метаданных при обновлении
        if avatar:
            await cache_service.delete(f"avatar_meta:{avatar_id}")
            # Если изменился статус, сбрасываем список пользователя
            if "status" in data or "is_main" in data:
                await cache_service.delete(f"user_avatars:{avatar.user_id}")
        
        return avatar

    async def set_avatar_gender(self, avatar_id: UUID, gender: str) -> Optional[Avatar]:
        """Установить пол аватара"""
        if gender.lower() not in ["male", "female"]:
            raise ValueError("Invalid gender")
        
        # Конвертируем в uppercase для БД
        gender_upper = gender.upper()
        
        avatar = await self.avatar_repo.update(avatar_id, {
            "gender": gender_upper,
            "avatar_data": {"gender": gender.lower()}  # В avatar_data храним lowercase для удобства
        })
        
        # ✅ Сбрасываем кеш метаданных
        if avatar:
            await cache_service.delete(f"avatar_meta:{avatar_id}")
        
        return avatar

    async def set_avatar_name(self, avatar_id: UUID, name: str) -> Optional[Avatar]:
        """Установить имя аватара"""
        avatar = await self.avatar_repo.update(avatar_id, {
            "name": name,
            "avatar_data": {"name": name}
        })
        
        # ✅ Сбрасываем кеш метаданных
        if avatar:
            await cache_service.delete(f"avatar_meta:{avatar_id}")
        
        return avatar

    async def add_photo(self, avatar_id: UUID, minio_key: str) -> AvatarPhoto:
        """Добавить фото к аватару"""
        order = await self.photo_repo.get_next_photo_order(avatar_id)
        photo = await self.photo_repo.create({
            "avatar_id": avatar_id,
            "minio_key": minio_key,
            "upload_order": order  # FIXED: заменяем order на upload_order
        })
        
        # ✅ Сбрасываем кеш метаданных аватара (изменилось количество фото)
        if photo:
            await cache_service.delete(f"avatar_meta:{avatar_id}")
        
        return photo

    async def remove_photo(self, photo_id: UUID) -> bool:
        """Удалить фото"""
        # Получаем фото для определения avatar_id
        photo = await self.photo_repo.get(photo_id)
        result = await self.photo_repo.delete(photo_id)
        
        # ✅ Сбрасываем кеш метаданных аватара
        if result and photo:
            await cache_service.delete(f"avatar_meta:{photo.avatar_id}")
        
        return result

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
        avatar = await self.avatar_repo.update(avatar_id, {
            # ✅ ИСПРАВЛЕНО: используем только status - поле is_draft удалено из БД
            "status": "ready_for_training"  # Передаём lowercase строковое значение
        })
        
        # ✅ Сбрасываем кеши
        if avatar:
            await cache_service.delete(f"avatar_meta:{avatar_id}")
            await cache_service.delete(f"user_avatars:{avatar.user_id}")
        
        return avatar

    async def delete_avatar_completely(self, avatar_id: UUID) -> bool:
        """
        Полностью удаляет аватар со всеми файлами
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            bool: Результат удаления
        """
        try:
            # Получаем аватар с фотографиями
            avatar = await self.avatar_repo.get_with_photos(avatar_id)
            if not avatar:
                logger.warning(f"Аватар {avatar_id} не найден для удаления")
                return False
            
            # Удаляем все фотографии через сервис
            from app.services.avatar.photo_service import PhotoUploadService
            photo_service = PhotoUploadService(self.session)
            
            for photo in avatar.photos:
                try:
                    # Исправляем сигнатуру метода delete_photo - добавляем user_id
                    await photo_service.delete_photo(photo.id, avatar.user_id)
                except Exception as e:
                    logger.warning(f"Не удалось удалить фото {photo.id}: {e}")
            
            # Удаляем аватар из базы
            await self.avatar_repo.delete(avatar_id)
            await self.session.commit()
            
            # ✅ Очищаем все связанные кеши
            await cache_service.delete(f"avatar_meta:{avatar_id}")
            await cache_service.delete(f"user_avatars:{avatar.user_id}")
            
            logger.info(f"Аватар {avatar_id} полностью удален")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.exception(f"Ошибка при полном удалении аватара {avatar_id}: {e}")
            raise



    async def delete_avatar_photo(self, photo_id: UUID, user_id: UUID) -> bool:
        """
        Удаляет фото аватара через PhotoUploadService
        
        Args:
            photo_id: ID фотографии
            user_id: ID пользователя
            
        Returns:
            bool: Результат удаления
        """
        try:
            # Получаем фото для определения avatar_id
            photo = await self.photo_repo.get(photo_id)
            if not photo:
                return False
                
            from app.services.avatar.photo_service import PhotoUploadService
            photo_service = PhotoUploadService(self.session)
            result = await photo_service.delete_photo(photo_id, user_id)
            
            # ✅ Сбрасываем кеш метаданных аватара
            if result:
                await cache_service.delete(f"avatar_meta:{photo.avatar_id}")
            
            return result
            
        except Exception as e:
            logger.exception(f"Ошибка при удалении фото аватара {photo_id}: {e}")
            return False

    async def set_main_avatar(self, user_id: UUID, avatar_id: UUID) -> bool:
        """
        Устанавливает аватар как основной для пользователя
        
        Args:
            user_id: ID пользователя
            avatar_id: ID аватара
            
        Returns:
            bool: Результат операции
        """
        try:
            # Сначала убираем флаг is_main у всех аватаров пользователя
            await self.avatar_repo.clear_main_avatar(user_id)
            
            # Устанавливаем флаг is_main для указанного аватара
            avatar = await self.avatar_repo.update(avatar_id, {"is_main": True})
            
            if avatar:
                # ✅ Сбрасываем кеши
                await cache_service.delete(f"avatar_meta:{avatar_id}")
                await cache_service.delete(f"user_avatars:{user_id}")
                
                logger.info(f"Аватар {avatar_id} установлен как основной для пользователя {user_id}")
                return True
            else:
                logger.warning(f"Не удалось установить аватар {avatar_id} как основной")
                return False
                
        except Exception as e:
            logger.exception(f"Ошибка при установке основного аватара {avatar_id} для пользователя {user_id}: {e}")
            return False

    async def unset_main_avatar(self, user_id: UUID) -> bool:
        """
        Убирает флаг основного аватара у всех аватаров пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: Результат операции
        """
        try:
            await self.avatar_repo.clear_main_avatar(user_id)
            
            # ✅ Сбрасываем кеш списка аватаров
            await cache_service.delete(f"user_avatars:{user_id}")
            
            logger.info(f"Убран флаг основного аватара для всех аватаров пользователя {user_id}")
            return True
            
        except Exception as e:
            logger.exception(f"Ошибка при сбросе основного аватара для пользователя {user_id}: {e}")
            return False

    async def get_main_avatar(self, user_id: UUID) -> Optional[Avatar]:
        """
        Получает основной аватар пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[Avatar]: Основной аватар или None
        """
        try:
            return await self.avatar_repo.get_main_avatar(user_id)
        except Exception as e:
            logger.exception(f"Ошибка при получении основного аватара пользователя {user_id}: {e}")
            return None

    async def get_user_avatars_with_photos(self, user_id: UUID) -> List[Avatar]:
        """
        Получает все аватары пользователя с загруженными фотографиями
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Avatar]: Список аватаров с фотографиями
        """
        try:
            return await self.avatar_repo.get_user_avatars_with_photos(user_id)
        except Exception as e:
            logger.exception(f"Ошибка при получении аватаров с фотографиями для пользователя {user_id}: {e}")
            return [] 