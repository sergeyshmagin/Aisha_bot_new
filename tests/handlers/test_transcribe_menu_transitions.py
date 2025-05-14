"""Тесты для проверки переходов в меню транскрибации."""

import pytest
from unittest.mock import patch, AsyncMock
from frontend_bot.services.state_manager import (
    get_state,
    clear_all_states,
    set_state,
)
from frontend_bot.keyboards.main_menu import main_menu_keyboard
from frontend_bot.keyboards.transcribe import transcribe_keyboard
from frontend_bot.handlers.general import handle_main_menu
from frontend_bot.handlers.transcribe import (
    handle_transcribe_menu,
    handle_transcribe_history,
)


@pytest.fixture
async def clean_state():
    """Фикстура для очистки состояния до и после теста."""
    await clear_all_states()
    yield
    await clear_all_states()


@pytest.fixture
def mock_bot():
    """Фикстура для мока бота."""
    with patch('frontend_bot.bot.bot') as mock:
        yield mock


@pytest.fixture
def create_message():
    """Фикстура для создания тестового сообщения."""
    def _create_message(user_id: int, text: str):
        message = AsyncMock()
        message.from_user.id = user_id
        message.chat.id = user_id
        message.text = text
        return message
    return _create_message


@pytest.mark.asyncio
async def test_main_menu_to_transcribe(clean_state, mock_bot, create_message):
    """
    Тест перехода из главного меню в меню транскрибации.
    
    Проверяет:
    - Отправку сообщения с описанием возможностей
    - Установку клавиатуры транскрибации
    - Установку состояния transcribe
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "main_menu")
    message = create_message(user_id, "🎙 Транскрибация")

    # Act
    await handle_main_menu(message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "Выберите действие" in args[1]
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert "📝 Новая транскрибация" in str(keyboard)
    state = await get_state(user_id)
    assert state == "transcribe"


@pytest.mark.asyncio
async def test_transcribe_to_history(clean_state, mock_bot, create_message):
    """
    Тест перехода из меню транскрибации в историю транскрибаций.
    
    Проверяет:
    - Отправку сообщения с историей
    - Установку состояния transcribe_history
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "transcribe")
    message = create_message(user_id, "📋 История")

    # Act
    await handle_transcribe_history(message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "История транскрибаций" in args[1]
    state = await get_state(user_id)
    assert state == "transcribe_history"


@pytest.mark.asyncio
async def test_transcribe_to_new(clean_state, mock_bot, create_message):
    """
    Тест перехода к новой транскрибации.
    
    Проверяет:
    - Отправку сообщения с инструкцией
    - Установку состояния transcribe_upload
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "transcribe")
    message = create_message(user_id, "📝 Новая транскрибация")

    # Act
    await handle_transcribe_menu(message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "Загрузите аудио или видео файл" in args[1]
    state = await get_state(user_id)
    assert state == "transcribe_upload"


@pytest.mark.asyncio
async def test_back_from_transcribe(clean_state, mock_bot, create_message):
    """
    Тест возврата из меню транскрибации в главное меню.
    
    Проверяет:
    - Возврат в главное меню
    - Установку клавиатуры главного меню
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "transcribe")
    message = create_message(user_id, "⬅️ Назад")

    # Act
    await handle_main_menu(message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert isinstance(keyboard, main_menu_keyboard().__class__)
    state = await get_state(user_id)
    assert state == "main_menu"


@pytest.mark.asyncio
async def test_back_from_history(clean_state, mock_bot, create_message):
    """
    Тест возврата из истории в меню транскрибации.
    
    Проверяет:
    - Возврат в меню транскрибации
    - Установку клавиатуры транскрибации
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "transcribe_history")
    message = create_message(user_id, "⬅️ Назад")

    # Act
    await handle_main_menu(message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert isinstance(keyboard, transcribe_keyboard().__class__)
    state = await get_state(user_id)
    assert state == "transcribe" 