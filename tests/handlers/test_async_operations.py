import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiofiles
import os
from frontend_bot.handlers.transcribe_protocol import send_mom
from frontend_bot.services.transcript_utils import get_user_transcript_or_error
from frontend_bot.shared.redis_client import redis_client

@pytest.fixture
async def mock_transcript_file(tmp_path):
    """Создает временный файл с транскриптом для тестов."""
    transcript_path = tmp_path / "test_transcript.txt"
    async with aiofiles.open(transcript_path, "w", encoding="utf-8") as f:
        await f.write("Test transcript content")
    return str(transcript_path)

@pytest.fixture
def mock_redis():
    """Мок для Redis клиента."""
    with patch("frontend_bot.shared.redis_client.redis_client") as mock:
        mock.get.return_value = AsyncMock(return_value="test_transcript.txt")
        yield mock

@pytest.mark.asyncio
async def test_async_file_operations(mock_transcript_file):
    """Тест асинхронных операций с файлами."""
    async with aiofiles.open(mock_transcript_file, "r", encoding="utf-8") as f:
        content = await f.read()
    assert content == "Test transcript content"

@pytest.mark.asyncio
async def test_get_user_transcript_async(mock_redis, mock_transcript_file):
    """Тест асинхронного получения транскрипта."""
    message = MagicMock()
    message.chat.id = 123456
    bot = AsyncMock()
    logger = MagicMock()
    
    with patch("frontend_bot.services.transcript_utils.async_exists", new_callable=AsyncMock) as mock_exists:
        mock_exists.return_value = True
        with patch("frontend_bot.services.transcript_utils.aiofiles.open", new_callable=AsyncMock) as mock_open:
            mock_open.return_value.__aenter__.return_value.read.return_value = "Test transcript content"
            
            transcript = await get_user_transcript_or_error(bot, message, logger)
            assert transcript == "Test transcript content"

@pytest.mark.asyncio
async def test_send_mom_async_flow(mock_redis, mock_transcript_file):
    """Тест асинхронного процесса отправки MoM."""
    message = MagicMock()
    message.chat.id = 123456
    message.from_user.id = 123456
    logger = MagicMock()
    
    with patch("frontend_bot.services.transcript_utils.async_exists", new_callable=AsyncMock) as mock_exists:
        mock_exists.return_value = True
        with patch("frontend_bot.services.transcript_utils.aiofiles.open", new_callable=AsyncMock) as mock_open:
            mock_open.return_value.__aenter__.return_value.read.return_value = "Test transcript content"
            
            with patch("frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt") as mock_format:
                mock_format.return_value = "Formatted MoM content"
                
                mock_bot = AsyncMock()
                mock_bot.send_document = AsyncMock()
                mock_bot.send_message = AsyncMock()
                mock_bot.send_chat_action = AsyncMock()
                with patch("frontend_bot.handlers.transcribe_protocol.bot", mock_bot):
                    await send_mom(message)
                    
                    mock_bot.send_document.assert_called_once()
                    args = mock_bot.send_document.call_args[0]
                    assert args[0] == 123456
                    assert os.path.exists(args[1]) 