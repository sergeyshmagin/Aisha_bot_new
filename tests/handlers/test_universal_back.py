"""
Тесты для универсальных обработчиков.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from frontend_bot.handlers.universal_back import (
    handle_cancel,
    handle_photo_enhance_back,
    handle_transcribe_back,
)
from frontend_bot.services.avatar_workflow import cleanup_state

@pytest.fixture
def mock_bot():
    """Фикстура для мока бота."""
    with patch("frontend_bot.handlers.universal_back.bot") as mock:
        mock.send_message = AsyncMock()
        yield mock

@pytest.fixture
def mock_state_manager():
    """Фикстура для мока state_manager."""
    with patch("frontend_bot.handlers.universal_back.get_state") as mock_get, \
         patch("frontend_bot.handlers.universal_back.set_state") as mock_set:
        
        mock_get.return_value = "main_menu"
        mock_set.return_value = AsyncMock()
        
        yield {
            "get": mock_get,
            "set": mock_set,
        }

@pytest.fixture
def mock_avatar_workflow():
    """Фикстура для мока avatar_workflow."""
    with patch("frontend_bot.handlers.universal_back.cleanup_state") as mock:
        mock.return_value = AsyncMock()
        yield mock

def create_test_message(state: str = "main_menu"):
    """Создает тестовое сообщение."""
    message = MagicMock()
    message.from_user.id = 123
    message.chat.id = 456
    message.text = "Отмена"
    
    # Мокаем состояние
    with patch("frontend_bot.handlers.universal_back.get_state", return_value=state):
        yield message

@pytest.mark.asyncio
async def test_handle_cancel_avatar_photo_upload(mock_bot, mock_state_manager, mock_avatar_workflow):
    """Тест отмены при загрузке фото аватара."""
    message = next(create_test_message("avatar_photo_upload"))
    
    await handle_cancel(message)
    
    mock_avatar_workflow.assert_called_once_with(123)
    mock_bot.send_message.assert_called_once()
    assert "Создание аватара отменено" in mock_bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_cancel_avatar_gender(mock_bot, mock_state_manager, mock_avatar_workflow):
    """Тест отмены при выборе пола аватара."""
    message = next(create_test_message("avatar_gender"))
    
    await handle_cancel(message)
    
    mock_avatar_workflow.assert_called_once_with(123)
    mock_bot.send_message.assert_called_once()
    assert "Создание аватара отменено" in mock_bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_cancel_avatar_name(mock_bot, mock_state_manager, mock_avatar_workflow):
    """Тест отмены при вводе имени аватара."""
    message = next(create_test_message("avatar_enter_name"))
    
    await handle_cancel(message)
    
    mock_avatar_workflow.assert_called_once_with(123)
    mock_bot.send_message.assert_called_once()
    assert "Создание аватара отменено" in mock_bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_cancel_avatar_confirm(mock_bot, mock_state_manager, mock_avatar_workflow):
    """Тест отмены при подтверждении создания аватара."""
    message = next(create_test_message("avatar_confirm"))
    
    await handle_cancel(message)
    
    mock_avatar_workflow.assert_called_once_with(123)
    mock_bot.send_message.assert_called_once()
    assert "Создание аватара отменено" in mock_bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_cancel_photo_enhance(mock_bot, mock_state_manager):
    """Тест отмены в меню улучшения фото."""
    message = next(create_test_message("photo_enhance"))
    
    await handle_cancel(message)
    
    mock_bot.send_message.assert_called_once()
    assert "Выберите действие" in mock_bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_cancel_transcribe(mock_bot, mock_state_manager):
    """Тест отмены в меню транскрибации."""
    message = next(create_test_message("transcribe"))
    
    await handle_cancel(message)
    
    mock_bot.send_message.assert_called_once()
    assert "Выберите действие" in mock_bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_cancel_other_state(mock_bot, mock_state_manager):
    """Тест отмены в другом состоянии."""
    message = next(create_test_message("other_state"))
    
    await handle_cancel(message)
    
    mock_state_manager["set"].assert_called_once_with(123, "main_menu")
    mock_bot.send_message.assert_called_once()
    assert "Действие отменено" in mock_bot.send_message.call_args[0][1]

@pytest.mark.asyncio
async def test_handle_cancel_error(mock_bot, mock_state_manager):
    """Тест обработки ошибки при отмене."""
    message = next(create_test_message("avatar_photo_upload"))
    mock_state_manager["set"].side_effect = Exception("Test error")
    
    await handle_cancel(message)
    
    mock_bot.send_message.assert_called_once()
    assert "Произошла ошибка при отмене действия" in mock_bot.send_message.call_args[0][1]
    mock_state_manager["set"].assert_called_with(123, "main_menu") 