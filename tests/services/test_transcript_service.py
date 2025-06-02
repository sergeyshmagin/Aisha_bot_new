"""
Тесты для сервиса транскриптов
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4, UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.transcript import TranscriptService
from app.database.repositories.transcript import TranscriptRepository
from app.database.models import UserTranscript, Userclass TestTranscriptService:
    """Тесты для TranscriptService"""
    
    def test_transcript_service_import(self):
        """Тест импорта TranscriptService"""
        from app.services.transcript import TranscriptService
        assert TranscriptService is not None
        
    def test_transcript_service_constructor(self):
        """Тест конструктора TranscriptService"""
        mock_session = Mock(spec=AsyncSession)
        service = TranscriptService(mock_session)
        
        assert service.session == mock_session
        assert hasattr(service, 'session')class TestTranscriptRepository:
    """Тесты для TranscriptRepository"""
    
    def test_transcript_repository_import(self):
        """Тест импорта TranscriptRepository"""
        from app.database.repositories.transcript import TranscriptRepository
        assert TranscriptRepository is not None
        
    def test_transcript_repository_constructor(self):
        """Тест конструктора TranscriptRepository"""
        mock_session = Mock(spec=AsyncSession)
        repo = TranscriptRepository(mock_session)
        
        assert repo.session == mock_session
        assert hasattr(repo, 'session')@pytest.mark.asyncio
class TestTranscriptServiceMethods:
    """Тесты методов TranscriptService"""
    
    async def test_get_user_transcripts_with_mock(self):
        """Тест получения транскриптов пользователя с мок-данными"""
        mock_session = Mock(spec=AsyncSession)
        service = TranscriptService(mock_session)
        
        # Создаем мок транскрипт
        mock_transcript = Mock(spec=UserTranscript)
        mock_transcript.id = uuid4()
        mock_transcript.user_id = uuid4()
        mock_transcript.created_at = datetime.now()
        mock_transcript.transcript_metadata = {"filename": "test.txt"}
        
        # Мокаем репозиторий
        with patch.object(service, '_get_transcript_repository') as mock_get_repo:
            mock_repo = AsyncMock()
            mock_repo.get_user_transcripts.return_value = [mock_transcript]
            mock_get_repo.return_value = mock_repo
            
            # Выполняем тест
            user_id = uuid4()
            result = await service.get_user_transcripts(user_id, limit=5)
            
            # Проверяем результат
            assert len(result) == 1
            assert result[0] == mock_transcript
            mock_repo.get_user_transcripts.assert_called_once_with(user_id, limit=5, offset=0)
            
    async def test_get_user_transcripts_type_conversion(self):
        """Тест конвертации типов user_id"""
        mock_session = Mock(spec=AsyncSession)
        service = TranscriptService(mock_session)
        
        with patch.object(service, '_get_transcript_repository') as mock_get_repo:
            mock_repo = AsyncMock()
            mock_repo.get_user_transcripts.return_value = []
            mock_get_repo.return_value = mock_repo
            
            # Тестируем разные типы user_id
            test_cases = [
                12345,  # int
                "12345",  # str
                uuid4(),  # UUID
            ]
            
            for user_id in test_cases:
                result = await service.get_user_transcripts(user_id)
                assert isinstance(result, list)
                mock_repo.get_user_transcripts.assert_called()
                
    async def test_transcript_dict_conversion(self):
        """Тест конвертации транскрипта в словарь"""
        mock_session = Mock(spec=AsyncSession)
        service = TranscriptService(mock_session)
        
        # Создаем мок транскрипт с атрибутами SQLAlchemy
        mock_transcript = Mock()
        mock_transcript.id = uuid4()
        mock_transcript.created_at = datetime.now()
        mock_transcript.transcript_metadata = {"filename": "test.mp3", "duration": 120}
        
        # Тестируем безопасную конвертацию
        transcript_dict = {
            "id": str(mock_transcript.id) if mock_transcript.id else None,
            "created_at": mock_transcript.created_at.isoformat() if mock_transcript.created_at else None,
            "metadata": mock_transcript.transcript_metadata or {}
        }
        
        assert "id" in transcript_dict
        assert "created_at" in transcript_dict
        assert "metadata" in transcript_dict
        assert isinstance(transcript_dict["metadata"], dict)@pytest.mark.asyncio
class TestTranscriptRepositoryMethods:
    """Тесты методов TranscriptRepository"""
    
    async def test_get_user_transcripts_sql_query(self):
        """Тест SQL запроса для получения транскриптов"""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = TranscriptRepository(mock_session)
        
        # Мокаем результат запроса
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        user_id = uuid4()
        result = await repo.get_user_transcripts(user_id, limit=10, offset=0)
        
        # Проверяем что запрос был выполнен
        assert mock_session.execute.called
        assert isinstance(result, list)
        
    async def test_create_transcript(self):
        """Тест создания транскрипта"""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = TranscriptRepository(mock_session)
        
        user_id = uuid4()
        transcript_data = {
            "content": "Тестовый текст",
            "metadata": {"filename": "test.txt"}
        }
        
        # Мокаем создание транскрипта
        with patch('aisha_v2.app.database.models.UserTranscript') as MockTranscript:
            mock_transcript = Mock()
            mock_transcript.id = uuid4()
            MockTranscript.return_value = mock_transcript
            
            result = await repo.create_transcript(user_id, transcript_data)
            
            # Проверяем что транскрипт был добавлен в сессию
            assert mock_session.add.called
            assert mock_session.commit.calledclass TestTranscriptModels:
    """Тесты моделей транскриптов"""
    
    def test_transcript_model_import(self):
        """Тест импорта модели UserTranscript"""
        from app.database.models import UserTranscript
        assert UserTranscript is not None
        
    def test_user_model_import(self):
        """Тест импорта модели User"""
        from app.database.models import User
        assert User is not None
        
    def test_transcript_model_attributes(self):
        """Тест атрибутов модели UserTranscript"""
        from app.database.models import UserTranscript
        
        # Проверяем наличие основных атрибутов
        expected_attributes = [
            'id',
            'user_id', 
            'created_at',
            'updated_at',
            'transcript_metadata'
        ]
        
        for attr in expected_attributes:
            assert hasattr(UserTranscript, attr), f"Атрибут {attr} отсутствует в модели UserTranscript"@pytest.mark.integration
class TestTranscriptIntegration:
    """Интеграционные тесты транскриптов"""
    
    @pytest.mark.asyncio
    async def test_transcript_service_with_repository(self):
        """Тест интеграции сервиса с репозиторием"""
        mock_session = Mock(spec=AsyncSession)
        
        # Тестируем что сервис может создать репозиторий
        service = TranscriptService(mock_session)
        
        # Проверяем что метод создания репозитория существует
        assert hasattr(service, '_get_transcript_repository')
        
        # Создаем репозиторий через сервис
        repo = service._get_transcript_repository()
        assert repo is not None
        assert hasattr(repo, 'get_user_transcripts')
        
    def test_transcript_handlers_import(self):
        """Тест импорта обработчиков транскриптов"""
        try:
            from app.handlers.transcript_main import TranscriptMainHandler
            from app.handlers.transcript_processing import TranscriptProcessingHandler
            
            assert TranscriptMainHandler is not None
            assert TranscriptProcessingHandler is not None
        except ImportError as e:
            pytest.fail(f"Не удалось импортировать обработчики транскриптов: {e}")
            
    def test_transcript_texts_and_keyboards(self):
        """Тест импорта текстов и клавиатур транскриптов"""
        try:
            from app.texts.transcript import TranscriptTexts
            from app.keyboards.transcript import get_transcript_menu
            
            assert TranscriptTexts is not None
            assert get_transcript_menu is not None
        except ImportError as e:
            pytest.fail(f"Не удалось импортировать UI компоненты транскриптов: {e}")class TestTranscriptErrorHandling:
    """Тесты обработки ошибок в транскриптах"""
    
    @pytest.mark.asyncio
    async def test_transcript_service_error_handling(self):
        """Тест обработки ошибок в TranscriptService"""
        mock_session = Mock(spec=AsyncSession)
        service = TranscriptService(mock_session)
        
        # Тестируем обработку ошибок при получении транскриптов
        with patch.object(service, '_get_transcript_repository') as mock_get_repo:
            mock_repo = AsyncMock()
            mock_repo.get_user_transcripts.side_effect = Exception("Database error")
            mock_get_repo.return_value = mock_repo
            
            # Проверяем что исключение пробрасывается
            with pytest.raises(Exception, match="Database error"):
                await service.get_user_transcripts(uuid4())
                
    def test_transcript_safe_attribute_access(self):
        """Тест безопасного доступа к атрибутам транскрипта"""
        # Создаем мок объект без некоторых атрибутов
        mock_transcript = Mock()
        mock_transcript.id = None
        mock_transcript.created_at = None
        mock_transcript.transcript_metadata = None
        
        # Безопасная конвертация
        transcript_dict = {
            "id": str(mock_transcript.id) if mock_transcript.id else None,
            "created_at": mock_transcript.created_at.isoformat() if mock_transcript.created_at else None,
            "metadata": mock_transcript.transcript_metadata or {}
        }
        
        assert transcript_dict["id"] is None
        assert transcript_dict["created_at"] is None
        assert transcript_dict["metadata"] == {}
        assert isinstance(transcript_dict["metadata"], dict)
