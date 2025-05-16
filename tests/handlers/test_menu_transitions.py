"""Тесты для проверки переходов между меню."""

import pytest
from unittest.mock import patch, AsyncMock
from frontend_bot.services.state_utils import set_state, get_state, clear_state
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
from frontend_bot.keyboards.reply import photo_menu_keyboard, ai_photographer_keyboard, my_avatars_keyboard
from frontend_bot.handlers.start import handle_start
from frontend_bot.services.shared_menu import send_main_menu

@pytest.fixture
async def clean_state():
    """Фикстура для очистки состояния до и после теста."""
    await clear_state()
    yield
    await clear_state()

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
async def test_start_to_main_menu(clean_state, mock_bot, create_message):
    """
    Тест перехода из /start в главное меню.
    
    Проверяет:
    - Отправку приветственного сообщения
    - Установку клавиатуры главного меню
    - Установку состояния main_menu
    """
    # Arrange
    user_id = 123456789
    message = create_message(user_id, "/start")

    # Act
    await handle_start(message)

    # Assert
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "Добро пожаловать" in args[1]
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert "🧑‍🎨 ИИ фотограф" in str(keyboard)
    state = await get_state(user_id)
    assert state == "main_menu"

@pytest.mark.asyncio
async def test_main_menu_to_ai_photographer(clean_state, mock_bot, create_message):
    """
    Тест перехода из главного меню в меню ИИ фотографа через 'Работа с фото'.
    """
    user_id = 123456789
    await set_state(user_id, "main_menu")
    # Шаг 1: нажимаем '🖼 Работа с фото'
    message = create_message(user_id, "🖼 Работа с фото")
    await send_main_menu(mock_bot, message)
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "Выберите действие" in args[1]
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert "🧑‍🎨 ИИ фотограф" in str(keyboard)
    state = await get_state(user_id)
    assert state == "photo_menu"
    mock_bot.reset_mock()
    # Шаг 2: нажимаем '🧑‍🎨 ИИ фотограф'
    message = create_message(user_id, "🧑‍🎨 ИИ фотограф")
    await send_main_menu(mock_bot, message)
    mock_bot.send_message.assert_called_once()
    args = mock_bot.send_message.call_args[0]
    assert args[0] == user_id
    assert "ИИ фотограф" in args[1]
    keyboard = mock_bot.send_message.call_args[1]['reply_markup']
    assert "🖼 Мои аватары" in str(keyboard)
    state = await get_state(user_id)
    assert state == "ai_photographer"

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
    await set_state(user_id, "ai_photographer")
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
    await set_state(user_id, "my_avatars")
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
    await set_state(user_id, "my_avatars")
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
    await set_state(user_id, "invalid_state")
    message = create_message(user_id, "🧑‍🎨 ИИ фотограф")

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