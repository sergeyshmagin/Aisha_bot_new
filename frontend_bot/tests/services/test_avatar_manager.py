"""
Тесты для менеджера аватаров.
"""

import pytest
import os
from pathlib import Path
import aiofiles
import json
from PIL import Image
from frontend_bot.services.avatar_manager import (
    ensure_avatar_dirs,
    get_user_avatar_dir,
    save_avatar_photo,
    get_user_avatar_photos,
    clear_user_avatar_photos,
    add_photo_to_avatar,
    generate_avatar_preview,
    validate_photo,
    mark_avatar_ready,
    get_current_avatar_id,
    set_current_avatar_id,
    get_user_dir,
    get_avatar_dir,
    get_avatar_json_path,
    get_avatars_index_path,
    init_avatar_fsm,
    load_avatar_fsm,
    save_avatar_fsm,
    update_avatar_fsm,
    clear_avatar_fsm,
    migrate_avatars_index,
    get_avatars_index,
    add_avatar_to_index,
    update_avatar_in_index,
    remove_avatar_from_index,
    find_avatar_by_tune_id,
    remove_photo_from_avatar
)
from frontend_bot.shared.file_operations import AsyncFileManager
from frontend_bot.shared.image_processing import AsyncImageProcessor
from frontend_bot.config import PHOTO_MIN_RES, PHOTO_MAX_MB
import io

def create_test_image(width=256, height=256, color=(255, 0, 0)):
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

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
async def test_state_management(tmp_path):
    """Тест управления состоянием (эмулируем через временный json-файл)."""
    from frontend_bot.services.avatar_manager import save_avatar_fsm, load_avatar_fsm
    user_id = "123"
    avatar_id = "test_avatar"
    test_state = {
        "photos": ["photo1.jpg", "photo2.jpg"],
        "title": "Test Avatar",
        "status": "pending"
    }
    await save_avatar_fsm(user_id, avatar_id, test_state)
    state = await load_avatar_fsm(user_id, avatar_id)
    assert state["title"] == "Test Avatar"
    # Очищаем состояние (удаляем файл)
    from frontend_bot.services.avatar_manager import get_avatar_json_path
    path = get_avatar_json_path(user_id, avatar_id)
    if os.path.exists(path):
        os.remove(path)
    state = await load_avatar_fsm(user_id, avatar_id)
    assert state is None

@pytest.mark.asyncio
async def test_cleanup_state(tmp_path):
    """Тест полной очистки данных пользователя (удаление фото и json)."""
    from frontend_bot.services.avatar_manager import save_avatar_fsm, load_avatar_fsm, get_avatar_json_path, save_avatar_photo, get_user_avatar_photos, clear_user_avatar_photos
    user_id = "123"
    avatar_id = "test_avatar"
    photo_bytes = create_test_image()
    await save_avatar_photo(user_id, photo_bytes, "photo1", tmp_path)
    await save_avatar_fsm(user_id, avatar_id, {"photos": ["photo1.jpg"]})
    await clear_user_avatar_photos(user_id, tmp_path)
    photos = await get_user_avatar_photos(user_id, tmp_path)
    assert len(photos) == 0
    path = get_avatar_json_path(user_id, avatar_id)
    if os.path.exists(path):
        os.remove(path)
    state = await load_avatar_fsm(user_id, avatar_id)
    assert state is None

