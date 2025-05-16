"""
Тесты для менеджера аватаров.
"""

import pytest
import os
from pathlib import Path
import aiofiles
import json
from frontend_bot.services.avatar_manager import (
    ensure_avatar_dirs,
    get_user_avatar_dir,
    save_avatar_photo,
    get_user_avatar_photos,
    clear_user_avatar_photos
)
from frontend_bot.shared.file_operations import AsyncFileManager
from frontend_bot.shared.image_processing import AsyncImageProcessor
from frontend_bot.config import PHOTO_MIN_RES, PHOTO_MAX_MB

@pytest.fixture
def temp_dir(tmp_path):
    """Создает временную директорию для тестов."""
    return tmp_path

@pytest.fixture
async def setup_avatar_dirs(temp_dir):
    """Создает необходимые директории для тестов."""
    await ensure_avatar_dirs(temp_dir)
    return temp_dir

@pytest.mark.asyncio
async def test_ensure_avatar_dirs(temp_dir):
    """Тест создания директорий."""
    await ensure_avatar_dirs(temp_dir)
    assert os.path.exists(temp_dir / "avatars")

@pytest.mark.asyncio
async def test_get_user_avatar_dir(temp_dir):
    """Тест получения директории пользователя."""
    user_dir = await get_user_avatar_dir("123", temp_dir)
    assert os.path.exists(user_dir)
    assert str(user_dir).endswith("123")

@pytest.mark.asyncio
async def test_save_avatar_photo(temp_dir):
    """Тест сохранения фото."""
    photo_data = b"test_photo_data"
    photo_id = "test_photo"
    photo_path = await save_avatar_photo("123", photo_data, photo_id, temp_dir)
    assert os.path.exists(photo_path)
    assert photo_path.name == f"{photo_id}.jpg"

@pytest.mark.asyncio
async def test_get_user_avatar_photos(temp_dir):
    """Тест получения списка фото."""
    # Создаем тестовые фото
    await save_avatar_photo("123", b"photo1", "photo1", temp_dir)
    await save_avatar_photo("123", b"photo2", "photo2", temp_dir)
    
    photos = await get_user_avatar_photos("123", temp_dir)
    assert len(photos) == 2
    assert all(p.name.endswith(".jpg") for p in photos)

@pytest.mark.asyncio
async def test_clear_user_avatar_photos(temp_dir):
    """Тест очистки фото пользователя."""
    # Создаем тестовые фото
    await save_avatar_photo("123", b"photo1", "photo1", temp_dir)
    await save_avatar_photo("123", b"photo2", "photo2", temp_dir)
    
    await clear_user_avatar_photos("123", temp_dir)
    photos = await get_user_avatar_photos("123", temp_dir)
    assert len(photos) == 0

@pytest.mark.asyncio
async def test_state_management(avatar_manager):
    """Тест управления состоянием."""
    user_id = "123"
    test_state = {
        "photos": ["photo1.jpg", "photo2.jpg"],
        "title": "Test Avatar",
        "status": "pending"
    }
    
    # Устанавливаем состояние
    await avatar_manager.set_state(user_id, test_state)
    
    # Получаем состояние
    state = await avatar_manager.get_state(user_id)
    assert state == test_state
    
    # Очищаем состояние
    await avatar_manager.clear_state(user_id)
    state = await avatar_manager.get_state(user_id)
    assert state is None

@pytest.mark.asyncio
async def test_cleanup_state(avatar_manager):
    """Тест полной очистки данных пользователя."""
    user_id = "123"
    test_state = {"photos": ["photo1.jpg"]}
    photo_data = b"test photo"
    
    # Сохраняем состояние и фото
    await avatar_manager.set_state(user_id, test_state)
    await avatar_manager.save_photo(user_id, photo_data, "photo1")
    
    # Очищаем все данные
    await avatar_manager.cleanup_state(user_id)
    
    # Проверяем, что все удалено
    state = await avatar_manager.get_state(user_id)
    photos = await avatar_manager.get_user_photos(user_id)
    assert state is None
    assert len(photos) == 0

