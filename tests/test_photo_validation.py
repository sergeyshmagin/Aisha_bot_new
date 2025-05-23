"""
Тесты для системы валидации фотографий аватаров
"""

import pytest
import hashlib
import io
from uuid import uuid4
from PIL import Image

from app.services.avatar.photo_validation import PhotoValidationService, PhotoValidationResult
from app.database.models import AvatarPhoto


class TestPhotoValidationService:
    """Тесты для PhotoValidationService"""
    
    @pytest.fixture
    def validation_service(self, db_session):
        """Создает экземпляр сервиса валидации"""
        return PhotoValidationService(db_session)
    
    @pytest.fixture
    def valid_image_data(self):
        """Создает валидные данные изображения"""
        # Создаем изображение 512x512 в формате JPEG
        image = Image.new('RGB', (512, 512), color='red')
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        return buffer.getvalue()
    
    @pytest.fixture
    def small_image_data(self):
        """Создает маленькое изображение (меньше минимального размера)"""
        image = Image.new('RGB', (256, 256), color='blue')
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        return buffer.getvalue()
    
    @pytest.fixture
    def large_image_data(self):
        """Создает большое изображение"""
        image = Image.new('RGB', (4096, 4096), color='green')
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        return buffer.getvalue()
    
    @pytest.mark.asyncio
    async def test_validate_valid_photo(self, validation_service, valid_image_data):
        """Тест валидации корректного фото"""
        avatar_id = uuid4()
        
        result = await validation_service.validate_photo(
            valid_image_data, 
            avatar_id
        )
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert 'photo_hash' in result.metadata
        assert result.metadata['width'] == 512
        assert result.metadata['height'] == 512
        assert result.metadata['format'] == 'JPEG'
    
    @pytest.mark.asyncio
    async def test_validate_small_photo(self, validation_service, small_image_data):
        """Тест валидации маленького фото (должно быть отклонено)"""
        avatar_id = uuid4()
        
        result = await validation_service.validate_photo(
            small_image_data, 
            avatar_id
        )
        
        assert result.is_valid is False
        assert any("меньше минимального" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_large_photo(self, validation_service, large_image_data):
        """Тест валидации большого фото (должно пройти с предупреждением)"""
        avatar_id = uuid4()
        
        result = await validation_service.validate_photo(
            large_image_data, 
            avatar_id
        )
        
        # Большое фото должно пройти валидацию, но с предупреждением
        assert result.is_valid is True
        assert any("больше рекомендуемого" in warning for warning in result.warnings)
    
    @pytest.mark.asyncio
    async def test_validate_empty_file(self, validation_service):
        """Тест валидации пустого файла"""
        avatar_id = uuid4()
        
        result = await validation_service.validate_photo(
            b'', 
            avatar_id
        )
        
        assert result.is_valid is False
        assert any("пустой" in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_validate_invalid_format(self, validation_service):
        """Тест валидации неподдерживаемого формата"""
        avatar_id = uuid4()
        invalid_data = b'not an image'
        
        result = await validation_service.validate_photo(
            invalid_data, 
            avatar_id
        )
        
        assert result.is_valid is False
        assert any("неподдерживаемый" in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(self, validation_service, valid_image_data, db_session):
        """Тест детекции дубликатов по MD5"""
        avatar_id = uuid4()
        user_id = uuid4()
        
        # Создаем существующую фотографию в БД
        photo_hash = hashlib.md5(valid_image_data).hexdigest()
        existing_photo = AvatarPhoto(
            avatar_id=avatar_id,
            user_id=user_id,
            minio_key="test/path",
            file_hash=photo_hash,
            upload_order=1,
            file_size=len(valid_image_data)
        )
        db_session.add(existing_photo)
        await db_session.commit()
        
        # Пытаемся загрузить то же фото
        result = await validation_service.validate_photo(
            valid_image_data, 
            avatar_id
        )
        
        assert result.is_valid is False
        assert any("уже загружено" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_photo_limits(self, validation_service, valid_image_data, db_session):
        """Тест проверки лимитов количества фото"""
        avatar_id = uuid4()
        user_id = uuid4()
        
        # Создаем максимальное количество фото
        max_photos = validation_service.AVATAR_MAX_PHOTOS
        for i in range(max_photos):
            photo = AvatarPhoto(
                avatar_id=avatar_id,
                user_id=user_id,
                minio_key=f"test/path_{i}",
                file_hash=f"hash_{i}",
                upload_order=i + 1,
                file_size=1000
            )
            db_session.add(photo)
        await db_session.commit()
        
        # Пытаемся загрузить еще одно фото
        result = await validation_service.validate_photo(
            valid_image_data, 
            avatar_id
        )
        
        assert result.is_valid is False
        assert any("лимит" in error.lower() for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_quality_analysis(self, validation_service, valid_image_data):
        """Тест анализа качества изображения"""
        avatar_id = uuid4()
        
        result = await validation_service.validate_photo(
            valid_image_data, 
            avatar_id
        )
        
        assert result.is_valid is True
        assert 'quality_score' in result.metadata
        assert 'brightness' in result.metadata
        assert 'contrast' in result.metadata
        assert 0 <= result.metadata['quality_score'] <= 1
    
    def test_calculate_photo_hash(self, validation_service, valid_image_data):
        """Тест вычисления MD5 хеша"""
        hash1 = validation_service.calculate_photo_hash(valid_image_data)
        hash2 = validation_service.calculate_photo_hash(valid_image_data)
        
        # Хеши одинаковых данных должны совпадать
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 хеш в hex формате
        
        # Хеш должен совпадать с прямым вычислением
        expected_hash = hashlib.md5(valid_image_data).hexdigest()
        assert hash1 == expected_hash
    
    @pytest.mark.asyncio
    async def test_check_photo_duplicate_existing(self, validation_service, db_session):
        """Тест проверки существующего дубликата"""
        avatar_id = uuid4()
        user_id = uuid4()
        photo_hash = "test_hash_123"
        
        # Создаем фото в БД
        photo = AvatarPhoto(
            avatar_id=avatar_id,
            user_id=user_id,
            minio_key="test/path",
            file_hash=photo_hash,
            upload_order=1,
            file_size=1000
        )
        db_session.add(photo)
        await db_session.commit()
        
        # Проверяем дубликат
        is_duplicate = await validation_service.check_photo_duplicate(
            avatar_id, 
            photo_hash
        )
        
        assert is_duplicate is True
    
    @pytest.mark.asyncio
    async def test_check_photo_duplicate_not_existing(self, validation_service):
        """Тест проверки несуществующего дубликата"""
        avatar_id = uuid4()
        photo_hash = "non_existing_hash"
        
        is_duplicate = await validation_service.check_photo_duplicate(
            avatar_id, 
            photo_hash
        )
        
        assert is_duplicate is False
    
    @pytest.mark.asyncio
    async def test_metadata_collection(self, validation_service, valid_image_data):
        """Тест сбора метаданных изображения"""
        avatar_id = uuid4()
        
        result = await validation_service.validate_photo(
            valid_image_data, 
            avatar_id
        )
        
        assert result.is_valid is True
        
        # Проверяем наличие всех ожидаемых метаданных
        expected_keys = [
            'width', 'height', 'format', 'mode', 'file_size',
            'aspect_ratio', 'megapixels', 'photo_hash',
            'quality_score', 'brightness', 'contrast'
        ]
        
        for key in expected_keys:
            assert key in result.metadata, f"Отсутствует метаданное: {key}"
        
        # Проверяем корректность значений
        assert result.metadata['width'] == 512
        assert result.metadata['height'] == 512
        assert result.metadata['aspect_ratio'] == 1.0
        assert result.metadata['megapixels'] == pytest.approx(0.262, rel=1e-2) 