@pytest.mark.asyncio
async def test_validate_photo():
    """Тест валидации фото."""
    # Создаем тестовое изображение с размером 512x512
    img = Image.new('RGB', (512, 512), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    # Проверяем валидацию
    is_valid, msg = await validate_photo(img_byte_arr)
    assert is_valid
    assert msg == "OK"

@pytest.mark.asyncio
async def test_generate_avatar_preview(temp_dir):
    """Тест генерации превью аватара."""
    # Создаем тестовое изображение
    img = Image.new('RGB', (500, 500), color='blue')
    photo_path = temp_dir / "test_photo.jpg"
    img.save(photo_path)
    preview_path = temp_dir / "preview.jpg"
    result = await generate_avatar_preview(photo_path, preview_path)
    assert result == preview_path
    assert os.path.exists(preview_path)

@pytest.mark.asyncio
async def test_mark_avatar_ready(temp_dir):
    """Тест отметки аватара как готового."""
    user_id = 123
    avatar_id = "test_avatar"
    # Инициализируем состояние аватара
    await init_avatar_fsm(user_id, avatar_id, title="Test Avatar")
    # Добавляем фото с размером 512x512
    img = Image.new('RGB', (512, 512), color='green')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    await add_photo_to_avatar(user_id, avatar_id, img_byte_arr)
    # Отмечаем как готовый
    await mark_avatar_ready(user_id, avatar_id)
    data = await load_avatar_fsm(user_id, avatar_id)
    assert data["ready"] is True

@pytest.mark.asyncio
async def test_get_current_avatar_id():
    """Тест получения текущего avatar_id."""
    user_id = 123
    avatar_id = "test_avatar"
    set_current_avatar_id(user_id, avatar_id)
    assert get_current_avatar_id(user_id) == avatar_id

@pytest.mark.asyncio
async def test_get_user_dir(temp_dir):
    """Тест получения директории пользователя."""
    user_id = 123
    user_dir = get_user_dir(user_id)
    assert user_dir.endswith(str(user_id))

@pytest.mark.asyncio
async def test_get_avatar_dir(temp_dir):
    """Тест получения директории аватара."""
    user_id = 123
    avatar_id = "test_avatar"
    avatar_dir = get_avatar_dir(user_id, avatar_id)
    assert avatar_dir.endswith(avatar_id)

@pytest.mark.asyncio
async def test_get_avatar_json_path(temp_dir):
    """Тест получения пути к JSON-файлу аватара."""
    user_id = 123
    avatar_id = "test_avatar"
    json_path = get_avatar_json_path(user_id, avatar_id)
    assert json_path.endswith("data.json")

@pytest.mark.asyncio
async def test_get_avatars_index_path(temp_dir):
    """Тест получения пути к индексу аватаров."""
    user_id = 123
    index_path = get_avatars_index_path(user_id)
    assert index_path.endswith("avatars.json")

@pytest.mark.asyncio
async def test_init_avatar_fsm(temp_dir):
    """Тест инициализации состояния аватара."""
    user_id = 123
    avatar_id = "test_avatar"
    await init_avatar_fsm(user_id, avatar_id, title="Test Avatar")
    data = await load_avatar_fsm(user_id, avatar_id)
    assert data["title"] == "Test Avatar"

@pytest.mark.asyncio
async def test_load_avatar_fsm(temp_dir):
    """Тест загрузки состояния аватара."""
    user_id = 123
    avatar_id = "test_avatar"
    data = await load_avatar_fsm(user_id, avatar_id)
    assert data is not None

@pytest.mark.asyncio
async def test_save_avatar_fsm(temp_dir):
    """Тест сохранения состояния аватара."""
    user_id = 123
    avatar_id = "test_avatar"
    test_data = {"title": "Test Avatar", "status": "pending"}
    await save_avatar_fsm(user_id, avatar_id, test_data)
    data = await load_avatar_fsm(user_id, avatar_id)
    assert data["title"] == "Test Avatar"

@pytest.mark.asyncio
async def test_add_photo_to_avatar(temp_dir):
    """Тест добавления фото к аватару."""
    user_id = 123
    avatar_id = "test_avatar"
    img = Image.new('RGB', (512, 512), color='yellow')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    photo_id = await add_photo_to_avatar(user_id, avatar_id, img_byte_arr)
    assert photo_id is not None

@pytest.mark.asyncio
async def test_update_avatar_fsm(temp_dir):
    """Тест обновления состояния аватара."""
    user_id = 123
    avatar_id = "test_avatar"
    await update_avatar_fsm(user_id, avatar_id, title="Updated Avatar")
    data = await load_avatar_fsm(user_id, avatar_id)
    assert data["title"] == "Updated Avatar"

@pytest.mark.asyncio
async def test_clear_avatar_fsm(temp_dir):
    """Тест очистки состояния аватара."""
    user_id = 123
    avatar_id = "test_avatar"
    await clear_avatar_fsm(user_id, avatar_id)
    data = await load_avatar_fsm(user_id, avatar_id)
    assert data is None

@pytest.mark.asyncio
async def test_migrate_avatars_index(temp_dir):
    """Тест миграции индекса аватаров."""
    user_id = 123
    await migrate_avatars_index(user_id)

@pytest.mark.asyncio
async def test_get_avatars_index(temp_dir):
    """Тест получения индекса аватаров."""
    user_id = 123
    index = await get_avatars_index(user_id)
    assert isinstance(index, list)

@pytest.mark.asyncio
async def test_add_avatar_to_index(temp_dir):
    """Тест добавления аватара в индекс."""
    user_id = 123
    avatar_id = "test_avatar"
    await add_avatar_to_index(user_id, avatar_id, "Test Avatar", "style", "2023-01-01")
    index = await get_avatars_index(user_id)
    assert any(avatar["avatar_id"] == avatar_id for avatar in index)

@pytest.mark.asyncio
async def test_update_avatar_in_index(temp_dir):
    """Тест обновления аватара в индексе."""
    user_id = 123
    avatar_id = "test_avatar"
    await update_avatar_in_index(user_id, avatar_id, {"title": "Updated Avatar"})
    index = await get_avatars_index(user_id)
    assert any(avatar["title"] == "Updated Avatar" for avatar in index)

@pytest.mark.asyncio
async def test_remove_avatar_from_index(temp_dir):
    """Тест удаления аватара из индекса."""
    user_id = 123
    avatar_id = "test_avatar"
    await remove_avatar_from_index(user_id, avatar_id)
    index = await get_avatars_index(user_id)
    assert not any(avatar["avatar_id"] == avatar_id for avatar in index)

@pytest.mark.asyncio
async def test_find_avatar_by_tune_id(temp_dir):
    """Тест поиска аватара по tune_id."""
    tune_id = "test_tune_id"
    avatar = await find_avatar_by_tune_id(tune_id)
    assert avatar is None

@pytest.mark.asyncio
async def test_remove_photo_from_avatar(temp_dir):
    """Тест удаления фото из аватара."""
    user_id = 123
    avatar_id = "test_avatar"
    result = await remove_photo_from_avatar(user_id, avatar_id, 0)
    assert result is False

@pytest.mark.asyncio
async def test_concurrent_operations(tmp_path):
    """Тест конкурентных операций сохранения фото."""
    from frontend_bot.services.avatar_manager import save_avatar_photo, get_user_avatar_photos
    import asyncio
    user_id = "123"
    async def save_photo(photo_id):
        await save_avatar_photo(user_id, create_test_image(), photo_id, tmp_path)
    tasks = [save_photo(f"photo{i}") for i in range(5)]
    await asyncio.gather(*tasks)
    photos = await get_user_avatar_photos(user_id, tmp_path)
    assert len(photos) == 5

@pytest.mark.asyncio
async def test_generate_avatar_preview_str_and_path(tmp_path):
    """Проверяет генерацию превью для str и Path, отсутствие ошибок и существование файла."""
    # Используем PIL для генерации тестового изображения
    photo_bytes = create_test_image(width=512, height=512)
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
    img1 = Image.open(io.BytesIO(await AsyncFileManager.read_binary(result1)))
    img2 = Image.open(io.BytesIO(await AsyncFileManager.read_binary(result2)))
    assert img1.size == (256, 256)
    assert img2.size == (256, 256) 