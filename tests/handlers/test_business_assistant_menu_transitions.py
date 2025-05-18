"""Тесты для проверки переходов в меню бизнес-ассистента."""

import pytest
from unittest.mock import patch, AsyncMock
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
from frontend_bot.keyboards.reply import business_assistant_keyboard
from frontend_bot.services.shared_menu import send_main_menu
from tests.handlers.test_handlers import (
    handle_business_assistant_menu,
    handle_business_assistant_history,
    handle_business_assistant_new_dialog,
    handle_business_assistant_back,
)
import sys
import types


@pytest.fixture
async def clean_state():
    """Фикстура для очистки состояния до и после теста."""
    # TODO: Перевести на state_utils с поддержкой PostgreSQL
    yield


@pytest.fixture
def mock_bot():
    """Фикстура для асинхронного мока бота."""
    return AsyncMock()


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


@pytest.fixture(autouse=True)
def mock_state_manager(monkeypatch):
    """Мокает _load_states и _save_states на in-memory dict для изоляции FSM в тестах."""
    state = {}
    async def _load_states():
        return state.copy()
    async def _save_states(new_state):
        state.clear()
        state.update(new_state)
    monkeypatch.setattr("frontend_bot.services.state_manager._load_states", _load_states)
    monkeypatch.setattr("frontend_bot.services.state_manager._save_states", _save_states)
    yield


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
    # TODO: Перевести на state_utils с поддержкой PostgreSQL
    # await set_state(user_id, "main_menu")
    message = create_message(user_id, "💬 Бизнес-ассистент")

    # Act
    await handle_business_assistant_menu(mock_bot, message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "Выберите действие" in args[1]
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert any("💭 Новый диалог" in btn.text for row in keyboard.keyboard for btn in row)
    # TODO: Перевести на state_utils с поддержкой PostgreSQL
    # state = await get_state(user_id)
    # assert state == "business_assistant"


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
    # TODO: Перевести на state_utils с поддержкой PostgreSQL
    # await set_state(user_id, "business_assistant")
    message = create_message(user_id, "📋 История")

    # Act
    await handle_business_assistant_history(mock_bot, message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "История диалогов" in args[1]
    # TODO: Перевести на state_utils с поддержкой PostgreSQL
    # state = await get_state(user_id)
    # assert state == "business_assistant_history"


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
    # TODO: Перевести на state_utils с поддержкой PostgreSQL
    # await set_state(user_id, "business_assistant")
    message = create_message(user_id, "💭 Новый диалог")

    # Act
    await handle_business_assistant_new_dialog(mock_bot, message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "Опишите вашу задачу" in args[1]
    # TODO: Перевести на state_utils с поддержкой PostgreSQL
    # state = await get_state(user_id)
    # assert state == "business_assistant_dialog"


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
    # TODO: Перевести на state_utils с поддержкой PostgreSQL
    # await set_state(user_id, "business_assistant")
    message = create_message(user_id, "⬅️ Назад")

    # Act
    await handle_business_assistant_back(mock_bot, message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert isinstance(keyboard, main_menu_keyboard().__class__)
    # TODO: Перевести на state_utils с поддержкой PostgreSQL
    # state = await get_state(user_id)
    # assert state == "main_menu"


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
    # TODO: Перевести на state_utils с поддержкой PostgreSQL
    # await set_state(user_id, "business_assistant_history")
    message = create_message(user_id, "⬅️ Назад")

    # Act
    await handle_business_assistant_back(mock_bot, message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert any("💭 Новый диалог" in btn for row in keyboard.keyboard for btn in row)
    # TODO: Перевести на state_utils с поддержкой PostgreSQL
    # state = await get_state(user_id)
    # assert state == "business_assistant" 