"""
Интеграционные тесты для TranscriptService.
"""

import os
import uuid
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from frontend_bot.services.transcript_service import TranscriptService
from database.models import UserTranscript

TEST_USER_ID = 123456789
TEST_AUDIO_DATA = b"test audio data"
TEST_TRANSCRIPT_DATA = b"test transcript data"
TEST_METADATA = {
    "duration": 60,
    "language": "ru",
    "model": "whisper-1",
    "word_count": 42
}

@pytest.fixture
async def transcript_service(test_session: AsyncSession):
    """Фикстура для создания TranscriptService."""
    service = TranscriptService(test_session)
    await service.init()
    return service

@pytest.mark.asyncio
async def test_transcript_service_save_and_get(transcript_service: TranscriptService):
    """Тест сохранения и получения транскрипта."""
    # Сохраняем транскрипт
    saved = await transcript_service.save_transcript(
        TEST_USER_ID,
        TEST_AUDIO_DATA,
        TEST_TRANSCRIPT_DATA,
        TEST_METADATA
    )
    
    assert saved["transcript_id"], "Должен быть присвоен transcript_id"
    assert saved["audio_url"].startswith("/transcripts/"), "Неверный формат audio_url"
    assert saved["transcript_url"].startswith("/transcripts/"), "Неверный формат transcript_url"
    assert saved["metadata"] == TEST_METADATA, "Метаданные должны совпадать"
    assert isinstance(saved["created_at"], datetime), "created_at должен быть datetime"
    
    # Получаем транскрипт
    transcript = await transcript_service.get_transcript(
        TEST_USER_ID,
        saved["transcript_id"]
    )
    
    assert transcript is not None, "Транскрипт должен быть найден"
    assert transcript["transcript_id"] == saved["transcript_id"], "ID должны совпадать"
    assert transcript["metadata"] == TEST_METADATA, "Метаданные должны совпадать"
    assert transcript["audio_url"].startswith("http"), "audio_url должен быть presigned URL"
    assert transcript["transcript_url"].startswith("http"), "transcript_url должен быть presigned URL"

@pytest.mark.asyncio
async def test_transcript_service_list(transcript_service: TranscriptService):
    """Тест получения списка транскриптов."""
    # Создаем несколько транскриптов
    transcripts = []
    for i in range(3):
        metadata = {**TEST_METADATA, "index": i}
        saved = await transcript_service.save_transcript(
            TEST_USER_ID,
            TEST_AUDIO_DATA,
            TEST_TRANSCRIPT_DATA,
            metadata
        )
        transcripts.append(saved)
    
    # Получаем список
    transcript_list = await transcript_service.list_transcripts(TEST_USER_ID, limit=10)
    
    assert len(transcript_list) == 3, "Должно быть 3 транскрипта"
    # Проверяем сортировку по дате (сначала новые)
    assert transcript_list[0]["created_at"] >= transcript_list[1]["created_at"], "Неверная сортировка"
    
    # Проверяем пагинацию
    paginated = await transcript_service.list_transcripts(TEST_USER_ID, limit=2, offset=1)
    assert len(paginated) == 2, "Должно быть 2 транскрипта"
    assert paginated[0]["transcript_id"] == transcript_list[1]["transcript_id"], "Неверное смещение"

@pytest.mark.asyncio
async def test_transcript_service_delete(transcript_service: TranscriptService):
    """Тест удаления транскрипта."""
    # Сохраняем транскрипт
    saved = await transcript_service.save_transcript(
        TEST_USER_ID,
        TEST_AUDIO_DATA,
        TEST_TRANSCRIPT_DATA,
        TEST_METADATA
    )
    
    # Удаляем транскрипт
    deleted = await transcript_service.delete_transcript(
        TEST_USER_ID,
        saved["transcript_id"]
    )
    assert deleted is True, "Удаление должно быть успешным"
    
    # Проверяем, что транскрипт удален
    transcript = await transcript_service.get_transcript(
        TEST_USER_ID,
        saved["transcript_id"]
    )
    assert transcript is None, "Транскрипт должен быть удален"
    
    # Проверяем повторное удаление
    deleted = await transcript_service.delete_transcript(
        TEST_USER_ID,
        saved["transcript_id"]
    )
    assert deleted is False, "Повторное удаление должно вернуть False"

@pytest.mark.asyncio
async def test_transcript_service_error_handling(transcript_service: TranscriptService):
    """Тест обработки ошибок."""
    # Попытка получить несуществующий транскрипт
    transcript = await transcript_service.get_transcript(
        TEST_USER_ID,
        str(uuid.uuid4())
    )
    assert transcript is None, "Несуществующий транскрипт должен вернуть None"
    
    # Попытка удалить несуществующий транскрипт
    deleted = await transcript_service.delete_transcript(
        TEST_USER_ID,
        str(uuid.uuid4())
    )
    assert deleted is False, "Удаление несуществующего транскрипта должно вернуть False"
    
    # Попытка получить транскрипты несуществующего пользователя
    transcripts = await transcript_service.list_transcripts(999999)
    assert len(transcripts) == 0, "Список транскриптов несуществующего пользователя должен быть пустым" 