@pytest.mark.asyncio
async def test_validate_photo(avatar_manager):
    """Тест валидации фото."""
    # Создаем тестовое изображение
    img = await AsyncImageProcessor.create_test_image(
        width=PHOTO_MIN_RES,
        height=PHOTO_MIN_RES,
        format="JPEG"
    )
    photo_bytes = await AsyncImageProcessor.image_to_bytes(img)
    
    # Проверяем валидное фото
    is_valid, photo_hash = await avatar_manager.validate_photo(
        photo_bytes,
        existing_photo_paths=[],
        min_size=(PHOTO_MIN_RES, PHOTO_MIN_RES),
        max_mb=PHOTO_MAX_MB
    )
    assert is_valid
    assert photo_hash is not None
    
    # Проверяем слишком маленькое фото
    small_img = await AsyncImageProcessor.create_test_image(
        width=PHOTO_MIN_RES - 1,
        height=PHOTO_MIN_RES - 1,
        format="JPEG"
    )
    small_photo_bytes = await AsyncImageProcessor.image_to_bytes(small_img)
    is_valid, error = await avatar_manager.validate_photo(
        small_photo_bytes,
        existing_photo_paths=[],
        min_size=(PHOTO_MIN_RES, PHOTO_MIN_RES),
        max_mb=PHOTO_MAX_MB
    )
    assert not is_valid
    assert "маленькое" in error

@pytest.mark.asyncio
async def test_generate_avatar_preview(avatar_manager):
    """Тест генерации превью аватара."""
    # Создаем тестовое изображение
    img = await AsyncImageProcessor.create_test_image(
        width=1024,
        height=1024,
        format="JPEG"
    )
    photo_bytes = await AsyncImageProcessor.image_to_bytes(img)
    
    # Сохраняем фото
    user_id = "123"
    photo_path = await avatar_manager.save_photo(user_id, photo_bytes, "test_photo")
    
    # Генерируем превью
    preview_path = photo_path.parent / "preview.jpg"
    generated_preview = await avatar_manager.generate_avatar_preview(
        photo_path,
        preview_path,
        size=(256, 256)
    )
    
    # Проверяем превью
    assert await AsyncFileManager.exists(generated_preview)
    preview_img = await AsyncImageProcessor.open(await AsyncFileManager.read_binary(generated_preview))
    assert preview_img.size == (256, 256)

@pytest.mark.asyncio
async def test_concurrent_operations(avatar_manager):
    """Тест конкурентных операций."""
    import asyncio
    
    async def save_photo_and_state(user_id, photo_id, content):
        await avatar_manager.save_photo(user_id, content, photo_id)
        await avatar_manager.set_state(user_id, {"photo_id": photo_id})
    
    # Выполняем конкурентные операции
    user_id = "123"
    tasks = [
        save_photo_and_state(user_id, f"photo{i}", f"content{i}".encode())
        for i in range(5)
    ]
    await asyncio.gather(*tasks)
    
    # Проверяем результаты
    photos = await avatar_manager.get_user_photos(user_id)
    state = await avatar_manager.get_state(user_id)
    assert len(photos) == 5
    assert state["photo_id"] == "photo4"  # Последнее значение 

@pytest.mark.asyncio
async def test_generate_avatar_preview_str_and_path(tmp_path):
    """Проверяет генерацию превью для str и Path, отсутствие ошибок и существование файла."""
    from frontend_bot.services.avatar_manager import generate_avatar_preview
    from frontend_bot.shared.image_processing import AsyncImageProcessor
    from frontend_bot.shared.file_operations import AsyncFileManager
    # Создаем тестовое изображение
    img = await AsyncImageProcessor.create_test_image(width=512, height=512, format="JPEG")
    photo_bytes = await AsyncImageProcessor.image_to_bytes(img)
    photo_path = tmp_path / "test_photo.jpg"
    preview_path = tmp_path / "preview.jpg"
    # Сохраняем исходное фото
    await AsyncFileManager.write_binary(photo_path, photo_bytes)
    # Тест: передаем str
    result1 = await generate_avatar_preview(str(photo_path), str(preview_path))
    assert await AsyncFileManager.exists(result1)
    # Тест: передаем Path
    preview_path2 = tmp_path / "preview2.jpg"
    result2 = await generate_avatar_preview(photo_path, preview_path2)
    assert await AsyncFileManager.exists(result2)
    # Проверяем размер превью
    img1 = await AsyncImageProcessor.open(await AsyncFileManager.read_binary(result1))
    img2 = await AsyncImageProcessor.open(await AsyncFileManager.read_binary(result2))
    assert img1.size == (256, 256)
    assert img2.size == (256, 256) 