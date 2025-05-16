"""
Тесты для модуля avatar_workflow.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO
from PIL import Image

from frontend_bot.services.avatar_workflow import (
    init_avatar_creation,
    validate_photo,
    handle_photo_upload,
    handle_gender_selection,
    handle_name_input,
    finalize_avatar,
    cleanup_state,
    handle_creation_error,
    AvatarCreationError,
    PhotoValidationError,
    ValidationError,
    StateError,
)
from frontend_bot.constants.avatar import AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS
from frontend_bot.config import PHOTO_MIN_RES

@pytest.fixture
def mock_avatar_manager():
    """Фикстура для мока avatar_manager."""
    with patch("frontend_bot.services.avatar_workflow.init_avatar_fsm") as mock_init, \
         patch("frontend_bot.services.avatar_workflow.add_photo_to_avatar") as mock_add, \
         patch("frontend_bot.services.avatar_workflow.update_avatar_fsm") as mock_update, \
         patch("frontend_bot.services.avatar_workflow.mark_avatar_ready") as mock_mark, \
         patch("frontend_bot.services.avatar_workflow.load_avatar_fsm") as mock_load:
        
        mock_init.return_value = None
        mock_add.return_value = "/path/to/photo.jpg"
        mock_update.return_value = None
        mock_mark.return_value = None
        mock_load.return_value = {"photos": []}
        
        yield {
            "init": mock_init,
            "add": mock_add,
            "update": mock_update,
            "mark": mock_mark,
            "load": mock_load,
        }

@pytest.fixture
def mock_state_manager():
    """Фикстура для мока state_manager."""
    with patch("frontend_bot.services.avatar_workflow.set_state") as mock_set, \
         patch("frontend_bot.services.avatar_workflow.get_state") as mock_get:
        
        mock_set.return_value = AsyncMock()  # set_state теперь асинхронный
        mock_get.return_value = AsyncMock(return_value="avatar_photo_upload")  # get_state теперь асинхронный
        
        yield {
            "set": mock_set,
            "get": mock_get,
        }

@pytest.fixture
def mock_image_processor():
    """Фикстура для мока image_processor."""
    with patch("frontend_bot.services.avatar_workflow.AsyncImageProcessor") as mock:
        mock_instance = AsyncMock()
        mock_instance.size = (PHOTO_MIN_RES, PHOTO_MIN_RES)
        mock_instance.open_from_bytes = AsyncMock(return_value=mock_instance)
        mock.return_value = mock_instance
        mock.open_from_bytes = AsyncMock(return_value=mock_instance)
        yield mock

def create_test_image(width: int, height: int) -> bytes:
    """Создает тестовое изображение заданного размера."""
    img = Image.new('RGB', (width, height), color='red')
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

@pytest.mark.asyncio
async def test_init_avatar_creation(mock_avatar_manager, mock_state_manager):
    """Тест инициализации создания аватара."""
    user_id = 123
    
    avatar_id = await init_avatar_creation(user_id)
    
    assert avatar_id is not None
    mock_avatar_manager["init"].assert_called_once()
    mock_state_manager["set"].assert_called_once_with(user_id, "avatar_photo_upload")

@pytest.mark.asyncio
async def test_validate_photo_valid(mock_image_processor):
    """Тест валидации корректного фото."""
    photo_bytes = create_test_image(PHOTO_MIN_RES, PHOTO_MIN_RES)
    
    result = await validate_photo(photo_bytes)

    assert result is True
    mock_image_processor.open_from_bytes.assert_called_once_with(photo_bytes)

@pytest.mark.asyncio
async def test_validate_photo_too_small(mock_image_processor):
    """Тест валидации фото с недостаточным разрешением."""
    photo_bytes = create_test_image(PHOTO_MIN_RES - 1, PHOTO_MIN_RES - 1)
    mock_instance = AsyncMock()
    mock_instance.size = (PHOTO_MIN_RES - 1, PHOTO_MIN_RES - 1)
    mock_image_processor.open_from_bytes.return_value = mock_instance
    
    with pytest.raises(PhotoValidationError):
        await validate_photo(photo_bytes)

@pytest.mark.asyncio
async def test_validate_photo_too_large():
    """Тест валидации фото с превышающим размером."""
    photo_bytes = b"x" * (10 * 1024 * 1024 + 1)  # > 10MB
    
    with pytest.raises(PhotoValidationError):
        await validate_photo(photo_bytes)

@pytest.mark.asyncio
async def test_handle_photo_upload_success(mock_avatar_manager, mock_image_processor):
    """Тест успешной загрузки фото."""
    user_id = 123
    avatar_id = "test_avatar_id"
    photo_bytes = create_test_image(PHOTO_MIN_RES, PHOTO_MIN_RES)
    
    photo_path = await handle_photo_upload(user_id, avatar_id, photo_bytes)
    
    assert photo_path == "/path/to/photo.jpg"
    mock_avatar_manager["add"].assert_called_once()
    mock_avatar_manager["load"].assert_called_once()
    mock_image_processor.open_from_bytes.assert_called_once_with(photo_bytes)

@pytest.mark.asyncio
async def test_handle_photo_upload_max_photos(mock_avatar_manager, mock_image_processor):
    """Тест загрузки фото при превышении лимита."""
    user_id = 123
    avatar_id = "test_avatar_id"
    photo_bytes = create_test_image(PHOTO_MIN_RES, PHOTO_MIN_RES)

    # Мокаем максимальное количество фото
    mock_avatar_manager["load"].return_value = {"photos": ["photo"] * (AVATAR_MAX_PHOTOS + 1)}

    with pytest.raises(PhotoValidationError) as exc_info:
        await handle_photo_upload(user_id, avatar_id, photo_bytes)
    
    assert str(exc_info.value) == f"Maximum number of photos ({AVATAR_MAX_PHOTOS}) exceeded"
    mock_image_processor.open_from_bytes.assert_called_once_with(photo_bytes)

@pytest.mark.asyncio
async def test_handle_gender_selection_valid(mock_avatar_manager, mock_state_manager):
    """Тест выбора валидного пола."""
    user_id = 123
    avatar_id = "test_avatar_id"
    gender = "male"
    
    await handle_gender_selection(user_id, avatar_id, gender)
    
    mock_avatar_manager["update"].assert_called_once_with(
        user_id, avatar_id, class_name=gender
    )
    mock_state_manager["set"].assert_called_once_with(user_id, "avatar_enter_name")

@pytest.mark.asyncio
async def test_handle_gender_selection_invalid(mock_avatar_manager, mock_state_manager):
    """Тест выбора невалидного пола."""
    user_id = 123
    avatar_id = "test_avatar_id"
    gender = "invalid"
    
    with pytest.raises(ValidationError):
        await handle_gender_selection(user_id, avatar_id, gender)

@pytest.mark.asyncio
async def test_handle_name_input_valid(mock_avatar_manager, mock_state_manager):
    """Тест ввода валидного имени."""
    user_id = 123
    avatar_id = "test_avatar_id"
    name = "Test Avatar"
    
    await handle_name_input(user_id, avatar_id, name)
    
    mock_avatar_manager["update"].assert_called_once_with(
        user_id, avatar_id, title=name
    )
    mock_state_manager["set"].assert_called_once_with(user_id, "avatar_confirm")

@pytest.mark.asyncio
async def test_handle_name_input_empty(mock_avatar_manager, mock_state_manager):
    """Тест ввода пустого имени."""
    user_id = 123
    avatar_id = "test_avatar_id"
    name = ""
    
    with pytest.raises(ValidationError):
        await handle_name_input(user_id, avatar_id, name)

@pytest.mark.asyncio
async def test_handle_name_input_too_long(mock_avatar_manager, mock_state_manager):
    """Тест ввода слишком длинного имени."""
    user_id = 123
    avatar_id = "test_avatar_id"
    name = "x" * 51  # > 50 characters
    
    with pytest.raises(ValidationError):
        await handle_name_input(user_id, avatar_id, name)

@pytest.mark.asyncio
async def test_finalize_avatar_success(mock_avatar_manager, mock_state_manager):
    """Тест успешного завершения создания аватара."""
    user_id = 123
    avatar_id = "test_avatar_id"
    
    # Мокаем достаточное количество фото
    mock_avatar_manager["load"].return_value = {
        "photos": ["photo"] * AVATAR_MIN_PHOTOS
    }
    
    await finalize_avatar(user_id, avatar_id)
    
    mock_avatar_manager["mark"].assert_called_once()
    mock_state_manager["set"].assert_called_once_with(user_id, "my_avatars")

@pytest.mark.asyncio
async def test_finalize_avatar_not_enough_photos(mock_avatar_manager, mock_state_manager):
    """Тест завершения с недостаточным количеством фото."""
    user_id = 123
    avatar_id = "test_avatar_id"
    
    # Мокаем недостаточное количество фото
    mock_avatar_manager["load"].return_value = {
        "photos": ["photo"] * (AVATAR_MIN_PHOTOS - 1)
    }
    
    with pytest.raises(ValidationError):
        await finalize_avatar(user_id, avatar_id)

@pytest.mark.asyncio
async def test_cleanup_state(mock_state_manager):
    """Тест очистки состояния."""
    user_id = 123
    
    await cleanup_state(user_id)
    
    mock_state_manager["set"].assert_called_once_with(user_id, "my_avatars")

@pytest.mark.asyncio
async def test_handle_creation_error_photo_validation(mock_state_manager):
    """Тест обработки ошибки валидации фото."""
    user_id = 123
    chat_id = 456
    error = PhotoValidationError("Test error")
    
    await handle_creation_error(user_id, chat_id, error)
    
    mock_state_manager["set"].assert_called_once_with(user_id, "my_avatars")

@pytest.mark.asyncio
async def test_handle_creation_error_validation(mock_state_manager):
    """Тест обработки ошибки валидации данных."""
    user_id = 123
    chat_id = 456
    error = ValidationError("Test error")
    
    await handle_creation_error(user_id, chat_id, error)
    
    mock_state_manager["set"].assert_called_once_with(user_id, "my_avatars")

@pytest.mark.asyncio
async def test_handle_creation_error_state(mock_state_manager):
    """Тест обработки ошибки состояния."""
    user_id = 123
    chat_id = 456
    error = StateError("Test error")
    
    await handle_creation_error(user_id, chat_id, error)
    
    mock_state_manager["set"].assert_called_once_with(user_id, "my_avatars") 