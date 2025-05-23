"""
Тесты для обработчиков аватаров (Фаза 2)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from aiogram.types import CallbackQuery, Message, User as TgUser, Chat, PhotoSize
from aiogram.fsm.context import FSMContext

from app.handlers.avatar import AvatarHandler
from app.handlers.state import AvatarStates
from app.database.models import AvatarType, AvatarGender, Avatar, User


@pytest.fixture
def avatar_handler():
    """Фикстура для AvatarHandler"""
    return AvatarHandler()


@pytest.fixture
def mock_user():
    """Мок пользователя Telegram"""
    return TgUser(
        id=12345,
        is_bot=False,
        first_name="Test",
        username="testuser"
    )


@pytest.fixture
def mock_chat():
    """Мок чата"""
    return Chat(id=12345, type="private")


@pytest.fixture
def mock_callback_query(mock_user, mock_chat):
    """Мок callback query"""
    message = MagicMock()
    message.edit_text = AsyncMock()
    message.chat = mock_chat
    
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = mock_user
    callback.message = message
    callback.answer = AsyncMock()
    callback.data = "avatar_menu"
    
    return callback


@pytest.fixture
def mock_message(mock_user, mock_chat):
    """Мок сообщения"""
    message = MagicMock(spec=Message)
    message.from_user = mock_user
    message.chat = mock_chat
    message.reply = AsyncMock()
    message.text = "Тестовый аватар"
    
    return message


@pytest.fixture
def mock_photo_message(mock_user, mock_chat):
    """Мок сообщения с фотографией"""
    message = MagicMock(spec=Message)
    message.from_user = mock_user
    message.chat = mock_chat
    message.reply = AsyncMock()
    
    # Мок фотографий разных размеров
    photo1 = MagicMock(spec=PhotoSize)
    photo1.file_id = "photo_small"
    photo1.width = 320
    photo1.height = 240
    
    photo2 = MagicMock(spec=PhotoSize)
    photo2.file_id = "photo_large"
    photo2.width = 1280
    photo2.height = 960
    
    message.photo = [photo1, photo2]
    
    return message


@pytest.fixture
def mock_state():
    """Мок FSM состояния"""
    state = AsyncMock(spec=FSMContext)
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    
    return state


@pytest.fixture
def mock_db_user():
    """Мок пользователя из базы данных"""
    user = User(
        id=uuid4(),
        telegram_id="12345",
        first_name="Test",
        username="testuser"
    )
    return user


@pytest.fixture
def mock_avatar():
    """Мок аватара из базы данных"""
    avatar = Avatar(
        id=uuid4(),
        user_id=uuid4(),
        name="Тестовый аватар",
        avatar_type=AvatarType.CHARACTER,
        gender=AvatarGender.MALE
    )
    return avatar


class TestAvatarHandler:
    """Тесты для AvatarHandler"""

    @pytest.mark.asyncio
    async def test_show_avatar_menu_success(
        self, 
        avatar_handler, 
        mock_callback_query, 
        mock_state,
        mock_db_user
    ):
        """Тест успешного показа меню аватаров"""
        
        with patch.object(avatar_handler, 'get_services') as mock_get_services:
            # Настраиваем моки сервисов
            mock_services = {
                'user_service': AsyncMock(),
                'avatar_service': AsyncMock(),
                'photo_service': AsyncMock(),
                'session': AsyncMock()
            }
            
            mock_services['user_service'].get_user_by_telegram_id.return_value = mock_db_user
            mock_services['avatar_service'].get_user_avatars.return_value = []
            
            mock_get_services.return_value = mock_services
            
            # Выполняем тест
            await avatar_handler.show_avatar_menu(mock_callback_query, mock_state)
            
            # Проверяем вызовы
            mock_services['user_service'].get_user_by_telegram_id.assert_called_once_with("12345")
            mock_services['avatar_service'].get_user_avatars.assert_called_once_with(mock_db_user.id)
            mock_state.set_state.assert_called_once_with(AvatarStates.menu)
            mock_callback_query.message.edit_text.assert_called_once()
            mock_callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_show_avatar_menu_user_not_found(
        self, 
        avatar_handler, 
        mock_callback_query, 
        mock_state
    ):
        """Тест показа меню когда пользователь не найден"""
        
        with patch.object(avatar_handler, 'get_services') as mock_get_services:
            mock_services = {
                'user_service': AsyncMock(),
                'avatar_service': AsyncMock(),
            }
            
            mock_services['user_service'].get_user_by_telegram_id.return_value = None
            mock_get_services.return_value = mock_services
            
            await avatar_handler.show_avatar_menu(mock_callback_query, mock_state)
            
            mock_callback_query.answer.assert_called_once_with(
                "❌ Пользователь не найден", 
                show_alert=True
            )

    @pytest.mark.asyncio
    async def test_process_avatar_name_success(
        self, 
        avatar_handler, 
        mock_message, 
        mock_state,
        mock_db_user,
        mock_avatar
    ):
        """Тест успешной обработки имени аватара"""
        
        # Настраиваем состояние
        mock_state.get_data.return_value = {
            'avatar_type': AvatarType.CHARACTER,
            'gender': AvatarGender.MALE
        }
        
        with patch.object(avatar_handler, 'get_services') as mock_get_services:
            mock_services = {
                'user_service': AsyncMock(),
                'avatar_service': AsyncMock(),
            }
            
            mock_services['user_service'].get_user_by_telegram_id.return_value = mock_db_user
            mock_services['avatar_service'].create_avatar.return_value = mock_avatar
            
            mock_get_services.return_value = mock_services
            
            await avatar_handler.process_avatar_name(mock_message, mock_state)
            
            # Проверяем создание аватара
            mock_services['avatar_service'].create_avatar.assert_called_once_with(
                user_id=mock_db_user.id,
                name="Тестовый аватар",
                avatar_type=AvatarType.CHARACTER,
                gender=AvatarGender.MALE
            )
            
            # Проверяем обновление состояния
            mock_state.update_data.assert_called_once()
            mock_state.set_state.assert_called_once_with(AvatarStates.uploading_photos)
            mock_message.reply.assert_called()

    @pytest.mark.asyncio
    async def test_process_avatar_name_validation_error(
        self, 
        avatar_handler, 
        mock_message, 
        mock_state
    ):
        """Тест валидации имени аватара"""
        
        # Тест слишком короткого имени
        mock_message.text = "A"
        
        await avatar_handler.process_avatar_name(mock_message, mock_state)
        
        mock_message.reply.assert_called_once_with(
            "❌ Имя должно содержать минимум 2 символа"
        )

    @pytest.mark.asyncio
    async def test_process_photo_upload_success(
        self, 
        avatar_handler, 
        mock_photo_message, 
        mock_state,
        mock_db_user
    ):
        """Тест успешной загрузки фотографии"""
        
        avatar_id = str(uuid4())
        mock_state.get_data.return_value = {
            'avatar_id': avatar_id,
            'name': 'Тестовый аватар'
        }
        
        with patch.object(avatar_handler, 'get_services') as mock_get_services, \
             patch('app.handlers.avatar.Bot') as mock_bot_class:
            
            # Настраиваем моки
            mock_services = {
                'user_service': AsyncMock(),
                'photo_service': AsyncMock(),
            }
            
            mock_services['user_service'].get_user_by_telegram_id.return_value = mock_db_user
            mock_services['photo_service'].upload_photo.return_value = MagicMock()
            mock_services['photo_service'].get_avatar_photos.return_value = ([], 1)
            
            mock_get_services.return_value = mock_services
            
            # Настраиваем Bot
            mock_bot = AsyncMock()
            mock_bot_class.get_current.return_value = mock_bot
            
            mock_file = MagicMock()
            mock_file.file_path = "photos/test.jpg"
            mock_bot.get_file.return_value = mock_file
            
            mock_photo_data = AsyncMock()
            mock_photo_data.read.return_value = b"fake_photo_data"
            mock_bot.download_file.return_value = mock_photo_data
            
            # Мок сообщения о загрузке
            loading_msg = AsyncMock()
            mock_photo_message.reply.return_value = loading_msg
            
            await avatar_handler.process_photo_upload(mock_photo_message, mock_state)
            
            # Проверяем вызовы
            mock_bot.get_file.assert_called_once_with("photo_large")  # Самое большое фото
            mock_services['photo_service'].upload_photo.assert_called_once()
            loading_msg.edit_text.assert_called()

    @pytest.mark.asyncio
    async def test_start_avatar_creation(
        self, 
        avatar_handler, 
        mock_callback_query, 
        mock_state
    ):
        """Тест начала создания аватара"""
        
        await avatar_handler.start_avatar_creation(mock_callback_query, mock_state)
        
        mock_state.set_state.assert_called_once_with(AvatarStates.selecting_type)
        mock_callback_query.message.edit_text.assert_called_once()
        mock_callback_query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_avatar_type(
        self, 
        avatar_handler, 
        mock_callback_query, 
        mock_state
    ):
        """Тест выбора типа аватара"""
        
        mock_callback_query.data = "avatar_type_character"
        
        await avatar_handler.select_avatar_type(mock_callback_query, mock_state)
        
        mock_state.update_data.assert_called_once_with(avatar_type=AvatarType.CHARACTER)
        mock_state.set_state.assert_called_once_with(AvatarStates.selecting_gender)
        mock_callback_query.message.edit_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_gender(
        self, 
        avatar_handler, 
        mock_callback_query, 
        mock_state
    ):
        """Тест выбора пола аватара"""
        
        mock_callback_query.data = "avatar_gender_male"
        
        await avatar_handler.select_gender(mock_callback_query, mock_state)
        
        mock_state.update_data.assert_called_once_with(gender=AvatarGender.MALE)
        mock_state.set_state.assert_called_once_with(AvatarStates.entering_name)
        mock_callback_query.message.edit_text.assert_called_once()


class TestAvatarHandlerIntegration:
    """Интеграционные тесты для полного цикла создания аватара"""

    @pytest.mark.asyncio
    async def test_full_avatar_creation_flow(
        self, 
        avatar_handler,
        mock_callback_query,
        mock_message,
        mock_state,
        mock_db_user,
        mock_avatar
    ):
        """Тест полного цикла создания аватара"""
        
        with patch.object(avatar_handler, 'get_services') as mock_get_services:
            mock_services = {
                'user_service': AsyncMock(),
                'avatar_service': AsyncMock(),
            }
            
            mock_services['user_service'].get_user_by_telegram_id.return_value = mock_db_user
            mock_services['avatar_service'].create_avatar.return_value = mock_avatar
            mock_services['avatar_service'].get_user_avatars.return_value = []
            
            mock_get_services.return_value = mock_services
            
            # 1. Показ меню
            await avatar_handler.show_avatar_menu(mock_callback_query, mock_state)
            
            # 2. Начало создания
            await avatar_handler.start_avatar_creation(mock_callback_query, mock_state)
            
            # 3. Выбор типа
            mock_callback_query.data = "avatar_type_character"
            await avatar_handler.select_avatar_type(mock_callback_query, mock_state)
            
            # 4. Выбор пола
            mock_callback_query.data = "avatar_gender_male"
            await avatar_handler.select_gender(mock_callback_query, mock_state)
            
            # 5. Ввод имени
            mock_state.get_data.return_value = {
                'avatar_type': AvatarType.CHARACTER,
                'gender': AvatarGender.MALE
            }
            await avatar_handler.process_avatar_name(mock_message, mock_state)
            
            # Проверяем что все этапы прошли успешно
            assert mock_services['avatar_service'].create_avatar.called
            assert mock_state.set_state.call_count >= 4  # Минимум 4 смены состояния 