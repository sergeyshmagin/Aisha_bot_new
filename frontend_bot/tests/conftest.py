"""
Общие фикстуры и конфигурация для тестов.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

def pytest_configure(config):
    """Добавляем маркеры для тестов."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires Redis server)"
    )

@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_bot():
    """Фикстура для мока бота."""
    with patch("frontend_bot.handlers.handlers.bot") as mock:
        mock.send_message = AsyncMock()
        mock.get_file = AsyncMock()
        mock.download_file = AsyncMock()
        yield mock

@pytest.fixture
def mock_avatar_workflow():
    """Фикстура для мока avatar_workflow."""
    with patch("frontend_bot.handlers.handlers.handle_photo_upload") as mock_upload, \
         patch("frontend_bot.handlers.handlers.handle_gender_selection") as mock_gender, \
         patch("frontend_bot.handlers.handlers.handle_name_input") as mock_name, \
         patch("frontend_bot.handlers.handlers.finalize_avatar") as mock_finalize, \
         patch("frontend_bot.handlers.handlers.load_avatar_fsm") as mock_load, \
         patch("frontend_bot.handlers.handlers.cleanup_state") as mock_cleanup:
        
        mock_upload.return_value = AsyncMock()
        mock_gender.return_value = AsyncMock()
        mock_name.return_value = AsyncMock()
        mock_finalize.return_value = AsyncMock()
        mock_load.return_value = {"photos": []}
        mock_cleanup.return_value = AsyncMock()
        
        yield {
            "upload": mock_upload,
            "gender": mock_gender,
            "name": mock_name,
            "finalize": mock_finalize,
            "load": mock_load,
            "cleanup": mock_cleanup,
        } 