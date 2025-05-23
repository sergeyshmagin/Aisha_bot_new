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

logger = get_logger(__name__)


class PhotoValidationResult:
    """Результат валидации фотографии"""
    
    def __init__(self, is_valid: bool, errors: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings: List[str] = []
        self.metadata: Dict[str, Any] = {}


class PhotoUploadService(BaseService):
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
        super().__init__()
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
            validation = await self._validate_photo(photo_data)
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

    async def _validate_photo(self, photo_data: bytes) -> PhotoValidationResult:
        """
        Валидирует фотографию
        
        Args:
            photo_data: Данные фотографии
            
        Returns:
            PhotoValidationResult: Результат валидации
        """
        result = PhotoValidationResult(is_valid=True)
        
        try:
            # Проверяем размер файла
            if len(photo_data) > settings.PHOTO_MAX_SIZE:
                result.is_valid = False
                result.errors.append(
                    f"Размер файла {len(photo_data)} байт превышает лимит {settings.PHOTO_MAX_SIZE}"
                )
            
            # Анализируем изображение с помощью PIL
            try:
                image = Image.open(io.BytesIO(photo_data))
                width, height = image.size
                format_name = image.format.lower() if image.format else 'unknown'
                
                result.metadata.update({
                    'width': width,
                    'height': height,
                    'format': format_name,
                    'mode': image.mode,
                })
                
                # Проверяем формат
                if format_name not in [f.lower() for f in settings.PHOTO_ALLOWED_FORMATS]:
                    result.is_valid = False
                    result.errors.append(f"Неподдерживаемый формат: {format_name}")
                
                # Проверяем разрешение
                min_dimension = min(width, height)
                if min_dimension < settings.PHOTO_MIN_RESOLUTION:
                    result.is_valid = False
                    result.errors.append(
                        f"Разрешение {width}x{height} меньше минимального {settings.PHOTO_MIN_RESOLUTION}"
                    )
                
                max_dimension = max(width, height)
                if max_dimension > settings.PHOTO_MAX_RESOLUTION:
                    result.warnings.append(
                        f"Разрешение {width}x{height} больше рекомендуемого {settings.PHOTO_MAX_RESOLUTION}"
                    )
                
                # TODO: Добавить детекцию лиц и NSFW контента
                if settings.ENABLE_FACE_DETECTION:
                    # Заглушка для детекции лиц
                    result.metadata['has_face'] = True  # Пока всегда True
                
                # Простая оценка качества (на основе размера и разрешения)
                quality_score = min(1.0, (min_dimension / settings.PHOTO_MIN_RESOLUTION) * 0.5 + 0.5)
                result.metadata['quality_score'] = quality_score
                
                if quality_score < settings.QUALITY_THRESHOLD:
                    result.warnings.append(f"Низкое качество изображения: {quality_score:.2f}")
                
            except Exception as e:
                result.is_valid = False
                result.errors.append(f"Ошибка анализа изображения: {str(e)}")
            
        except Exception as e:
            logger.exception(f"Ошибка валидации фотографии: {e}")
            result.is_valid = False
            result.errors.append(f"Внутренняя ошибка валидации: {str(e)}")
        
        return result

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
        Проверяет на дубликаты фотографий
        
        Args:
            avatar_id: ID аватара
            photo_hash: Хеш фотографии
            
        Raises:
            ValueError: При обнаружении дубликата
        """
        existing_query = (
            select(AvatarPhoto.id)
            .where(
                AvatarPhoto.avatar_id == avatar_id,
                AvatarPhoto.file_hash == photo_hash
            )
        )
        result = await self.session.execute(existing_query)
        existing = result.scalar_one_or_none()
        
        if existing:
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