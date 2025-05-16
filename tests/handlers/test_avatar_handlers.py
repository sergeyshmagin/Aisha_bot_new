"""
Тесты для обработчиков создания аватара.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO
from PIL import Image

from frontend_bot.handlers.handlers import (
    handle_avatar_photo,
    handle_avatar_photo_next,
    handle_avatar_gender,
    handle_avatar_name,
    handle_avatar_confirm,
)
from frontend_bot.services.avatar_workflow import (
    PhotoValidationError,
    ValidationError,
)
from frontend_bot.constants.avatar import AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS
from frontend_bot.bot_instance import bot

@pytest.fixture
def mock_bot():
    """Фикстура для мока бота."""
    with patch("frontend_bot.handlers.handlers.bot") as mock:
        mock.send_message = AsyncMock()
        mock.get_file = AsyncMock()
        mock.download_file = AsyncMock()
        yield mock

@pytest.fixture
def mock_avatar_workflow():
    """Фикстура для мока avatar_workflow."""
    with patch("frontend_bot.handlers.handlers.handle_photo_upload") as mock_upload, \
         patch("frontend_bot.handlers.handlers.handle_gender_selection") as mock_gender, \
         patch("frontend_bot.handlers.handlers.handle_name_input") as mock_name, \
         patch("frontend_bot.handlers.handlers.finalize_avatar") as mock_finalize, \
         patch("frontend_bot.handlers.handlers.load_avatar_fsm") as mock_load, \
         patch("frontend_bot.handlers.handlers.cleanup_state") as mock_cleanup:
        
        mock_upload.return_value = AsyncMock()
        mock_gender.return_value = AsyncMock()
        mock_name.return_value = AsyncMock()
        mock_finalize.return_value = AsyncMock()
        mock_load.return_value = {"photos": []}
        mock_cleanup.return_value = AsyncMock()
        
        yield {
            "upload": mock_upload,
            "gender": mock_gender,
            "name": mock_name,
            "finalize": mock_finalize,
            "load": mock_load,
            "cleanup": mock_cleanup,
        }

@pytest.fixture
def mock_state_manager():
    """Фикстура для мока state_manager."""
    with patch("frontend_bot.handlers.handlers.get_state") as mock_get, \
         patch("frontend_bot.handlers.handlers.set_state") as mock_set, \
         patch("frontend_bot.handlers.handlers.get_current_avatar_id") as mock_get_id, \
         patch("frontend_bot.services.avatar_workflow.set_state") as mock_set_workflow:
        
        mock_get.return_value = "avatar_photo_upload"
        mock_set.return_value = AsyncMock()
        mock_get_id.return_value = "test_avatar_id"
        mock_set_workflow.return_value = AsyncMock()
        
        yield {
            "get": mock_get,
            "set": mock_set,
            "set_workflow": mock_set_workflow,
            "get_id": mock_get_id,
        }

def create_test_photo_message():
    """Создает тестовое сообщение с фото."""
    message = MagicMock()
    message.from_user.id = 123
    message.chat.id = 456
    
    # Создаем тестовое фото
    img = Image.new('RGB', (512, 512), color='red')
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    photo_bytes = img_byte_arr.getvalue()
    
    # Создаем объекты фото разных размеров
    photo1 = MagicMock()
    photo1.file_id = "photo1"
    photo1.file_size = 1000
    
    photo2 = MagicMock()
    photo2.file_id = "photo2"
    photo2.file_size = 2000
    
    message.photo = [photo1, photo2]
    
    return message, photo_bytes

def create_test_text_message(text: str, state: str = "avatar_photo_upload"):
    """Создает тестовое текстовое сообщение."""
    message = MagicMock()
    message.from_user.id = 123
    message.chat.id = 456
    message.text = text
    
    # Мокаем состояние
    with patch("frontend_bot.handlers.handlers.get_state", return_value=state):
        yield message

@pytest.mark.asyncio
async def test_handle_avatar_photo_success(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест успешной загрузки фото."""
    message, photo_bytes = create_test_photo_message()
    mock_bot.download_file.return_value = photo_bytes
    
    await handle_avatar_photo(message)
    
    mock_avatar_workflow["upload"].assert_called_once()
    mock_bot.send_message.assert_called_once()
    assert "Фото успешно загружено" in mock_bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_avatar_photo_validation_error(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест ошибки валидации фото."""
    message, photo_bytes = create_test_photo_message()
    mock_bot.download_file.return_value = photo_bytes
    mock_avatar_workflow["upload"].side_effect = PhotoValidationError("Test error")
    
    await handle_avatar_photo(message)
    
    mock_avatar_workflow["cleanup"].assert_called_once_with(123)

@pytest.mark.asyncio
async def test_handle_avatar_photo_next_success(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест успешного перехода к следующему шагу."""
    message = next(create_test_text_message("Далее"))
    mock_avatar_workflow["load"].return_value = {"photos": ["photo"] * AVATAR_MIN_PHOTOS}
    
    await handle_avatar_photo_next(message)
    
    mock_bot.send_message.assert_called_once()
    assert "Выберите пол для аватара" in mock_bot.send_message.call_args[0][1]
    mock_state_manager["set"].assert_called_once_with(123, "avatar_gender")

@pytest.mark.asyncio
async def test_handle_avatar_photo_next_not_enough_photos(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест перехода при недостаточном количестве фото."""
    message = next(create_test_text_message("Далее"))
    mock_avatar_workflow["load"].return_value = {"photos": ["photo"] * (AVATAR_MIN_PHOTOS - 1)}
    
    await handle_avatar_photo_next(message)
    
    mock_bot.send_message.assert_called_once()
    assert "Недостаточно фото" in mock_bot.send_message.call_args[0][1]
    mock_state_manager["set"].assert_not_called()

@pytest.mark.asyncio
async def test_handle_avatar_gender_success(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест успешного выбора пола."""
    message = next(create_test_text_message("Мужской", "avatar_gender"))
    
    await handle_avatar_gender(message)
    
    mock_avatar_workflow["gender"].assert_called_once_with(123, "test_avatar_id", "male")
    mock_bot.send_message.assert_called_once()
    assert "Введите имя для аватара" in mock_bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_avatar_gender_validation_error(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест ошибки валидации при выборе пола."""
    message = next(create_test_text_message("Неверный пол", "avatar_gender"))
    mock_avatar_workflow["gender"].side_effect = ValidationError("Test error")
    
    await handle_avatar_gender(message)
    
    mock_avatar_workflow["cleanup"].assert_called_once_with(123)

@pytest.mark.asyncio
async def test_handle_avatar_name_success(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест успешного ввода имени."""
    message = next(create_test_text_message("Test Avatar", "avatar_enter_name"))
    
    await handle_avatar_name(message)
    
    mock_avatar_workflow["name"].assert_called_once_with(123, "test_avatar_id", "Test Avatar")
    mock_bot.send_message.assert_called_once()
    assert "Проверьте данные аватара" in mock_bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_avatar_name_validation_error(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест ошибки валидации при вводе имени."""
    message = next(create_test_text_message("", "avatar_enter_name"))
    mock_avatar_workflow["name"].side_effect = ValidationError("Test error")
    
    await handle_avatar_name(message)
    
    mock_avatar_workflow["cleanup"].assert_called_once_with(123)

@pytest.mark.asyncio
async def test_handle_avatar_confirm_success(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест успешного подтверждения создания аватара."""
    message = next(create_test_text_message("Подтвердить", "avatar_confirm"))
    
    await handle_avatar_confirm(message)
    
    mock_avatar_workflow["finalize"].assert_called_once_with(123, "test_avatar_id")
    mock_bot.send_message.assert_called_once()
    assert "Аватар успешно создан" in mock_bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_avatar_confirm_validation_error(mock_bot, mock_avatar_workflow, mock_state_manager):
    """Тест ошибки валидации при подтверждении."""
    message = next(create_test_text_message("Подтвердить", "avatar_confirm"))
    mock_avatar_workflow["finalize"].side_effect = ValidationError("Test error")
    
    await handle_avatar_confirm(message)
    
    mock_avatar_workflow["cleanup"].assert_called_once_with(123) 