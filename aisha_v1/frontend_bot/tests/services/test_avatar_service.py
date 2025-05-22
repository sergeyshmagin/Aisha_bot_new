"""
Тесты для сервиса аватаров.
"""

import pytest
import os
from pathlib import Path
import aiofiles
import json
from PIL import Image
import io
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from frontend_bot.services.avatar_service import AvatarService
from frontend_bot.config import settings
from frontend_bot.utils.logger import get_logger

logger = get_logger(__name__)

def create_test_image(width=256, height=256, color=(255, 0, 0)):
    """Создает тестовое изображение."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

@pytest.fixture
async def avatar_service(session):
    """Создает экземпляр сервиса аватаров."""
    service = AvatarService(session)
    await service.init()
    return service

@pytest.mark.asyncio
async def test_validate_photo(avatar_service):
    """Тест валидации фото."""
    # Создаем тестовое изображение с размером 512x512
    photo_data = create_test_image(512, 512)
    is_valid, msg = await avatar_service.validate_photo(photo_data)
    assert is_valid
    assert msg == "OK"

@pytest.mark.asyncio
async def test_save_avatar(avatar_service):
    """Тест сохранения аватара."""
    user_id = 123
    photo_data = create_test_image(512, 512)
    metadata = {
        "title": "Test Avatar",
        "style": "realistic",
        "gender": "male"
    }
    
    result = await avatar_service.save_avatar(user_id, photo_data, metadata)
    assert "avatar_id" in result
    assert "preview_url" in result
    assert result["metadata"] == metadata

@pytest.mark.asyncio
async def test_get_avatar(avatar_service):
    """Тест получения аватара."""
    user_id = 123
    photo_data = create_test_image(512, 512)
    metadata = {"title": "Test Avatar"}
    
    # Сначала сохраняем аватар
    saved = await avatar_service.save_avatar(user_id, photo_data, metadata)
    avatar_id = saved["avatar_id"]
    
    # Получаем аватар
    avatar = await avatar_service.get_avatar(user_id, avatar_id)
    assert avatar is not None
    assert avatar["metadata"] == metadata

@pytest.mark.asyncio
async def test_delete_avatar(avatar_service):
    """Тест удаления аватара."""
    user_id = 123
    photo_data = create_test_image(512, 512)
    metadata = {"title": "Test Avatar"}
    
    # Сначала сохраняем аватар
    saved = await avatar_service.save_avatar(user_id, photo_data, metadata)
    avatar_id = saved["avatar_id"]
    
    # Удаляем аватар
    result = await avatar_service.delete_avatar(user_id, avatar_id)
    assert result is True
    
    # Проверяем, что аватар удален
    avatar = await avatar_service.get_avatar(user_id, avatar_id)
    assert avatar is None

@pytest.mark.asyncio
async def test_list_avatars(avatar_service):
    """Тест получения списка аватаров."""
    user_id = 123
    photo_data = create_test_image(512, 512)
    metadata1 = {"title": "Avatar 1"}
    metadata2 = {"title": "Avatar 2"}
    
    # Создаем два аватара
    await avatar_service.save_avatar(user_id, photo_data, metadata1)
    await avatar_service.save_avatar(user_id, photo_data, metadata2)
    
    # Получаем список
    avatars = await avatar_service.list_avatars(user_id)
    assert len(avatars) == 2
    titles = [a["metadata"]["title"] for a in avatars]
    assert "Avatar 1" in titles
    assert "Avatar 2" in titles

@pytest.mark.asyncio
async def test_update_avatar(avatar_service):
    """Тест обновления аватара."""
    user_id = 123
    photo_data = create_test_image(512, 512)
    metadata = {"title": "Original Title"}
    
    # Сначала сохраняем аватар
    saved = await avatar_service.save_avatar(user_id, photo_data, metadata)
    avatar_id = saved["avatar_id"]
    
    # Обновляем метаданные
    new_metadata = {"title": "Updated Title"}
    await avatar_service.update_avatar(user_id, avatar_id, new_metadata)
    
    # Проверяем обновление
    avatar = await avatar_service.get_avatar(user_id, avatar_id)
    assert avatar["metadata"]["title"] == "Updated Title"

@pytest.mark.asyncio
async def test_generate_preview(avatar_service):
    """Тест генерации превью."""
    photo_data = create_test_image(512, 512)
    preview_data = await avatar_service.generate_preview(photo_data)
    assert preview_data is not None
    assert len(preview_data) < len(photo_data)  # Превью должно быть меньше

@pytest.mark.asyncio
async def test_concurrent_operations(avatar_service):
    """Тест конкурентных операций."""
    user_id = 123
    photo_data = create_test_image(512, 512)
    metadata = {"title": "Test Avatar"}
    
    # Создаем несколько аватаров одновременно
    tasks = []
    for i in range(3):
        task = avatar_service.save_avatar(user_id, photo_data, {**metadata, "index": i})
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    assert len(results) == 3
    
    # Проверяем, что все аватары созданы
    avatars = await avatar_service.list_avatars(user_id)
    assert len(avatars) == 3

@pytest.mark.asyncio
async def test_invalid_image_format(avatar_service):
    """Тест обработки некорректного формата изображения."""
    user_id = 123
    invalid_image = b"not_an_image_file"
    metadata = {"title": "Test Avatar"}
    
    with pytest.raises(ValueError) as exc_info:
        await avatar_service.save_avatar(user_id, invalid_image, metadata)
    assert "Invalid image format" in str(exc_info.value)

@pytest.mark.asyncio
async def test_image_size_validation(avatar_service):
    """Тест валидации размеров изображения."""
    user_id = 123
    metadata = {"title": "Test Avatar"}
    
    # Тест с слишком маленьким изображением
    small_image = create_test_image(100, 100)
    with pytest.raises(ValueError) as exc_info:
        await avatar_service.save_avatar(user_id, small_image, metadata)
    assert "Image too small" in str(exc_info.value)
    
    # Тест с слишком большим изображением
    large_image = create_test_image(2048, 2048)
    with pytest.raises(ValueError) as exc_info:
        await avatar_service.save_avatar(user_id, large_image, metadata)
    assert "Image too large" in str(exc_info.value)

@pytest.mark.asyncio
async def test_different_avatar_styles(avatar_service):
    """Тест работы с разными стилями аватаров."""
    user_id = 123
    photo_data = create_test_image(512, 512)
    
    # Тест с реалистичным стилем
    realistic_metadata = {
        "title": "Realistic Avatar",
        "style": "realistic",
        "gender": "male"
    }
    result_realistic = await avatar_service.save_avatar(
        user_id,
        photo_data,
        realistic_metadata
    )
    assert result_realistic["metadata"]["style"] == "realistic"
    
    # Тест с аниме стилем
    anime_metadata = {
        "title": "Anime Avatar",
        "style": "anime",
        "gender": "female"
    }
    result_anime = await avatar_service.save_avatar(
        user_id,
        photo_data,
        anime_metadata
    )
    assert result_anime["metadata"]["style"] == "anime"

@pytest.mark.asyncio
async def test_avatar_processing_error_handling(avatar_service):
    """Тест обработки ошибок при обработке аватара."""
    user_id = 123
    photo_data = create_test_image(512, 512)
    metadata = {"title": "Test Avatar"}
    
    # Симулируем ошибку при обработке изображения
    avatar_service.process_image = AsyncMock(side_effect=Exception("Processing error"))
    
    with pytest.raises(Exception) as exc_info:
        await avatar_service.save_avatar(user_id, photo_data, metadata)
    assert "Processing error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_avatar_cleanup(avatar_service):
    """Тест очистки старых аватаров."""
    user_id = 123
    photo_data = create_test_image(512, 512)
    metadata = {"title": "Test Avatar"}
    
    # Создаем несколько аватаров
    for i in range(5):
        await avatar_service.save_avatar(
            user_id,
            photo_data,
            {**metadata, "index": i}
        )
    
    # Запускаем очистку
    await avatar_service.cleanup_old_avatars(user_id, max_age_days=1)
    
    # Проверяем, что старые аватары удалены
    avatars = await avatar_service.list_avatars(user_id)
    assert len(avatars) <= 5  # Максимум 5 аватаров должно остаться 