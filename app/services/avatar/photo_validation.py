"""
Улучшенная система валидации фотографий для аватаров
Перенесена из legacy проекта и дополнена новыми возможностями
"""

import hashlib
import io
import mimetypes
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from PIL import Image, ImageStat
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ...core.config import settings
from ...core.logger import get_logger
from ...database.models import AvatarPhoto

logger = get_logger(__name__)@dataclass
class PhotoValidationResult:
    """Результат валидации фотографии"""
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}class PhotoValidationService:
    """
    Сервис валидации фотографий аватаров с функциями из legacy проекта:
    
    ✅ Проверка минимального размера изображения (512x512)
    ✅ Проверка максимального размера файла (20MB)
    ✅ Детекция дубликатов по MD5 хешу
    ✅ Валидация формата файла
    ✅ Проверка качества изображения
    ✅ Анализ содержимого (яркость, контраст)
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Настройки из legacy проекта
        self.PHOTO_MIN_RESOLUTION = getattr(settings, 'PHOTO_MIN_RESOLUTION', 512)
        self.PHOTO_MAX_RESOLUTION = getattr(settings, 'PHOTO_MAX_RESOLUTION', 2048)
        self.PHOTO_MAX_SIZE = getattr(settings, 'PHOTO_MAX_SIZE', 20 * 1024 * 1024)  # 20MB
        self.ALLOWED_FORMATS = getattr(settings, 'PHOTO_ALLOWED_FORMATS', ['JPEG', 'PNG', 'JPG'])
        self.AVATAR_MAX_PHOTOS = getattr(settings, 'AVATAR_MAX_PHOTOS', 20)
        self.QUALITY_THRESHOLD = getattr(settings, 'QUALITY_THRESHOLD', 0.3)
    
    async def validate_photo(
        self, 
        photo_data: bytes, 
        avatar_id: UUID,
        filename: Optional[str] = None
    ) -> PhotoValidationResult:
        """
        Полная валидация фотографии с проверками из legacy проекта
        
        Args:
            photo_data: Данные фотографии
            avatar_id: ID аватара
            filename: Имя файла (опционально)
            
        Returns:
            PhotoValidationResult: Результат валидации
        """
        result = PhotoValidationResult(is_valid=True)
        
        try:
            # 1. Базовые проверки размера файла
            self._validate_file_size(photo_data, result)
            
            # 2. Проверка MIME типа
            self._validate_mime_type(photo_data, filename, result)
            
            # 3. Анализ изображения через PIL
            image = self._load_image(photo_data, result)
            if image is None:
                return result
            
            # 4. Проверка разрешения
            self._validate_resolution(image, result)
            
            # 5. Проверка формата
            self._validate_format(image, result)
            
            # 6. Проверка дубликатов по MD5
            await self._validate_duplicates(photo_data, avatar_id, result)
            
            # 7. Проверка лимитов количества фото
            await self._validate_photo_limits(avatar_id, result)
            
            # 8. Анализ качества изображения
            self._analyze_image_quality(image, result)
            
            # 9. Сохраняем метаданные
            self._collect_metadata(image, photo_data, result)
            
            logger.info(
                f"Валидация фото завершена: valid={result.is_valid}, "
                f"errors={len(result.errors)}, warnings={len(result.warnings)}"
            )
            
        except Exception as e:
            logger.exception(f"Ошибка при валидации фотографии: {e}")
            result.is_valid = False
            result.errors.append(f"Внутренняя ошибка валидации: {str(e)}")
        
        return result
    
    def _validate_file_size(self, photo_data: bytes, result: PhotoValidationResult) -> None:
        """Проверка размера файла (из legacy)"""
        file_size = len(photo_data)
        
        if file_size == 0:
            result.is_valid = False
            result.errors.append("Файл пустой")
            return
        
        if file_size > self.PHOTO_MAX_SIZE:
            result.is_valid = False
            result.errors.append(
                f"Размер файла {file_size / 1024 / 1024:.1f}MB превышает лимит "
                f"{self.PHOTO_MAX_SIZE / 1024 / 1024}MB"
            )
        
        # Предупреждение для маленьких файлов
        if file_size < 50 * 1024:  # 50KB
            result.warnings.append("Файл очень маленький, качество может быть низким")
    
    def _validate_mime_type(
        self, 
        photo_data: bytes, 
        filename: Optional[str], 
        result: PhotoValidationResult
    ) -> None:
        """Проверка MIME типа"""
        # Проверяем магические байты
        if photo_data.startswith(b'\xff\xd8\xff'):
            mime_type = 'image/jpeg'
        elif photo_data.startswith(b'\x89PNG\r\n\x1a\n'):
            mime_type = 'image/png'
        elif photo_data.startswith(b'WEBP', 8):
            mime_type = 'image/webp'
        else:
            # Попытка определить через mimetypes
            if filename:
                mime_type, _ = mimetypes.guess_type(filename)
            else:
                mime_type = None
        
        if not mime_type or not mime_type.startswith('image/'):
            result.is_valid = False
            result.errors.append("Неподдерживаемый тип файла")
    
    def _load_image(self, photo_data: bytes, result: PhotoValidationResult) -> Optional[Image.Image]:
        """Загрузка изображения через PIL"""
        try:
            image = Image.open(io.BytesIO(photo_data))
            # Убеждаемся что изображение загружено
            image.load()
            return image
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"Ошибка при открытии изображения: {str(e)}")
            return None
    
    def _validate_resolution(self, image: Image.Image, result: PhotoValidationResult) -> None:
        """Проверка разрешения (из legacy проекта)"""
        width, height = image.size
        min_dimension = min(width, height)
        max_dimension = max(width, height)
        
        # Минимальное разрешение (критичная ошибка)
        if min_dimension < self.PHOTO_MIN_RESOLUTION:
            result.is_valid = False
            result.errors.append(
                f"Разрешение {width}x{height} меньше минимального "
                f"{self.PHOTO_MIN_RESOLUTION}x{self.PHOTO_MIN_RESOLUTION}"
            )
        
        # Максимальное разрешение (предупреждение)
        if max_dimension > self.PHOTO_MAX_RESOLUTION:
            result.warnings.append(
                f"Разрешение {width}x{height} больше рекомендуемого "
                f"{self.PHOTO_MAX_RESOLUTION}x{self.PHOTO_MAX_RESOLUTION}"
            )
        
        # Проверка соотношения сторон
        aspect_ratio = max_dimension / min_dimension
        if aspect_ratio > 3:  # Слишком вытянутое изображение
            result.warnings.append(
                f"Необычное соотношение сторон: {aspect_ratio:.1f}:1"
            )
    
    def _validate_format(self, image: Image.Image, result: PhotoValidationResult) -> None:
        """Проверка формата изображения"""
        format_name = image.format
        if not format_name:
            result.is_valid = False
            result.errors.append("Не удалось определить формат изображения")
            return
        
        # Нормализуем название формата
        if format_name.upper() == 'JPEG':
            format_name = 'JPG'
        
        if format_name.upper() not in [f.upper() for f in self.ALLOWED_FORMATS]:
            result.is_valid = False
            result.errors.append(
                f"Неподдерживаемый формат: {format_name}. "
                f"Разрешены: {', '.join(self.ALLOWED_FORMATS)}"
            )
    
    async def _validate_duplicates(
        self, 
        photo_data: bytes, 
        avatar_id: UUID, 
        result: PhotoValidationResult
    ) -> None:
        """Проверка дубликатов по MD5 хешу (из legacy проекта)"""
        photo_hash = hashlib.md5(photo_data).hexdigest()
        result.metadata['photo_hash'] = photo_hash
        
        try:
            # Ищем фото с таким же хешем в этом аватаре
            query = (
                select(AvatarPhoto.id)
                .where(
                    AvatarPhoto.avatar_id == avatar_id,
                    AvatarPhoto.file_hash == photo_hash
                )
            )
            
            result_db = await self.session.execute(query)
            existing = result_db.scalar_one_or_none()
            
            if existing:
                result.is_valid = False
                result.errors.append(
                    "Это фото уже загружено. Пожалуйста, загрузите другое фото."
                )
                logger.warning(f"Найден дубликат фото по MD5: {photo_hash}")
        
        except Exception as e:
            logger.exception(f"Ошибка при проверке дубликатов: {e}")
            result.warnings.append("Не удалось проверить дубликаты")
    
    async def _validate_photo_limits(self, avatar_id: UUID, result: PhotoValidationResult) -> None:
        """Проверка лимитов количества фото (из legacy проекта)"""
        try:
            count_query = (
                select(func.count(AvatarPhoto.id))
                .where(AvatarPhoto.avatar_id == avatar_id)
            )
            count_result = await self.session.execute(count_query)
            photos_count = count_result.scalar() or 0
            
            if photos_count >= self.AVATAR_MAX_PHOTOS:
                result.is_valid = False
                result.errors.append(
                    f"Достигнут лимит в {self.AVATAR_MAX_PHOTOS} фотографий"
                )
            elif photos_count >= self.AVATAR_MAX_PHOTOS * 0.8:
                # Предупреждение при приближении к лимиту
                result.warnings.append(
                    f"Загружено {photos_count} из {self.AVATAR_MAX_PHOTOS} фото"
                )
        
        except Exception as e:
            logger.exception(f"Ошибка при проверке лимитов: {e}")
            result.warnings.append("Не удалось проверить лимиты")
    
    def _analyze_image_quality(self, image: Image.Image, result: PhotoValidationResult) -> None:
        """Анализ качества изображения (улучшенная версия из legacy)"""
        try:
            # Конвертируем в RGB если нужно
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Анализ статистики изображения
            stat = ImageStat.Stat(image)
            
            # Средняя яркость (0-255)
            brightness = sum(stat.mean) / len(stat.mean)
            result.metadata['brightness'] = brightness
            
            # Стандартное отклонение (контраст)
            contrast = sum(stat.stddev) / len(stat.stddev)
            result.metadata['contrast'] = contrast
            
            # Оценка качества на основе размера и метрик
            width, height = image.size
            min_dimension = min(width, height)
            
            # Базовая оценка по разрешению
            resolution_score = min(1.0, min_dimension / self.PHOTO_MIN_RESOLUTION)
            
            # Оценка по контрасту (хорошие фото имеют контраст > 20)
            contrast_score = min(1.0, contrast / 30.0)
            
            # Оценка по яркости (избегаем слишком темных/светлых)
            brightness_score = 1.0 - abs(brightness - 128) / 128
            
            # Итоговая оценка качества
            quality_score = (resolution_score * 0.5 + contrast_score * 0.3 + brightness_score * 0.2)
            result.metadata['quality_score'] = quality_score
            
            # Предупреждения по качеству
            if quality_score < self.QUALITY_THRESHOLD:
                result.warnings.append(f"Низкое качество изображения: {quality_score:.2f}")
            
            if brightness < 30:
                result.warnings.append("Изображение слишком темное")
            elif brightness > 220:
                result.warnings.append("Изображение слишком светлое")
            
            if contrast < 15:
                result.warnings.append("Низкий контраст изображения")
            
        except Exception as e:
            logger.exception(f"Ошибка при анализе качества: {e}")
            result.warnings.append("Не удалось проанализировать качество")
    
    def _collect_metadata(
        self, 
        image: Image.Image, 
        photo_data: bytes, 
        result: PhotoValidationResult
    ) -> None:
        """Сбор метаданных изображения"""
        width, height = image.size
        
        result.metadata.update({
            'width': width,
            'height': height,
            'format': image.format,
            'mode': image.mode,
            'file_size': len(photo_data),
            'aspect_ratio': width / height,
            'megapixels': (width * height) / 1_000_000,
        })
        
        # EXIF данные (если есть)
        try:
            if hasattr(image, '_getexif') and image._getexif():
                exif_data = image._getexif()
                if exif_data:
                    # Извлекаем только безопасные EXIF теги
                    safe_exif = {}
                    if 271 in exif_data:  # Make
                        safe_exif['camera_make'] = str(exif_data[271])[:50]
                    if 272 in exif_data:  # Model
                        safe_exif['camera_model'] = str(exif_data[272])[:50]
                    
                    result.metadata['exif'] = safe_exif
        except Exception:
            # EXIF данные не критичны
            pass

    def calculate_photo_hash(self, photo_data: bytes) -> str:
        """Вычисляет MD5 хеш фотографии (из legacy проекта)"""
        return hashlib.md5(photo_data).hexdigest()

    # УДАЛЕН: check_photo_duplicate() - дублирует функциональность _validate_duplicates()
    # Используйте _validate_duplicates() вместо этого метода
