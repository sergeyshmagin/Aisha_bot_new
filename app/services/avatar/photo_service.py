"""
Сервис для работы с фотографиями аватаров
"""
import hashlib
import io
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload

from ...core.config import settings
from ...core.logger import get_logger
from ...database.models import Avatar, AvatarPhoto, PhotoValidationStatus
from ..base import BaseService
from ..storage import StorageService

logger = get_logger(__name__)# Импортируем PhotoValidationResult из нового модуля валидации
from .photo_validation import PhotoValidationResultclass PhotoUploadService(BaseService):
    """
    Сервис для загрузки и валидации фотографий аватаров.
    
    Функции:
    - Загрузка фотографий в MinIO
    - Валидация размера, формата, качества
    - Детекция дубликатов
    - Проверка наличия лиц (опционально)
    - Управление галереей фотографий
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.session = session
        self.storage = StorageService()

    async def upload_photo(
        self, 
        avatar_id: UUID, 
        user_id: UUID,
        photo_data: bytes,
        filename: Optional[str] = None
    ) -> AvatarPhoto:
        """
        Загружает фотографию для аватара
        
        Args:
            avatar_id: ID аватара
            user_id: ID пользователя
            photo_data: Данные фотографии
            filename: Имя файла (опционально)
            
        Returns:
            AvatarPhoto: Созданная запись фотографии
            
        Raises:
            ValueError: При ошибках валидации
        """
        try:
            # Валидируем фотографию
            validation = await self._validate_photo(photo_data, avatar_id)
            if not validation.is_valid:
                raise ValueError(f"Фото не прошло валидацию: {', '.join(validation.errors)}")
            
            # Проверяем лимиты
            await self._check_photo_limits(avatar_id)
            
            # Проверяем на дубликаты
            photo_hash = self._calculate_hash(photo_data)
            await self._check_duplicates(avatar_id, photo_hash)
            
            # Определяем порядок загрузки
            upload_order = await self._get_next_upload_order(avatar_id)
            
            # Создаем путь в MinIO
            file_extension = validation.metadata.get('format', 'jpg').lower()
            object_name = f"avatars/{user_id}/{avatar_id}/photo_{upload_order}.{file_extension}"
            
            # Загружаем в MinIO
            minio_path = await self.storage.upload_file(
                bucket="avatars",
                object_name=object_name,
                data=photo_data,
                content_type=f"image/{file_extension}"
            )
            
            # Создаем запись в БД
            photo = AvatarPhoto(
                avatar_id=avatar_id,
                user_id=user_id,
                minio_key=minio_path,
                file_hash=photo_hash,
                upload_order=upload_order,
                validation_status=PhotoValidationStatus.VALID,
                file_size=len(photo_data),
                width=validation.metadata.get('width'),
                height=validation.metadata.get('height'),
                format=file_extension,
                has_face=validation.metadata.get('has_face'),
                quality_score=validation.metadata.get('quality_score'),
                photo_metadata={
                    'original_filename': filename,
                    'validation_warnings': validation.warnings,
                    'upload_timestamp': datetime.utcnow().isoformat(),
                }
            )
            
            self.session.add(photo)
            await self.session.commit()
            await self.session.refresh(photo)
            
            # Обновляем счетчик фотографий в аватаре
            await self._update_avatar_photos_count(avatar_id)
            
            logger.info(
                f"Загружена фотография {photo.id} для аватара {avatar_id}: "
                f"size={len(photo_data)}, order={upload_order}"
            )
            
            return photo
            
        except Exception as e:
            await self.session.rollback()
            logger.exception(f"Ошибка при загрузке фотографии: {e}")
            raise

    async def get_avatar_photos(
        self, 
        avatar_id: UUID, 
        page: int = 1, 
        per_page: int = None
    ) -> Tuple[List[AvatarPhoto], int]:
        """
        Получает список фотографий аватара с пагинацией
        
        Args:
            avatar_id: ID аватара
            page: Номер страницы (начиная с 1)
            per_page: Количество фото на страницу
            
        Returns:
            Tuple[List[AvatarPhoto], int]: Список фотографий и общее количество
        """
        try:
            if per_page is None:
                per_page = settings.GALLERY_PHOTOS_PER_PAGE
                
            # Подсчитываем общее количество
            count_query = (
                select(func.count(AvatarPhoto.id))
                .where(AvatarPhoto.avatar_id == avatar_id)
            )
            result = await self.session.execute(count_query)
            total_count = result.scalar() or 0
            
            # Получаем фотографии с пагинацией
            offset = (page - 1) * per_page
            photos_query = (
                select(AvatarPhoto)
                .where(AvatarPhoto.avatar_id == avatar_id)
                .order_by(AvatarPhoto.upload_order)
                .offset(offset)
                .limit(per_page)
            )
            
            result = await self.session.execute(photos_query)
            photos = result.scalars().all()
            
            logger.debug(f"Получено {len(photos)} фотографий для аватара {avatar_id}, страница {page}")
            return photos, total_count
            
        except Exception as e:
            logger.exception(f"Ошибка при получении фотографий аватара {avatar_id}: {e}")
            raise

    async def delete_photo(self, photo_id: UUID, user_id: UUID) -> bool:
        """
        Удаляет фотографию (с проверкой прав)
        
        Args:
            photo_id: ID фотографии
            user_id: ID пользователя (для проверки прав)
            
        Returns:
            bool: True если удалено успешно
        """
        try:
            # Получаем фотографию с проверкой прав
            query = (
                select(AvatarPhoto)
                .where(
                    AvatarPhoto.id == photo_id,
                    AvatarPhoto.user_id == user_id
                )
            )
            result = await self.session.execute(query)
            photo = result.scalar_one_or_none()
            
            if not photo:
                logger.warning(f"Попытка удалить чужую фотографию {photo_id} пользователем {user_id}")
                return False
            
            # Удаляем из MinIO
            try:
                await self.storage.delete_file("avatars", photo.minio_key)
            except Exception as e:
                logger.warning(f"Ошибка при удалении файла из MinIO {photo.minio_key}: {e}")
            
            # Удаляем из БД
            avatar_id = photo.avatar_id
            await self.session.delete(photo)
            await self.session.commit()
            
            # Обновляем счетчик фотографий
            await self._update_avatar_photos_count(avatar_id)
            
            logger.info(f"Удалена фотография {photo_id} пользователя {user_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.exception(f"Ошибка при удалении фотографии {photo_id}: {e}")
            raise

    async def get_photo_by_id(self, photo_id: UUID) -> Optional[AvatarPhoto]:
        """
        Получает фотографию по ID
        
        Args:
            photo_id: ID фотографии
            
        Returns:
            Optional[AvatarPhoto]: Фотография или None
        """
        try:
            query = select(AvatarPhoto).where(AvatarPhoto.id == photo_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.exception(f"Ошибка при получении фотографии {photo_id}: {e}")
            raise

    async def get_photo_data(self, photo_id: UUID) -> Optional[bytes]:
        """
        Получает данные фотографии из MinIO
        
        Args:
            photo_id: ID фотографии
            
        Returns:
            Optional[bytes]: Данные фотографии или None
        """
        try:
            photo = await self.get_photo_by_id(photo_id)
            if not photo:
                return None
                
            # Загружаем из MinIO
            data = await self.storage.download_file("avatars", photo.minio_key)
            return data
            
        except Exception as e:
            logger.exception(f"Ошибка при получении данных фотографии {photo_id}: {e}")
            raise

    async def _validate_photo(self, photo_data: bytes, avatar_id: UUID) -> PhotoValidationResult:
        """
        Валидирует фотографию с использованием улучшенного валидатора
        
        Args:
            photo_data: Данные фотографии
            avatar_id: ID аватара
            
        Returns:
            PhotoValidationResult: Результат валидации
        """
        # Используем новый улучшенный валидатор из legacy проекта
        from .photo_validation import PhotoValidationService
        
        validator = PhotoValidationService(self.session)
        return await validator.validate_photo(photo_data, avatar_id)

    async def _check_photo_limits(self, avatar_id: UUID) -> None:
        """
        Проверяет лимиты фотографий для аватара
        
        Args:
            avatar_id: ID аватара
            
        Raises:
            ValueError: При превышении лимитов
        """
        count_query = (
            select(func.count(AvatarPhoto.id))
            .where(AvatarPhoto.avatar_id == avatar_id)
        )
        result = await self.session.execute(count_query)
        photos_count = result.scalar() or 0
        
        if photos_count >= settings.AVATAR_MAX_PHOTOS:
            raise ValueError(
                f"Превышен лимит фотографий: {photos_count}/{settings.AVATAR_MAX_PHOTOS}"
            )

    async def _check_duplicates(self, avatar_id: UUID, photo_hash: str) -> None:
        """
        Проверяет на дубликаты фотографий используя PhotoValidationService
        
        Args:
            avatar_id: ID аватара
            photo_hash: Хеш фотографии
            
        Raises:
            ValueError: При обнаружении дубликата
        """
        # РЕФАКТОРИНГ: Используем PhotoValidationService вместо дублирования логики
        from .photo_validation import PhotoValidationService
        
        validator = PhotoValidationService(self.session)
        
        # Создаем фиктивные данные для проверки дубликата
        result = PhotoValidationResult(is_valid=True)
        result.metadata['photo_hash'] = photo_hash
        
        # Используем существующий метод валидации
        await validator._validate_duplicates(b'', avatar_id, result)
        
        if not result.is_valid:
            raise ValueError("Такая фотография уже была загружена")

    async def _get_next_upload_order(self, avatar_id: UUID) -> int:
        """
        Получает следующий порядковый номер для загрузки
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            int: Следующий порядковый номер
        """
        max_order_query = (
            select(func.max(AvatarPhoto.upload_order))
            .where(AvatarPhoto.avatar_id == avatar_id)
        )
        result = await self.session.execute(max_order_query)
        max_order = result.scalar() or 0
        
        return max_order + 1

    async def _update_avatar_photos_count(self, avatar_id: UUID) -> None:
        """
        Обновляет счетчик фотографий в аватаре
        
        Args:
            avatar_id: ID аватара
        """
        count_query = (
            select(func.count(AvatarPhoto.id))
            .where(AvatarPhoto.avatar_id == avatar_id)
        )
        result = await self.session.execute(count_query)
        photos_count = result.scalar() or 0
        
        stmt = (
            update(Avatar)
            .where(Avatar.id == avatar_id)
            .values(photos_count=photos_count, updated_at=datetime.utcnow())
        )
        
        await self.session.execute(stmt)
        await self.session.commit()

    def _calculate_hash(self, data: bytes) -> str:
        """
        Вычисляет MD5 хеш данных
        
        Args:
            data: Данные для хеширования
            
        Returns:
            str: MD5 хеш в hex формате
        """
        return hashlib.md5(data).hexdigest()
