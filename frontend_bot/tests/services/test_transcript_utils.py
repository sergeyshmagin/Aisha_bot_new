"""
Тесты для утилит транскриптов.
"""

import pytest
import json
import io
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from frontend_bot.services.transcript_utils import (
    get_user_transcript_or_error,
    send_document_with_caption,
    send_transcript_error
)
from frontend_bot.services.transcript_cache import set_transcript
from frontend_bot.shared.redis_client import redis_client
from frontend_bot.config import settings
from frontend_bot.utils.logger import get_logger

logger = get_logger(__name__)

@pytest.fixture
async def mock_bot():
    """Создает мок бота для тестов."""
    bot = AsyncMock()
    bot.send_document = AsyncMock()
    bot.send_message = AsyncMock()
    return bot

@pytest.fixture
async def transcript_cache():
    """Подготовка кэша для тестов."""
    from frontend_bot.services.transcript_cache import clear_transcripts
    await clear_transcripts()
    yield
    await clear_transcripts()

@pytest.mark.asyncio
async def test_get_user_transcript_or_error_success(mock_bot, transcript_cache):
    """Тест успешного получения транскрипта."""
    user_id = 123
    transcript_data = {
        "text": "Test transcript",
        "created_at": datetime.now().isoformat()
    }
    
    # Сохраняем транскрипт
    await set_transcript(user_id, transcript_data)
    
    # Получаем транскрипт
    result = await get_user_transcript_or_error(mock_bot, user_id)
    assert result is not None
    assert result["text"] == transcript_data["text"]
    assert result["created_at"] == transcript_data["created_at"]
    
    # Проверяем, что бот не отправлял сообщения об ошибке
    mock_bot.send_message.assert_not_called()

@pytest.mark.asyncio
async def test_get_user_transcript_or_error_not_found(mock_bot, transcript_cache):
    """Тест получения транскрипта, когда он не найден."""
    user_id = 123
    
    # Пытаемся получить несуществующий транскрипт
    result = await get_user_transcript_or_error(mock_bot, user_id)
    assert result is None
    
    # Проверяем, что бот отправил сообщение об ошибке
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args[1]
    assert "error" in call_args["text"].lower()

@pytest.mark.asyncio
async def test_send_document_with_caption_bytes(mock_bot):
    """Тест отправки документа с байтовыми данными."""
    user_id = 123
    caption = "Test caption"
    file_data = b"Test file content"
    
    # Отправляем документ
    await send_document_with_caption(mock_bot, user_id, file_data, caption)
    
    # Проверяем, что бот отправил документ
    mock_bot.send_document.assert_called_once()
    call_args = mock_bot.send_document.call_args[1]
    assert call_args["chat_id"] == user_id
    assert call_args["caption"] == caption
    assert isinstance(call_args["document"], io.BytesIO)

@pytest.mark.asyncio
async def test_send_document_with_caption_bytesio(mock_bot):
    """Тест отправки документа с BytesIO."""
    user_id = 123
    caption = "Test caption"
    file_data = io.BytesIO(b"Test file content")
    
    # Отправляем документ
    await send_document_with_caption(mock_bot, user_id, file_data, caption)
    
    # Проверяем, что бот отправил документ
    mock_bot.send_document.assert_called_once()
    call_args = mock_bot.send_document.call_args[1]
    assert call_args["chat_id"] == user_id
    assert call_args["caption"] == caption
    assert call_args["document"] == file_data

@pytest.mark.asyncio
async def test_send_document_with_keyboard(mock_bot):
    """Тест отправки документа с клавиатурой."""
    user_id = 123
    caption = "Test caption"
    file_data = b"Test file content"
    keyboard = MagicMock()
    
    # Отправляем документ с клавиатурой
    await send_document_with_caption(mock_bot, user_id, file_data, caption, keyboard)
    
    # Проверяем, что бот отправил документ с клавиатурой
    mock_bot.send_document.assert_called_once()
    call_args = mock_bot.send_document.call_args[1]
    assert call_args["chat_id"] == user_id
    assert call_args["caption"] == caption
    assert call_args["reply_markup"] == keyboard

@pytest.mark.asyncio
async def test_send_transcript_error(mock_bot):
    """Тест отправки сообщения об ошибке."""
    user_id = 123
    error_message = "Test error message"
    keyboard = MagicMock()
    
    # Отправляем сообщение об ошибке
    await send_transcript_error(mock_bot, user_id, error_message, keyboard)
    
    # Проверяем, что бот отправил сообщение об ошибке
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args[1]
    assert call_args["chat_id"] == user_id
    assert error_message in call_args["text"]
    assert call_args["reply_markup"] == keyboard

@pytest.mark.asyncio
async def test_send_transcript_error_without_keyboard(mock_bot):
    """Тест отправки сообщения об ошибке без клавиатуры."""
    user_id = 123
    error_message = "Test error message"
    
    # Отправляем сообщение об ошибке без клавиатуры
    await send_transcript_error(mock_bot, user_id, error_message)
    
    # Проверяем, что бот отправил сообщение об ошибке
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args[1]
    assert call_args["chat_id"] == user_id
    assert error_message in call_args["text"]
    assert "reply_markup" not in call_args 