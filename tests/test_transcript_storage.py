import pytest
import uuid
from pathlib import Path
from datetime import datetime
from typing import AsyncGenerator

from minio import Minio
from minio.error import S3Error

from database.models import UserTranscript
from database.config import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from frontend_bot.services.transcript_service import TranscriptService

# Фикстуры
@pytest.fixture
async def minio_client() -> AsyncGenerator[Minio, None]:
    """Фикстура для создания тестового клиента MinIO"""
    client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    
    # Создаем тестовый bucket если его нет
    bucket_name = "test-transcripts"
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
    except S3Error as e:
        pytest.fail(f"Failed to create test bucket: {e}")
    
    yield client
    
    # Очистка после тестов
    try:
        objects = client.list_objects(bucket_name, recursive=True)
        for obj in objects:
            client.remove_object(bucket_name, obj.object_name)
        client.remove_bucket(bucket_name)
    except S3Error as e:
        pytest.fail(f"Failed to cleanup test bucket: {e}")

@pytest.fixture
async def transcript_service(minio_client: Minio) -> TranscriptService:
    """Фикстура для создания сервиса транскриптов"""
    return TranscriptService(minio_client, bucket_name="test-transcripts")

# Тесты
@pytest.mark.asyncio
async def test_save_transcript(transcript_service: TranscriptService):
    """Тест сохранения транскрипта"""
    # Arrange
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    test_content = b"Test transcript content"
    metadata = {"status": "completed", "language": "ru"}
    
    # Act
    transcript = await transcript_service.save_transcript(
        user_id=user_id,
        session_id=session_id,
        content=test_content,
        metadata=metadata
    )
    
    # Assert
    assert transcript.user_id == user_id
    assert transcript.session_id == session_id
    assert transcript.metadata == metadata
    assert transcript.file_path == f"{user_id}/{session_id}/transcript.txt"

@pytest.mark.asyncio
async def test_get_transcript(transcript_service: TranscriptService):
    """Тест получения транскрипта"""
    # Arrange
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    test_content = b"Test transcript content"
    metadata = {"status": "completed", "language": "ru"}
    
    # Сохраняем тестовые данные
    await transcript_service.save_transcript(
        user_id=user_id,
        session_id=session_id,
        content=test_content,
        metadata=metadata
    )
    
    # Act
    content, transcript = await transcript_service.get_transcript(
        user_id=user_id,
        session_id=session_id
    )
    
    # Assert
    assert content == test_content
    assert transcript.user_id == user_id
    assert transcript.session_id == session_id
    assert transcript.metadata == metadata

@pytest.mark.asyncio
async def test_delete_transcript(transcript_service: TranscriptService):
    """Тест удаления транскрипта"""
    # Arrange
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    test_content = b"Test transcript content"
    
    # Сохраняем тестовые данные
    await transcript_service.save_transcript(
        user_id=user_id,
        session_id=session_id,
        content=test_content
    )
    
    # Act
    await transcript_service.delete_transcript(
        user_id=user_id,
        session_id=session_id
    )
    
    # Assert
    with pytest.raises(ValueError):
        await transcript_service.get_transcript(
            user_id=user_id,
            session_id=session_id
        )

@pytest.mark.asyncio
async def test_list_user_transcripts(transcript_service: TranscriptService):
    """Тест получения списка транскриптов пользователя"""
    # Arrange
    user_id = uuid.uuid4()
    test_content = b"Test transcript content"
    
    # Создаем несколько транскриптов
    for i in range(3):
        await transcript_service.save_transcript(
            user_id=user_id,
            session_id=uuid.uuid4(),
            content=test_content,
            metadata={"index": i}
        )
    
    # Act
    transcripts = await transcript_service.list_user_transcripts(
        user_id=user_id,
        limit=10
    )
    
    # Assert
    assert len(transcripts) == 3
    assert all(t.user_id == user_id for t in transcripts)
    assert all("index" in t.metadata for t in transcripts)
    
    # Проверяем сортировку по created_at
    created_at_list = [t.created_at for t in transcripts]
    assert created_at_list == sorted(created_at_list, reverse=True)

@pytest.mark.asyncio
async def test_get_nonexistent_transcript(transcript_service: TranscriptService):
    """Тест получения несуществующего транскрипта"""
    # Act & Assert
    with pytest.raises(ValueError):
        await transcript_service.get_transcript(
            user_id=uuid.uuid4(),
            session_id=uuid.uuid4()
        )

@pytest.mark.asyncio
async def test_delete_nonexistent_transcript(transcript_service: TranscriptService):
    """Тест удаления несуществующего транскрипта"""
    # Act & Assert
    with pytest.raises(ValueError):
        await transcript_service.delete_transcript(
            user_id=uuid.uuid4(),
            session_id=uuid.uuid4()
        ) 