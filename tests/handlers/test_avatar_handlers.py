"""
Тесты для обработчиков создания аватара.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from io import BytesIO
from PIL import Image

from frontend_bot.handlers.handlers import (
    handle_avatar_photo,
    handle_avatar_gender,
    handle_avatar_name,
    handle_avatar_confirm,
    handle_avatar_photo_next
)
from frontend_bot.services.state_utils import get_state, set_state
from frontend_bot.services.avatar_workflow import cleanup_state
from frontend_bot.constants.avatar import AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS
from frontend_bot.bot_instance import bot
from tests.conftest_redis import mock_redis

@pytest.fixture
def mock_message():
    """Фикстура для создания тестового сообщения."""
    message = MagicMock()
    message.from_user.id = 123456
    message.chat.id = 123456
    return message

@pytest.fixture
def mock_bot():
    """Мок для бота."""
    with patch("frontend_bot.bot_instance.bot") as mock:
        mock.send_message = AsyncMock()
        mock.send_chat_action = AsyncMock()
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
         patch("frontend_bot.services.avatar_workflow.set_state") as mock_set_workflow:
        
        mock_get.return_value = "avatar_upload_photo"
        mock_set.return_value = None
        mock_set_workflow.return_value = None
        
        yield {
            "get": mock_get,
            "set": mock_set,
            "set_workflow": mock_set_workflow
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
async def test_handle_avatar_photo_success(mock_message, mock_bot, mock_redis):
    """Тест успешной обработки фото аватара."""
    # Настраиваем моки
    mock_message.photo = [MagicMock(file_id="test_file_id")]
    mock_bot.get_file.return_value = MagicMock(file_path="test_path")
    mock_bot.download_file.return_value = b"test_photo_data"
    mock_bot.send_message = AsyncMock()
    
    # Устанавливаем начальное состояние
    await set_state(mock_message.from_user.id, "avatar_photo_upload")
    
    # Вызываем обработчик
    await handle_avatar_photo(mock_message)
    
    # Проверяем результат
    assert await get_state(mock_message.from_user.id) == "avatar_photo_upload"
    mock_bot.send_message.assert_called_once()
    mock_bot.get_file.assert_called_once_with("test_file_id")
    mock_bot.download_file.assert_called_once_with("test_path")

@pytest.mark.asyncio
async def test_handle_avatar_photo_validation_error(mock_message, mock_bot, mock_redis):
    """Тест ошибки валидации фото аватара."""
    # Настраиваем моки
    mock_message.photo = None
    mock_bot.send_message = AsyncMock()
    
    # Устанавливаем начальное состояние
    await set_state(mock_message.from_user.id, "avatar_photo_upload")
    
    # Вызываем обработчик
    await handle_avatar_photo(mock_message)
    
    # Проверяем результат
    assert await get_state(mock_message.from_user.id) == "avatar_photo_upload"
    mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_handle_avatar_gender_success(mock_message, mock_bot, mock_redis):
    """Тест успешной обработки выбора пола."""
    # Настраиваем моки
    mock_message.text = "Мужской"
    mock_bot.send_message = AsyncMock()
    
    # Устанавливаем начальное состояние
    await set_state(mock_message.from_user.id, "avatar_gender")
    
    # Вызываем обработчик
    await handle_avatar_gender(mock_message)
    
    # Проверяем результат
    assert await get_state(mock_message.from_user.id) == "avatar_enter_name"
    mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_handle_avatar_gender_validation_error(mock_message, mock_bot, mock_redis):
    """Тест ошибки валидации выбора пола."""
    # Настраиваем моки
    mock_message.text = "Неверный выбор"
    mock_bot.send_message = AsyncMock()
    
    # Устанавливаем начальное состояние
    await set_state(mock_message.from_user.id, "avatar_gender")
    
    # Вызываем обработчик
    await handle_avatar_gender(mock_message)
    
    # Проверяем результат
    assert await get_state(mock_message.from_user.id) == "avatar_gender"
    mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_handle_avatar_name_success(mock_message, mock_bot, mock_redis):
    """Тест успешной обработки ввода имени."""
    # Настраиваем моки
    mock_message.text = "Test Avatar"
    mock_bot.send_message = AsyncMock()
    
    # Устанавливаем начальное состояние
    await set_state(mock_message.from_user.id, "avatar_enter_name")
    
    # Вызываем обработчик
    await handle_avatar_name(mock_message)
    
    # Проверяем результат
    assert await get_state(mock_message.from_user.id) == "avatar_confirm"
    mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_handle_avatar_name_validation_error(mock_message, mock_bot, mock_redis):
    """Тест ошибки валидации имени."""
    # Настраиваем моки
    mock_message.text = ""
    mock_bot.send_message = AsyncMock()
    
    # Устанавливаем начальное состояние
    await set_state(mock_message.from_user.id, "avatar_enter_name")
    
    # Вызываем обработчик
    await handle_avatar_name(mock_message)
    
    # Проверяем результат
    assert await get_state(mock_message.from_user.id) == "avatar_enter_name"
    mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_handle_avatar_confirm_success(mock_message, mock_bot, mock_redis):
    """Тест успешного подтверждения создания аватара."""
    # Настраиваем моки
    mock_message.text = "Подтвердить"
    mock_bot.send_message = AsyncMock()
    
    # Устанавливаем начальное состояние
    await set_state(mock_message.from_user.id, "avatar_confirm")
    
    # Вызываем обработчик
    await handle_avatar_confirm(mock_message)
    
    # Проверяем результат
    assert await get_state(mock_message.from_user.id) == "main_menu"
    mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_handle_avatar_confirm_validation_error(mock_message, mock_bot, mock_redis):
    """Тест ошибки валидации подтверждения."""
    # Настраиваем моки
    mock_message.text = "Отмена"
    mock_bot.send_message = AsyncMock()
    
    # Устанавливаем начальное состояние
    await set_state(mock_message.from_user.id, "avatar_confirm")
    
    # Вызываем обработчик
    await handle_avatar_confirm(mock_message)
    
    # Проверяем результат
    assert await get_state(mock_message.from_user.id) == "main_menu"
    mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_handle_avatar_photo_next_success(mock_bot, mock_avatar_workflow, mock_state_manager, mock_redis):
    """Тест успешной обработки следующего фото."""
    # Настраиваем моки
    message = MagicMock()
    message.from_user.id = 123456
    message.chat.id = 123456
    message.photo = [MagicMock(file_id="test_file_id")]
    mock_bot.send_message = AsyncMock()
    
    # Устанавливаем начальное состояние
    await set_state(message.from_user.id, "avatar_photo_upload")
    
    # Вызываем обработчик
    await handle_avatar_photo_next(message)
    
    # Проверяем результат
    mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_handle_avatar_photo_next_not_enough_photos(mock_bot, mock_avatar_workflow, mock_state_manager, mock_redis):
    """Тест обработки недостаточного количества фото."""
    # Настраиваем моки
    message = MagicMock()
    message.from_user.id = 123456
    message.chat.id = 123456
    message.photo = None
    mock_bot.send_message = AsyncMock()
    
    # Устанавливаем начальное состояние
    await set_state(message.from_user.id, "avatar_photo_upload")
    
    # Вызываем обработчик
    await handle_avatar_photo_next(message)
    
    # Проверяем результат
    mock_bot.send_message.assert_called_once() 