"""
Тесты для сервиса транскриптов.
"""

import pytest
from datetime import datetime
from uuid import UUID

from frontend_bot.services.transcript_service import TranscriptService
from database.models import UserTranscript

@pytest.fixture
def transcript_service(session):
    """Создает экземпляр сервиса транскриптов."""
    return TranscriptService(session)

@pytest.fixture
def test_transcript_data():
    """Создает тестовые данные транскрипта."""
    return {
        "transcript_name": "test_transcript",
        "transcript_type": "text/plain",
        "transcript_size": 1024,
        "transcript_path": "/path/to/test_transcript.txt",
        "transcript_data": {
            "key1": "value1",
            "key2": "value2"
        }
    }

@pytest.mark.asyncio
async def test_create_transcript(transcript_service, test_user_data, test_transcript_data):
    """Тест создания транскрипта."""
    # Создаем пользователя
    user = await transcript_service.create_user(**test_user_data)
    assert user.id == test_user_data["id"]
    
    # Создаем транскрипт
    transcript = await transcript_service.create_transcript(
        user_id=user.id,
        **test_transcript_data
    )
    
    assert isinstance(transcript.id, UUID)
    assert transcript.user_id == user.id
    assert transcript.transcript_name == test_transcript_data["transcript_name"]
    assert transcript.transcript_type == test_transcript_data["transcript_type"]
    assert transcript.transcript_size == test_transcript_data["transcript_size"]
    assert transcript.transcript_path == test_transcript_data["transcript_path"]
    assert transcript.transcript_data == test_transcript_data["transcript_data"]
    assert isinstance(transcript.created_at, datetime)
    assert isinstance(transcript.updated_at, datetime)

@pytest.mark.asyncio
async def test_get_transcript(transcript_service, test_user_data, test_transcript_data):
    """Тест получения транскрипта."""
    # Создаем пользователя
    user = await transcript_service.create_user(**test_user_data)
    
    # Создаем транскрипт
    transcript = await transcript_service.create_transcript(
        user_id=user.id,
        **test_transcript_data
    )
    
    # Получаем транскрипт
    retrieved_transcript = await transcript_service.get_transcript(transcript.id)
    assert retrieved_transcript.id == transcript.id
    assert retrieved_transcript.user_id == user.id
    assert retrieved_transcript.transcript_name == test_transcript_data["transcript_name"]
    assert retrieved_transcript.transcript_type == test_transcript_data["transcript_type"]
    assert retrieved_transcript.transcript_size == test_transcript_data["transcript_size"]
    assert retrieved_transcript.transcript_path == test_transcript_data["transcript_path"]
    assert retrieved_transcript.transcript_data == test_transcript_data["transcript_data"]

@pytest.mark.asyncio
async def test_update_transcript(transcript_service, test_user_data, test_transcript_data):
    """Тест обновления транскрипта."""
    # Создаем пользователя
    user = await transcript_service.create_user(**test_user_data)
    
    # Создаем транскрипт
    transcript = await transcript_service.create_transcript(
        user_id=user.id,
        **test_transcript_data
    )
    
    # Обновляем транскрипт
    updated_data = {
        "transcript_name": "updated_transcript",
        "transcript_type": "text/markdown",
        "transcript_size": 2048,
        "transcript_path": "/path/to/updated_transcript.md",
        "transcript_data": {
            "key3": "value3",
            "key4": "value4"
        }
    }
    
    updated_transcript = await transcript_service.update_transcript(
        transcript.id,
        **updated_data
    )
    
    assert updated_transcript.id == transcript.id
    assert updated_transcript.user_id == user.id
    assert updated_transcript.transcript_name == updated_data["transcript_name"]
    assert updated_transcript.transcript_type == updated_data["transcript_type"]
    assert updated_transcript.transcript_size == updated_data["transcript_size"]
    assert updated_transcript.transcript_path == updated_data["transcript_path"]
    assert updated_transcript.transcript_data == updated_data["transcript_data"]
    assert updated_transcript.updated_at > transcript.updated_at

@pytest.mark.asyncio
async def test_delete_transcript(transcript_service, test_user_data, test_transcript_data):
    """Тест удаления транскрипта."""
    # Создаем пользователя
    user = await transcript_service.create_user(**test_user_data)
    
    # Создаем транскрипт
    transcript = await transcript_service.create_transcript(
        user_id=user.id,
        **test_transcript_data
    )
    
    # Удаляем транскрипт
    await transcript_service.delete_transcript(transcript.id)
    
    # Проверяем, что транскрипт удален
    retrieved_transcript = await transcript_service.get_transcript(transcript.id)
    assert retrieved_transcript is None

@pytest.mark.asyncio
async def test_get_user_transcripts(transcript_service, test_user_data, test_transcript_data):
    """Тест получения транскриптов пользователя."""
    # Создаем пользователя
    user = await transcript_service.create_user(**test_user_data)
    
    # Создаем транскрипты
    transcript1 = await transcript_service.create_transcript(
        user_id=user.id,
        **test_transcript_data
    )
    transcript2 = await transcript_service.create_transcript(
        user_id=user.id,
        **{**test_transcript_data, "transcript_name": "test_transcript2"}
    )
    
    # Получаем транскрипты пользователя
    user_transcripts = await transcript_service.get_user_transcripts(user.id)
    assert len(user_transcripts) == 2
    assert all(isinstance(t.id, UUID) for t in user_transcripts)
    assert all(t.user_id == user.id for t in user_transcripts)
    assert {t.transcript_name for t in user_transcripts} == {"test_transcript", "test_transcript2"}

@pytest.mark.asyncio
async def test_get_transcripts_by_type(transcript_service, test_user_data, test_transcript_data):
    """Тест получения транскриптов по типу."""
    # Создаем пользователя
    user = await transcript_service.create_user(**test_user_data)
    
    # Создаем транскрипты разных типов
    await transcript_service.create_transcript(
        user_id=user.id,
        **test_transcript_data
    )
    await transcript_service.create_transcript(
        user_id=user.id,
        **{**test_transcript_data, "transcript_name": "test_transcript2", "transcript_type": "text/markdown"}
    )
    
    # Получаем транскрипты по типу
    plain_transcripts = await transcript_service.get_transcripts_by_type("text/plain")
    assert len(plain_transcripts) == 1
    assert plain_transcripts[0].transcript_type == "text/plain"
    
    markdown_transcripts = await transcript_service.get_transcripts_by_type("text/markdown")
    assert len(markdown_transcripts) == 1
    assert markdown_transcripts[0].transcript_type == "text/markdown"

@pytest.mark.asyncio
async def test_get_transcripts_by_data(transcript_service, test_user_data, test_transcript_data):
    """Тест получения транскриптов по данным."""
    # Создаем пользователя
    user = await transcript_service.create_user(**test_user_data)
    
    # Создаем транскрипты с разными данными
    await transcript_service.create_transcript(
        user_id=user.id,
        **test_transcript_data
    )
    await transcript_service.create_transcript(
        user_id=user.id,
        **{**test_transcript_data, "transcript_name": "test_transcript2", "transcript_data": {"key3": "value3"}}
    )
    
    # Получаем транскрипты по данным
    transcripts_with_key1 = await transcript_service.get_transcripts_by_data("key1", "value1")
    assert len(transcripts_with_key1) == 1
    assert transcripts_with_key1[0].transcript_data["key1"] == "value1"
    
    transcripts_with_key3 = await transcript_service.get_transcripts_by_data("key3", "value3")
    assert len(transcripts_with_key3) == 1
    assert transcripts_with_key3[0].transcript_data["key3"] == "value3" 