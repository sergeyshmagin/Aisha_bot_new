"""Тесты для проверки переходов между меню."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
from frontend_bot.keyboards.reply import photo_menu_keyboard, ai_photographer_keyboard, my_avatars_keyboard
from frontend_bot.handlers.start import handle_start
from frontend_bot.services.shared_menu import send_main_menu
from frontend_bot.bot_instance import bot

@pytest.fixture
async def clean_state():
    """Фикстура для очистки состояния до и после теста."""
    user_id = 123456
    await clear_state(user_id)
    yield
    await clear_state(user_id)

@pytest.fixture
def mock_bot():
    """Мок для бота."""
    with patch("frontend_bot.bot_instance.bot") as mock:
        mock.send_message = AsyncMock()
        mock.send_chat_action = AsyncMock()
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
async def test_start_to_main_menu(clean_state, mock_bot):
    """Тест перехода из стартового меню в главное."""
    user_id = 123456
    message = MagicMock()
    message.from_user.id = user_id
    message.chat.id = user_id
    message.text = "/start"
    
    await handle_start(message)
    
    assert await get_state(user_id) == "main_menu"
    mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_main_menu_to_ai_photographer(clean_state, mock_bot):
    """Тест перехода из главного меню в меню AI-фотографа."""
    user_id = 123456
    message = MagicMock()
    message.from_user.id = user_id
    message.chat.id = user_id
    message.text = "AI-фотограф"
    
    await set_state(user_id, "main_menu", session)
    await handle_main_menu(message)
    
    assert await get_state(user_id) == "ai_photographer"
    mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_ai_photographer_to_my_avatars(clean_state, mock_bot, create_message):
    """
    Тест перехода из меню ИИ фотографа в меню Мои аватары.
    
    Проверяет:
    - Отправку сообщения с описанием возможностей
    - Установку клавиатуры Мои аватары
    - Установку состояния my_avatars
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "ai_photographer", session)
    message = create_message(user_id, "👁 Мои аватары")

    # Act
    await send_main_menu(mock_bot, message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert "📷 Создать аватар" in str(keyboard)
    state = await get_state(user_id)
    assert state == "my_avatars"

@pytest.mark.asyncio
async def test_my_avatars_to_create_avatar(clean_state, mock_bot, create_message):
    """
    Тест перехода из меню Мои аватары к созданию аватара.
    
    Проверяет:
    - Отправку сообщения с инструкцией загрузки фото
    - Установку состояния avatar_photo_upload
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "my_avatars", session)
    message = create_message(user_id, "📷 Создать аватар")

    # Act
    # await handle_create_avatar(message)  # TODO: заменить на сервисную функцию создания аватара
    pass

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "Загрузите фотографию" in args[1]
    state = await get_state(user_id)
    assert state == "avatar_photo_upload"

@pytest.mark.asyncio
async def test_back_to_previous_menu(clean_state, mock_bot, create_message):
    """
    Тест возврата в предыдущее меню по кнопке Назад.
    
    Проверяет:
    - Возврат из my_avatars в ai_photographer
    - Возврат из ai_photographer в main_menu
    """
    # Arrange
    user_id = 123456789
    
    # Тест возврата из my_avatars в ai_photographer
    await set_state(user_id, "my_avatars", session)
    message = create_message(user_id, "⬅️ Назад")
    
    # Act & Assert для первого перехода
    await send_main_menu(mock_bot, message)
    state = await get_state(user_id)
    assert state == "ai_photographer"
    
    # Тест возврата из ai_photographer в main_menu
    message = create_message(user_id, "⬅️ Назад")
    
    # Act & Assert для второго перехода
    await send_main_menu(mock_bot, message)
    state = await get_state(user_id)
    assert state == "main_menu"

@pytest.mark.asyncio
async def test_invalid_state_transition(clean_state, mock_bot, create_message):
    """
    Тест обработки некорректного перехода.
    
    Проверяет:
    - Возврат в главное меню при некорректном состоянии
    - Отправку сообщения об ошибке
    """
    # Arrange
    user_id = 123456789
    await set_state(user_id, "invalid_state", session)
    message = create_message(user_id, "��‍🎨 ИИ фотограф")

    # Act
    await send_main_menu(mock_bot, message)

    # Assert
    mock_bot.send_message.assert_called_once_with(
        user_id,
        "Что-то пошло не так. Возвращаемся в главное меню...",
        reply_markup=main_menu_keyboard()
    )
    state = await get_state(user_id)
    assert state == "main_menu"

# TODO: Перевести на state_utils с поддержкой PostgreSQL 