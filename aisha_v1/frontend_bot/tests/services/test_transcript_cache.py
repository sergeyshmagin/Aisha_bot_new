"""
Тесты для кэширования транскриптов.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from frontend_bot.services.transcript_cache import (
    get_transcript,
    set_transcript,
    remove_transcript,
    clear_transcripts,
    get_all_transcripts
)
from frontend_bot.shared.redis_client import redis_client
from frontend_bot.config import settings
from frontend_bot.utils.logger import get_logger

logger = get_logger(__name__)

@pytest.fixture
async def transcript_cache():
    """Подготовка кэша для тестов."""
    await clear_transcripts()  # Очищаем кэш перед тестами
    yield
    await clear_transcripts()  # Очищаем кэш после тестов

@pytest.mark.asyncio
async def test_set_and_get_transcript(transcript_cache):
    """Тест сохранения и получения транскрипта."""
    user_id = 123
    transcript_data = {
        "text": "Test transcript",
        "created_at": datetime.now().isoformat()
    }
    
    # Сохраняем транскрипт
    result = await set_transcript(user_id, transcript_data)
    assert result is True
    
    # Получаем транскрипт
    cached_data = await get_transcript(user_id)
    assert cached_data is not None
    assert cached_data["text"] == transcript_data["text"]
    assert cached_data["created_at"] == transcript_data["created_at"]

@pytest.mark.asyncio
async def test_remove_transcript(transcript_cache):
    """Тест удаления транскрипта."""
    user_id = 123
    transcript_data = {
        "text": "Test transcript",
        "created_at": datetime.now().isoformat()
    }
    
    # Сохраняем транскрипт
    await set_transcript(user_id, transcript_data)
    
    # Удаляем транскрипт
    result = await remove_transcript(user_id)
    assert result is True
    
    # Проверяем, что транскрипт удален
    cached_data = await get_transcript(user_id)
    assert cached_data is None

@pytest.mark.asyncio
async def test_clear_transcripts(transcript_cache):
    """Тест очистки всех транскриптов."""
    # Сохраняем несколько транскриптов
    for i in range(3):
        user_id = i + 1
        transcript_data = {
            "text": f"Test transcript {i}",
            "created_at": datetime.now().isoformat()
        }
        await set_transcript(user_id, transcript_data)
    
    # Очищаем все транскрипты
    result = await clear_transcripts()
    assert result is True
    
    # Проверяем, что все транскрипты удалены
    for i in range(3):
        user_id = i + 1
        cached_data = await get_transcript(user_id)
        assert cached_data is None

@pytest.mark.asyncio
async def test_get_all_transcripts(transcript_cache):
    """Тест получения всех транскриптов."""
    # Сохраняем несколько транскриптов
    expected_transcripts = {}
    for i in range(3):
        user_id = i + 1
        transcript_data = {
            "text": f"Test transcript {i}",
            "created_at": datetime.now().isoformat()
        }
        await set_transcript(user_id, transcript_data)
        expected_transcripts[str(user_id)] = transcript_data
    
    # Получаем все транскрипты
    all_transcripts = await get_all_transcripts()
    assert len(all_transcripts) == 3
    
    # Проверяем содержимое
    for user_id, transcript_data in all_transcripts.items():
        assert user_id in expected_transcripts
        assert transcript_data["text"] == expected_transcripts[user_id]["text"]
        assert transcript_data["created_at"] == expected_transcripts[user_id]["created_at"]

@pytest.mark.asyncio
async def test_transcript_expiration(transcript_cache):
    """Тест истечения срока действия транскрипта."""
    user_id = 123
    transcript_data = {
        "text": "Test transcript",
        "created_at": datetime.now().isoformat()
    }
    
    # Сохраняем транскрипт с коротким TTL
    await set_transcript(user_id, transcript_data, ttl=1)
    
    # Ждем истечения TTL
    import asyncio
    await asyncio.sleep(2)
    
    # Проверяем, что транскрипт удален
    cached_data = await get_transcript(user_id)
    assert cached_data is None

@pytest.mark.asyncio
async def test_concurrent_operations(transcript_cache):
    """Тест конкурентных операций с транскриптами."""
    import asyncio
    
    # Создаем несколько транскриптов
    tasks = []
    for i in range(3):
        user_id = i + 1
        transcript_data = {
            "text": f"Test transcript {i}",
            "created_at": datetime.now().isoformat()
        }
        tasks.append(set_transcript(user_id, transcript_data))
    
    # Сохраняем транскрипты одновременно
    results = await asyncio.gather(*tasks)
    assert all(results)
    
    # Проверяем, что все транскрипты сохранены
    all_transcripts = await get_all_transcripts()
    assert len(all_transcripts) == 3 