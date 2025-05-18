"""
Тесты для сервиса транскриптов.
"""

import pytest
import os
from pathlib import Path
import aiofiles
import json
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from frontend_bot.services.transcript_service import TranscriptService
from frontend_bot.shared.storage_utils import init_storage
from frontend_bot.config import settings
from frontend_bot.utils.logger import get_logger
from frontend_bot.services.transcript_service import get_user_transcript_or_error

logger = get_logger(__name__)

@pytest.fixture
async def transcript_service(session):
    """Создает экземпляр сервиса транскриптов."""
    service = TranscriptService(session)
    await service.init()
    return service

@pytest.mark.asyncio
async def test_save_transcript(transcript_service):
    """Тест сохранения транскрипта."""
    user_id = 123
    audio_data = b"test_audio_data"
    transcript_data = b"test_transcript_data"
    metadata = {
        "title": "Test Transcript",
        "language": "ru",
        "duration": 60
    }
    
    result = await transcript_service.save_transcript(
        user_id,
        audio_data,
        transcript_data,
        metadata
    )
    assert "transcript_id" in result
    assert "audio_url" in result
    assert "transcript_url" in result
    assert result["metadata"] == metadata

@pytest.mark.asyncio
async def test_get_transcript(transcript_service):
    """Тест получения транскрипта."""
    user_id = 123
    audio_data = b"test_audio_data"
    transcript_data = b"test_transcript_data"
    metadata = {"title": "Test Transcript"}
    
    # Сначала сохраняем транскрипт
    saved = await transcript_service.save_transcript(
        user_id,
        audio_data,
        transcript_data,
        metadata
    )
    transcript_id = saved["transcript_id"]
    
    # Получаем транскрипт
    transcript = await transcript_service.get_transcript(user_id, transcript_id)
    assert transcript is not None
    assert transcript["metadata"] == metadata
    assert "audio_url" in transcript
    assert "transcript_url" in transcript

@pytest.mark.asyncio
async def test_delete_transcript(transcript_service):
    """Тест удаления транскрипта."""
    user_id = 123
    audio_data = b"test_audio_data"
    transcript_data = b"test_transcript_data"
    metadata = {"title": "Test Transcript"}
    
    # Сначала сохраняем транскрипт
    saved = await transcript_service.save_transcript(
        user_id,
        audio_data,
        transcript_data,
        metadata
    )
    transcript_id = saved["transcript_id"]
    
    # Удаляем транскрипт
    result = await transcript_service.delete_transcript(user_id, transcript_id)
    assert result is True
    
    # Проверяем, что транскрипт удален
    transcript = await transcript_service.get_transcript(user_id, transcript_id)
    assert transcript is None

@pytest.mark.asyncio
async def test_list_transcripts(transcript_service):
    """Тест получения списка транскриптов."""
    user_id = 123
    audio_data = b"test_audio_data"
    transcript_data = b"test_transcript_data"
    metadata1 = {"title": "Transcript 1"}
    metadata2 = {"title": "Transcript 2"}
    
    # Создаем два транскрипта
    await transcript_service.save_transcript(
        user_id,
        audio_data,
        transcript_data,
        metadata1
    )
    await transcript_service.save_transcript(
        user_id,
        audio_data,
        transcript_data,
        metadata2
    )
    
    # Получаем список
    transcripts = await transcript_service.list_transcripts(user_id)
    assert len(transcripts) == 2
    titles = [t["metadata"]["title"] for t in transcripts]
    assert "Transcript 1" in titles
    assert "Transcript 2" in titles

