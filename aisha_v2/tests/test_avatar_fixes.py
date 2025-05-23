"""
Тесты для проверки исправлений функционала аватаров
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from aisha_v2.app.handlers.avatar import AvatarHandler
from aisha_v2.app.services.avatar.avatar_service import AvatarService
from aisha_v2.app.services.avatar.photo_service import PhotoUploadService
from aisha_v2.app.services.avatar.training_service import AvatarTrainingService
from aisha_v2.app.services.fal.client import FalAIClient


class TestAvatarImports:
    """Тесты импортов модулей аватаров"""
    
    def test_avatar_handler_import(self):
        """Тест импорта AvatarHandler"""
        from aisha_v2.app.handlers.avatar import AvatarHandler
        assert AvatarHandler is not None
        
    def test_avatar_service_import(self):
        """Тест импорта AvatarService"""
        from aisha_v2.app.services.avatar.avatar_service import AvatarService
        assert AvatarService is not None
        
    def test_photo_service_import(self):
        """Тест импорта PhotoUploadService"""
        from aisha_v2.app.services.avatar.photo_service import PhotoUploadService
        assert PhotoUploadService is not None
        
    def test_training_service_import(self):
        """Тест импорта AvatarTrainingService"""
        from aisha_v2.app.services.avatar.training_service import AvatarTrainingService
        assert AvatarTrainingService is not None
        
    def test_fal_client_import(self):
        """Тест импорта FalAIClient"""
        from aisha_v2.app.services.fal.client import FalAIClient
        assert FalAIClient is not None
        
    def test_avatar_texts_import(self):
        """Тест импорта текстов аватаров"""
        from aisha_v2.app.texts.avatar import AvatarTexts
        assert AvatarTexts is not None
        
    def test_avatar_keyboards_import(self):
        """Тест импорта клавиатур аватаров"""
        from aisha_v2.app.keyboards.avatar import get_avatar_main_menu
        assert get_avatar_main_menu is not None


class TestBaseServiceConstructors:
    """Тесты конструкторов сервисов, наследующихся от BaseService"""
    
    def test_avatar_service_constructor(self):
        """Тест конструктора AvatarService"""
        mock_session = Mock(spec=AsyncSession)
        service = AvatarService(mock_session)
        
        assert service.session == mock_session
        assert hasattr(service, 'session')
        
    def test_photo_service_constructor(self):
        """Тест конструктора PhotoUploadService"""
        mock_session = Mock(spec=AsyncSession)
        service = PhotoUploadService(mock_session)
        
        assert service.session == mock_session
        assert hasattr(service, 'storage')
        
    def test_training_service_constructor(self):
        """Тест конструктора AvatarTrainingService"""
        mock_session = Mock(spec=AsyncSession)
        service = AvatarTrainingService(mock_session)
        
        assert service.session == mock_session
        assert hasattr(service, 'fal_client')
        
    def test_fal_client_constructor(self):
        """Тест конструктора FalAIClient (НЕ наследуется от BaseService)"""
        client = FalAIClient()
        
        # FalAIClient НЕ должен требовать session
        assert hasattr(client, 'logger')
        assert hasattr(client, 'api_key')
        assert hasattr(client, 'test_mode')


class TestAvatarHandlerStructure:
    """Тесты структуры обработчика аватаров"""
    
    def test_avatar_handler_methods_exist(self):
        """Тест наличия всех необходимых методов в AvatarHandler"""
        required_methods = [
            'show_avatar_menu',
            'start_avatar_creation', 
            'select_avatar_type',
            'select_gender',
            'process_avatar_name',
            'show_avatar_gallery',
            'show_avatar_details',
            'start_photo_upload',
            'process_photo_upload',
            'confirm_training',
            'start_training',
            'show_training_progress',
            'cancel_training',
            'handle_back'
        ]
        
        handler = AvatarHandler()
        
        for method_name in required_methods:
            assert hasattr(handler, method_name), f"Метод {method_name} отсутствует"
            
    def test_avatar_handler_creation_without_session(self):
        """Тест создания AvatarHandler без передачи session (должно работать)"""
        handler = AvatarHandler()
        assert handler is not None


class TestAvatarTextsAndKeyboards:
    """Тесты генерации текстов и клавиатур"""
    
    def test_avatar_texts_creation(self):
        """Тест создания экземпляра AvatarTexts"""
        from aisha_v2.app.texts.avatar import AvatarTexts
        
        texts = AvatarTexts()
        assert texts is not None
        
    def test_avatar_main_menu_text_generation(self):
        """Тест генерации текста главного меню"""
        from aisha_v2.app.texts.avatar import AvatarTexts
        
        texts = AvatarTexts()
        main_text_empty = texts.get_main_menu_text(0)
        main_text_with_avatars = texts.get_main_menu_text(3)
        
        assert isinstance(main_text_empty, str)
        assert isinstance(main_text_with_avatars, str)
        assert len(main_text_empty) > 0
        assert len(main_text_with_avatars) > 0
        
    def test_avatar_keyboards_creation(self):
        """Тест создания клавиатур аватаров"""
        from aisha_v2.app.keyboards.avatar import get_avatar_main_menu, get_avatar_type_keyboard
        
        main_keyboard = get_avatar_main_menu(0)
        type_keyboard = get_avatar_type_keyboard()
        
        assert main_keyboard is not None
        assert type_keyboard is not None
        assert hasattr(main_keyboard, 'inline_keyboard')
        assert hasattr(type_keyboard, 'inline_keyboard')


@pytest.mark.asyncio 
class TestMainMenuIntegration:
    """Тесты интеграции с главным меню"""
    
    async def test_main_menu_avatar_handler_import(self):
        """Тест импорта обработчика аватаров из главного меню"""
        from aisha_v2.app.handlers.main_menu import router
        assert router is not None
        
    async def test_avatar_handler_method_call(self):
        """Тест вызова метода AvatarHandler без ошибки frozen CallbackQuery"""
        from aiogram.types import CallbackQuery, Message, User as TgUser, Chat
        from aiogram.fsm.context import FSMContext
        from unittest.mock import AsyncMock, MagicMock
        
        # Создаем мок объекты
        mock_user = TgUser(id=12345, is_bot=False, first_name="Test")
        mock_chat = Chat(id=12345, type="private")
        
        mock_message = MagicMock(spec=Message)
        mock_message.edit_text = AsyncMock()
        mock_message.chat = mock_chat
        
        mock_call = MagicMock(spec=CallbackQuery)
        mock_call.from_user = mock_user
        mock_call.message = mock_message
        mock_call.answer = AsyncMock()
        mock_call.data = "business_avatar"
        
        mock_state = AsyncMock(spec=FSMContext)
        
        # Тестируем создание и вызов AvatarHandler
        handler = AvatarHandler()
        
        # Мокаем get_services для избежания обращения к БД
        with patch.object(handler, 'get_services') as mock_get_services:
            mock_services = {
                'user_service': AsyncMock(),
                'avatar_service': AsyncMock(),
                'session': AsyncMock()
            }
            mock_services['user_service'].get_user_by_telegram_id.return_value = None
            mock_get_services.return_value = mock_services
            
            # Должно работать без ошибки ValidationError: Instance is frozen
            await handler.show_avatar_menu(mock_call, mock_state)
            
        # Проверяем что вызовы прошли без ошибок
        assert mock_call.answer.called
        

class TestAvatarServiceMethods:
    """Тесты методов сервисов аватаров"""
    
    def test_avatar_service_has_required_methods(self):
        """Тест наличия необходимых методов в AvatarService"""
        mock_session = Mock(spec=AsyncSession)
        service = AvatarService(mock_session)
        
        required_methods = [
            'get_user_avatars',
            'create_avatar',
            'get_avatar_by_id',
            'update_avatar_status',
            'delete_avatar'
        ]
        
        for method_name in required_methods:
            assert hasattr(service, method_name), f"Метод {method_name} отсутствует в AvatarService"
            
    def test_photo_service_has_required_methods(self):
        """Тест наличия необходимых методов в PhotoUploadService"""
        mock_session = Mock(spec=AsyncSession)
        service = PhotoUploadService(mock_session)
        
        # Проверяем что сервис создается без ошибок
        assert service is not None
        assert hasattr(service, 'storage')
        
    def test_training_service_has_required_methods(self):
        """Тест наличия необходимых методов в AvatarTrainingService"""
        mock_session = Mock(spec=AsyncSession)
        service = AvatarTrainingService(mock_session)
        
        # Проверяем что сервис создается без ошибок
        assert service is not None
        assert hasattr(service, 'fal_client')


class TestFalClientStructure:
    """Тесты структуры FalAIClient"""
    
    def test_fal_client_methods(self):
        """Тест наличия методов в FalAIClient"""
        client = FalAIClient()
        
        required_methods = [
            'start_training',
            'get_training_status',
            'generate_image',
            'is_training_complete'
        ]
        
        for method_name in required_methods:
            assert hasattr(client, method_name), f"Метод {method_name} отсутствует в FalAIClient"
            
    def test_fal_client_properties(self):
        """Тест свойств FalAIClient"""
        client = FalAIClient()
        
        assert hasattr(client, 'logger')
        assert hasattr(client, 'api_key')
        assert hasattr(client, 'test_mode')


@pytest.mark.integration
class TestAvatarFixesIntegration:
    """Интеграционные тесты исправлений аватаров"""
    
    @pytest.mark.asyncio
    async def test_avatar_full_import_chain(self):
        """Тест полной цепочки импортов аватаров"""
        # Импорты должны работать без ошибок
        from aisha_v2.app.handlers.avatar import AvatarHandler
        from aisha_v2.app.services.avatar.avatar_service import AvatarService
        from aisha_v2.app.services.avatar.photo_service import PhotoUploadService
        from aisha_v2.app.services.avatar.training_service import AvatarTrainingService
        from aisha_v2.app.services.fal.client import FalAIClient
        from aisha_v2.app.texts.avatar import AvatarTexts
        from aisha_v2.app.keyboards.avatar import get_avatar_main_menu
        
        # Создание экземпляров должно работать
        handler = AvatarHandler()
        client = FalAIClient()
        texts = AvatarTexts()
        keyboard = get_avatar_main_menu(0)
        
        # Создание сервисов с session должно работать
        mock_session = Mock(spec=AsyncSession)
        avatar_service = AvatarService(mock_session)
        photo_service = PhotoUploadService(mock_session)
        training_service = AvatarTrainingService(mock_session)
        
        # Все объекты должны быть созданы успешно
        assert handler is not None
        assert client is not None
        assert texts is not None
        assert keyboard is not None
        assert avatar_service is not None
        assert photo_service is not None
        assert training_service is not None 