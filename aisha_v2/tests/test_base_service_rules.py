"""
Тесты для проверки правил BaseService из best practices
"""
import pytest
from unittest.mock import Mock
from sqlalchemy.ext.asyncio import AsyncSession

from aisha_v2.app.services.base import BaseService


class TestBaseServiceRules:
    """Тесты правил наследования от BaseService"""
    
    def test_base_service_requires_session(self):
        """Тест что BaseService требует session в конструкторе"""
        
        # Попытка создать BaseService без session должна вызвать ошибку
        with pytest.raises(TypeError, match="missing.*required.*positional argument.*session"):
            BaseService()  # ❌ Без session
            
    def test_base_service_with_session_works(self):
        """Тест что BaseService работает с session"""
        mock_session = Mock(spec=AsyncSession)
        
        # Создание с session должно работать
        service = BaseService(mock_session)  # ✅ С session
        
        assert service.session == mock_session
        assert hasattr(service, 'session')
        
    def test_derived_service_correct_constructor(self):
        """Тест правильного конструктора производного сервиса"""
        
        class CorrectService(BaseService):
            def __init__(self, session: AsyncSession):
                super().__init__(session)  # ✅ Передаем session
                self.session = session
                
        mock_session = Mock(spec=AsyncSession)
        service = CorrectService(mock_session)
        
        assert service.session == mock_session
        
    def test_derived_service_incorrect_constructor_fails(self):
        """Тест неправильного конструктора производного сервиса"""
        
        class IncorrectService(BaseService):
            def __init__(self, session: AsyncSession):
                super().__init__()  # ❌ НЕ передаем session
                self.session = session
                
        mock_session = Mock(spec=AsyncSession)
        
        # Должна возникнуть ошибка
        with pytest.raises(TypeError, match="missing.*required.*positional argument.*session"):
            IncorrectService(mock_session)
            
    def test_utility_class_should_not_inherit_from_base_service(self):
        """Тест что утилитарные классы НЕ должны наследоваться от BaseService"""
        
        # ✅ Правильно - утилитарный класс без BaseService
        class UtilityClass:
            def __init__(self):
                self.some_config = "config"
                
        utility = UtilityClass()
        assert utility is not None
        assert not isinstance(utility, BaseService)
        
        # ❌ Неправильно - утилитарный класс наследуется от BaseService
        class BadUtilityClass(BaseService):
            def __init__(self):
                super().__init__()  # Ошибка - нет session
                
        with pytest.raises(TypeError):
            BadUtilityClass()


class TestServiceClassification:
    """Тесты классификации сервисов"""
    
    def test_database_service_should_inherit_from_base_service(self):
        """Тест что сервисы для работы с БД должны наследоваться от BaseService"""
        
        class DatabaseService(BaseService):
            def __init__(self, session: AsyncSession):
                super().__init__(session)
                
            async def get_data(self):
                # Работа с БД
                pass
                
        mock_session = Mock(spec=AsyncSession)
        service = DatabaseService(mock_session)
        
        assert isinstance(service, BaseService)
        assert service.session == mock_session
        
    def test_api_client_should_not_inherit_from_base_service(self):
        """Тест что API клиенты НЕ должны наследоваться от BaseService"""
        
        class APIClient:
            def __init__(self, api_key: str):
                self.api_key = api_key
                
            async def make_request(self):
                # Работа с внешним API
                pass
                
        client = APIClient("test_key")
        
        assert not isinstance(client, BaseService)
        assert client.api_key == "test_key"
        
    def test_helper_class_should_not_inherit_from_base_service(self):
        """Тест что вспомогательные классы НЕ должны наследоваться от BaseService"""
        
        class HelperClass:
            def __init__(self):
                self.logger = "logger"
                
            def format_data(self, data):
                return f"formatted: {data}"
                
        helper = HelperClass()
        
        assert not isinstance(helper, BaseService)
        assert helper.logger == "logger"