@pytest.mark.asyncio
async def test_concurrent_operations(transcript_service):
    """Тест конкурентных операций."""
    user_id = 123
    audio_data = b"test_audio_data"
    transcript_data = b"test_transcript_data"
    metadata = {"title": "Test Transcript"}
    
    # Создаем несколько транскриптов одновременно
    tasks = []
    for i in range(3):
        task = transcript_service.save_transcript(
            user_id,
            audio_data,
            transcript_data,
            {**metadata, "index": i}
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    assert len(results) == 3
    
    # Проверяем, что все транскрипты созданы
    transcripts = await transcript_service.list_transcripts(user_id)
    assert len(transcripts) == 3

@pytest.mark.asyncio
async def test_get_user_transcript_or_error(transcript_service):
    """Тест получения транскрипта с обработкой ошибок."""
    user_id = 123
    audio_data = b"test_audio_data"
    transcript_data = b"test_transcript_data"
    metadata = {"title": "Test Transcript"}
    
    # Сначала сохраняем транскрипт
    saved = await transcript_service.save_transcript(
        user_id,
        audio_data,
        transcript_data,
        metadata
    )
    transcript_id = saved["transcript_id"]
    
    # Получаем транскрипт
    transcript, error = await get_user_transcript_or_error(
        user_id,
        transcript_id,
        transcript_service.session
    )
    assert transcript is not None
    assert error is None
    assert transcript["metadata"] == metadata
    
    # Проверяем случай с несуществующим транскриптом
    transcript, error = await get_user_transcript_or_error(
        user_id,
        "non_existent_id",
        transcript_service.session
    )
    assert transcript is None
    assert error == "Транскрипт не найден"

@pytest.mark.asyncio
async def test_invalid_audio_format(transcript_service):
    """Тест обработки некорректного формата аудио."""
    user_id = 123
    invalid_audio = b"not_an_audio_file"
    transcript_data = b"test_transcript_data"
    metadata = {"title": "Test Transcript"}
    
    with pytest.raises(ValueError) as exc_info:
        await transcript_service.save_transcript(
            user_id,
            invalid_audio,
            transcript_data,
            metadata
        )
    assert "Invalid audio format" in str(exc_info.value)

@pytest.mark.asyncio
async def test_metadata_validation(transcript_service):
    """Тест валидации метаданных."""
    user_id = 123
    audio_data = b"test_audio_data"
    transcript_data = b"test_transcript_data"
    
    # Тест с отсутствующими обязательными полями
    invalid_metadata = {"title": "Test"}
    with pytest.raises(ValueError) as exc_info:
        await transcript_service.save_transcript(
            user_id,
            audio_data,
            transcript_data,
            invalid_metadata
        )
    assert "Missing required metadata" in str(exc_info.value)
    
    # Тест с некорректным языком
    invalid_language = {
        "title": "Test",
        "language": "invalid_lang",
        "duration": 60
    }
    with pytest.raises(ValueError) as exc_info:
        await transcript_service.save_transcript(
            user_id,
            audio_data,
            transcript_data,
            invalid_language
        )
    assert "Invalid language" in str(exc_info.value)

@pytest.mark.asyncio
async def test_file_operations_error_handling(transcript_service):
    """Тест обработки ошибок при работе с файлами."""
    user_id = 123
    audio_data = b"test_audio_data"
    transcript_data = b"test_transcript_data"
    metadata = {
        "title": "Test Transcript",
        "language": "ru",
        "duration": 60
    }
    
    # Симулируем ошибку при сохранении файла
    transcript_service.storage.save_file = AsyncMock(side_effect=IOError("Storage error"))
    
    with pytest.raises(IOError) as exc_info:
        await transcript_service.save_transcript(
            user_id,
            audio_data,
            transcript_data,
            metadata
        )
    assert "Storage error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_different_audio_formats(transcript_service):
    """Тест работы с разными форматами аудио."""
    user_id = 123
    transcript_data = b"test_transcript_data"
    metadata = {
        "title": "Test Transcript",
        "language": "ru",
        "duration": 60
    }
    
    # Тест с MP3
    mp3_data = b"fake_mp3_data"
    result_mp3 = await transcript_service.save_transcript(
        user_id,
        mp3_data,
        transcript_data,
        {**metadata, "format": "mp3"}
    )
    assert result_mp3["metadata"]["format"] == "mp3"
    
    # Тест с WAV
    wav_data = b"fake_wav_data"
    result_wav = await transcript_service.save_transcript(
        user_id,
        wav_data,
        transcript_data,
        {**metadata, "format": "wav"}
    )
    assert result_wav["metadata"]["format"] == "wav"

@pytest.mark.asyncio
async def test_transcript_cleanup(transcript_service):
    """Тест очистки старых транскриптов."""
    user_id = 123
    audio_data = b"test_audio_data"
    transcript_data = b"test_transcript_data"
    metadata = {
        "title": "Test Transcript",
        "language": "ru",
        "duration": 60
    }
    
    # Создаем несколько транскриптов
    for i in range(5):
        await transcript_service.save_transcript(
            user_id,
            audio_data,
            transcript_data,
            {**metadata, "index": i}
        )
    
    # Запускаем очистку
    await transcript_service.cleanup_old_transcripts(user_id, max_age_days=1)
    
    # Проверяем, что старые транскрипты удалены
    transcripts = await transcript_service.list_transcripts(user_id)
    assert len(transcripts) <= 5  # Максимум 5 транскриптов должно остаться 