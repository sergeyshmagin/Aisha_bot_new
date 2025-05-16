"""Тесты для функций транскрибации протоколов."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from telebot.types import Message
from frontend_bot.handlers.transcribe_protocol import send_mom
from frontend_bot.services.transcript_utils import get_user_transcript_or_error
from frontend_bot.services import transcript_cache
from frontend_bot.services.gpt_assistant import format_transcript_with_gpt

@pytest.fixture
def mock_message():
    """Фикстура для создания тестового сообщения."""
    message = MagicMock()
    message.from_user.id = 123456
    message.chat.id = 123456
    message.text = "Сформировать MoM"
    return message

@pytest.fixture
def mock_transcript_file(tmp_path):
    """Создает временный файл с транскриптом для тестов."""
    transcript_path = tmp_path / "test_transcript.txt"
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write("Test transcript content")
    return str(transcript_path)

@pytest.fixture
def mock_mom_text():
    """Фикстура для тестового MoM."""
    return "Test MoM content"

@pytest.mark.asyncio
async def test_send_mom_success(mock_message, mock_transcript_file):
    """Тест успешной отправки MoM."""
    await transcript_cache.set(mock_message.from_user.id, mock_transcript_file)
    
    with patch("frontend_bot.services.transcript_utils.async_exists", new_callable=AsyncMock) as mock_exists:
        mock_exists.return_value = True
        with patch("frontend_bot.services.transcript_utils.aiofiles.open", new_callable=AsyncMock) as mock_open:
            mock_open.return_value.__aenter__.return_value.read.return_value = "Test transcript content"
            
            with patch("frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt") as mock_format:
                mock_format.return_value = "Formatted MoM content"
                
                with patch("frontend_bot.handlers.transcribe_protocol.bot") as mock_bot:
                    mock_bot.send_document = AsyncMock()
                    
                    await send_mom(mock_message)
                    
                    mock_bot.send_document.assert_called_once()
                    args = mock_bot.send_document.call_args[0]
                    assert args[0] == 123456

@pytest.mark.asyncio
async def test_send_mom_no_transcript(mock_message):
    """Тест обработки отсутствия транскрипта."""
    with patch("frontend_bot.handlers.transcribe_protocol.bot") as mock_bot:
        mock_bot.send_message = AsyncMock()
        
        await send_mom(mock_message)
        
        mock_bot.send_message.assert_called_once()
        args = mock_bot.send_message.call_args[0]
        assert args[0] == 123456
        assert "транскрипт не найден" in args[1].lower()

@pytest.mark.asyncio
async def test_send_mom_format_error(mock_message, mock_transcript_file):
    """Тест обработки ошибки форматирования."""
    await transcript_cache.set(mock_message.from_user.id, mock_transcript_file)
    
    with patch("frontend_bot.services.transcript_utils.async_exists", new_callable=AsyncMock) as mock_exists:
        mock_exists.return_value = True
        with patch("frontend_bot.services.transcript_utils.aiofiles.open", new_callable=AsyncMock) as mock_open:
            mock_open.return_value.__aenter__.return_value.read.return_value = "Test transcript content"
            
            with patch("frontend_bot.handlers.transcribe_protocol.format_transcript_with_gpt") as mock_format:
                mock_format.return_value = None
                
                with patch("frontend_bot.handlers.transcribe_protocol.bot") as mock_bot:
                    mock_bot.send_message = AsyncMock()
                    
                    await send_mom(mock_message)
                    
                    mock_bot.send_message.assert_called_once()
                    args = mock_bot.send_message.call_args[0]
                    assert args[0] == 123456
                    assert "ошибка" in args[1].lower() 