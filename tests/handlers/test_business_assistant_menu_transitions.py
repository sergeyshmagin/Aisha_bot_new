"""Тесты для проверки переходов в меню бизнес-ассистента."""

import pytest
from unittest.mock import patch, AsyncMock
from frontend_bot.services.state_manager import (
    get_state,
    clear_all_states,
    set_state,
)
from frontend_bot.keyboards.main_menu import main_menu_keyboard
from frontend_bot.keyboards.business_assistant import business_assistant_keyboard
from frontend_bot.handlers.general import handle_main_menu
from frontend_bot.handlers.business_assistant import (
    handle_business_assistant_menu,
    handle_business_assistant_history,
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
async def test_main_menu_to_business_assistant(
    clean_state,
    mock_bot,
    create_message
):
    """
    Тест перехода из главного меню в меню бизнес-ассистента.
    
    Проверяет:
    - Отправку сообщения с описанием возможностей
    - Установку клавиатуры бизнес-ассистента
    - Установку состояния business_assistant
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "main_menu")
    message = create_message(user_id, "💬 Бизнес-ассистент")

    # Act
    await handle_main_menu(message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "Выберите действие" in args[1]
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert "💭 Новый диалог" in str(keyboard)
    state = await get_state(user_id)
    assert state == "business_assistant"


@pytest.mark.asyncio
async def test_business_assistant_to_history(
    clean_state,
    mock_bot,
    create_message
):
    """
    Тест перехода из меню бизнес-ассистента в историю диалогов.
    
    Проверяет:
    - Отправку сообщения с историей
    - Установку состояния business_assistant_history
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "business_assistant")
    message = create_message(user_id, "📋 История")

    # Act
    await handle_business_assistant_history(message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "История диалогов" in args[1]
    state = await get_state(user_id)
    assert state == "business_assistant_history"


@pytest.mark.asyncio
async def test_business_assistant_to_new_dialog(
    clean_state,
    mock_bot,
    create_message
):
    """
    Тест перехода к новому диалогу.
    
    Проверяет:
    - Отправку сообщения с инструкцией
    - Установку состояния business_assistant_dialog
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "business_assistant")
    message = create_message(user_id, "💭 Новый диалог")

    # Act
    await handle_business_assistant_menu(message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "Опишите вашу задачу" in args[1]
    state = await get_state(user_id)
    assert state == "business_assistant_dialog"


@pytest.mark.asyncio
async def test_back_from_business_assistant(
    clean_state,
    mock_bot,
    create_message
):
    """
    Тест возврата из меню бизнес-ассистента в главное меню.
    
    Проверяет:
    - Возврат в главное меню
    - Установку клавиатуры главного меню
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "business_assistant")
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
    Тест возврата из истории в меню бизнес-ассистента.
    
    Проверяет:
    - Возврат в меню бизнес-ассистента
    - Установку клавиатуры бизнес-ассистента
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "business_assistant_history")
    message = create_message(user_id, "⬅️ Назад")

    # Act
    await handle_main_menu(message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert isinstance(keyboard, business_assistant_keyboard().__class__)
    state = await get_state(user_id)
    assert state == "business_assistant" 