class TestBaseServiceBestPractices:
    """Тесты лучших практик BaseService"""
    
    def test_service_constructor_pattern(self):
        """Тест правильного паттерна конструктора сервиса"""
        
        class WellDesignedService(BaseService):
            """Пример хорошо спроектированного сервиса"""
            
            def __init__(self, session: AsyncSession):
                super().__init__(session)  # ✅ Передаем session
                self.session = session
                
                # Дополнительная инициализация если нужна
                self.cache = {}
                
        mock_session = Mock(spec=AsyncSession)
        service = WellDesignedService(mock_session)
        
        assert service.session == mock_session
        assert hasattr(service, 'cache')
        assert isinstance(service.cache, dict)
        
    def test_multiple_services_creation(self):
        """Тест создания множества сервисов"""
        
        class ServiceA(BaseService):
            def __init__(self, session: AsyncSession):
                super().__init__(session)
                
        class ServiceB(BaseService):
            def __init__(self, session: AsyncSession):
                super().__init__(session)
                
        class ServiceC(BaseService):
            def __init__(self, session: AsyncSession):
                super().__init__(session)
                
        mock_session = Mock(spec=AsyncSession)
        
        # Все сервисы должны создаваться без ошибок
        service_a = ServiceA(mock_session)
        service_b = ServiceB(mock_session)
        service_c = ServiceC(mock_session)
        
        assert all([
            isinstance(service_a, BaseService),
            isinstance(service_b, BaseService),
            isinstance(service_c, BaseService),
        ])
        
    def test_service_with_additional_dependencies(self):
        """Тест сервиса с дополнительными зависимостями"""
        
        class ServiceWithDependencies(BaseService):
            def __init__(self, session: AsyncSession, api_client=None, cache=None):
                super().__init__(session)  # ✅ Сначала передаем session
                self.session = session
                self.api_client = api_client
                self.cache = cache or {}
                
        mock_session = Mock(spec=AsyncSession)
        mock_api_client = Mock()
        
        service = ServiceWithDependencies(
            session=mock_session,
            api_client=mock_api_client,
            cache={"key": "value"}
        )
        
        assert service.session == mock_session
        assert service.api_client == mock_api_client
        assert service.cache["key"] == "value"


class TestErrorMessages:
    """Тесты сообщений об ошибках"""
    
    def test_missing_session_error_message(self):
        """Тест сообщения об ошибке отсутствия session"""
        
        class BadService(BaseService):
            def __init__(self, session: AsyncSession):
                super().__init__()  # ❌ Забыли передать session
                
        mock_session = Mock(spec=AsyncSession)
        
        with pytest.raises(TypeError) as exc_info:
            BadService(mock_session)
            
        error_message = str(exc_info.value)
        assert "missing" in error_message.lower()
        assert "session" in error_message.lower()
        
    def test_helpful_error_context(self):
        """Тест полезного контекста ошибки"""
        
        # Документируем типичную ошибку для разработчиков
        common_mistake_example = """
        # ❌ ЧАСТАЯ ОШИБКА:
        class MyService(BaseService):
            def __init__(self, session: AsyncSession):
                super().__init__()  # Забыли передать session!
                self.session = session
        """
        
        correct_example = """
        # ✅ ПРАВИЛЬНО:
        class MyService(BaseService):
            def __init__(self, session: AsyncSession):
                super().__init__(session)  # Передаем session
                self.session = session
        """
        
        # Проверяем что у нас есть документация
        assert "❌" in common_mistake_example
        assert "✅" in correct_example
        assert "super().__init__(session)" in correct_example


@pytest.mark.integration
class TestRealWorldServiceExamples:
    """Тесты реальных примеров сервисов из проекта"""
    
    def test_avatar_service_pattern(self):
        """Тест паттерна AvatarService"""
        
        # Имитируем структуру AvatarService
        class MockAvatarService(BaseService):
            def __init__(self, session: AsyncSession):
                super().__init__(session)  # ✅ Правильно
                self.session = session
                
        mock_session = Mock(spec=AsyncSession)
        service = MockAvatarService(mock_session)
        
        assert service.session == mock_session
        
    def test_fal_client_pattern(self):
        """Тест паттерна FalAIClient (НЕ наследуется от BaseService)"""
        
        # FalAIClient - утилитарный класс для API
        class MockFalAIClient:
            def __init__(self):
                self.api_key = "test_key"
                self.test_mode = True
                
        client = MockFalAIClient()
        
        assert not isinstance(client, BaseService)
        assert client.api_key == "test_key"
        assert client.test_mode is True
        
    def test_mixed_service_architecture(self):
        """Тест смешанной архитектуры сервисов"""
        
        # Сервис для БД
        class DataService(BaseService):
            def __init__(self, session: AsyncSession):
                super().__init__(session)
                
        # API клиент
        class APIClient:
            def __init__(self, api_key: str):
                self.api_key = api_key
                
        # Утилитарный класс
        class Helper:
            def __init__(self):
                self.utils = {}
                
        mock_session = Mock(spec=AsyncSession)
        
        # Создаем экземпляры
        data_service = DataService(mock_session)
        api_client = APIClient("key")
        helper = Helper()
        
        # Проверяем типы
        assert isinstance(data_service, BaseService)
        assert not isinstance(api_client, BaseService)
        assert not isinstance(helper, BaseService)
        
        # Проверяем что все работает
        assert data_service.session == mock_session
        assert api_client.api_key == "key"
        assert isinstance(helper.utils, dict) 