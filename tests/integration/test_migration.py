"""
Интеграционные тесты для скрипта миграции.
"""

import os
import pytest
import uuid
import aiofiles
from datetime import datetime
from pathlib import Path

from shared_storage import storage_utils
from scripts.migrate_to_minio import DataMigrator
from database.models import User, UserAvatar, UserTranscript, UserHistory
from frontend_bot.config import settings

@pytest.fixture(scope="function")
async def async_session():
    """Фикстура для создания сессии БД"""
    async for session in get_async_db():
        yield session

@pytest.fixture(scope="function")
async def test_bucket():
    """Фикстура для создания тестового bucket'а"""
    bucket_name = f"test-{uuid.uuid4().hex[:8]}"
    await storage_utils.init_storage()
    yield bucket_name

@pytest.fixture
async def test_user(async_session):
    """Фикстура для создания тестового пользователя"""
    user = User(
        telegram_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    async_session.add(user)
    await async_session.commit()
    return user

@pytest.fixture
async def test_data_dir(tmp_path):
    """Фикстура для создания тестовых файлов"""
    # Создаем структуру директорий
    avatar_dir = tmp_path / "storage/avatars"
    transcript_dir = tmp_path / "storage/transcripts"
    history_dir = tmp_path / "storage/documents"
    
    for directory in [avatar_dir, transcript_dir, history_dir]:
        directory.mkdir(parents=True)
    
    # Создаем тестовые файлы
    test_files = {
        "avatar": {
            "photo": avatar_dir / "test_photo.png",
            "preview": avatar_dir / "test_preview.png"
        },
        "transcript": {
            "audio": transcript_dir / "test_audio.mp3",
            "transcript": transcript_dir / "test_transcript.txt"
        },
        "history": {
            "content": history_dir / "test_content.txt"
        }
    }
    
    # Записываем тестовые данные
    test_data = {
        "avatar": {
            "photo": b"test photo data",
            "preview": b"test preview data"
        },
        "transcript": {
            "audio": b"test audio data",
            "transcript": b"test transcript text"
        },
        "history": {
            "content": b"test history content"
        }
    }
    
    for data_type, files in test_files.items():
        for file_type, file_path in files.items():
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(test_data[data_type][file_type])
    
    yield {
        "paths": test_files,
        "data": test_data,
        "root": tmp_path
    }
    
    # Очистка после тестов
    for directory in [avatar_dir, transcript_dir, history_dir]:
        for file in directory.glob("*"):
            file.unlink()
        directory.rmdir()

@pytest.mark.asyncio
async def test_migration_success(test_bucket, test_user, test_data_dir, async_session):
    """Тест успешной миграции"""
    # Создаем записи в БД
    avatar = UserAvatar(
        user_id=test_user.id,
        photo_key=str(test_data_dir["paths"]["avatar"]["photo"].relative_to(test_data_dir["root"])),
        preview_key=str(test_data_dir["paths"]["avatar"]["preview"].relative_to(test_data_dir["root"]))
    )
    
    transcript = UserTranscript(
        user_id=test_user.id,
        audio_key=str(test_data_dir["paths"]["transcript"]["audio"].relative_to(test_data_dir["root"])),
        transcript_key=str(test_data_dir["paths"]["transcript"]["transcript"].relative_to(test_data_dir["root"]))
    )
    
    history = UserHistory(
        user_id=test_user.id,
        content_key=str(test_data_dir["paths"]["history"]["content"].relative_to(test_data_dir["root"]))
    )
    
    async_session.add_all([avatar, transcript, history])
    await async_session.commit()
    
    # Запускаем миграцию
    migrator = DataMigrator(async_session)
    await migrator.init_storage()
    
    # Миграция данных
    await migrator.migrate_avatars()
    await migrator.migrate_transcripts()
    await migrator.migrate_history()
    
    # Валидация
    success = await migrator.validate_migration()
    assert success, "Migration validation failed"
    
    # Проверяем статистику
    assert migrator.stats["avatars"]["success"] == 1
    assert migrator.stats["transcripts"]["success"] == 1
    assert migrator.stats["history"]["success"] == 1
    assert migrator.stats["avatars"]["failed"] == 0
    assert migrator.stats["transcripts"]["failed"] == 0
    assert migrator.stats["history"]["failed"] == 0

@pytest.mark.asyncio
async def test_migration_rollback(test_bucket, test_user, test_data_dir, async_session):
    """Тест отката миграции при ошибке"""
    # Создаем запись в БД с несуществующим файлом
    avatar = UserAvatar(
        user_id=test_user.id,
        photo_key="non_existent.png",
        preview_key="non_existent_preview.png"
    )
    
    async_session.add(avatar)
    await async_session.commit()
    
    # Запускаем миграцию
    migrator = DataMigrator(async_session)
    await migrator.init_storage()
    
    # Миграция данных
    await migrator.migrate_avatars()
    
    # Проверяем статистику
    assert migrator.stats["avatars"]["failed"] == 1
    assert migrator.stats["avatars"]["rollback"] == 0  # Нечего откатывать, файл не был создан

@pytest.mark.asyncio
async def test_migration_partial_failure(test_bucket, test_user, test_data_dir, async_session):
    """Тест частичной ошибки миграции"""
    # Создаем записи в БД
    avatar1 = UserAvatar(
        user_id=test_user.id,
        photo_key=str(test_data_dir["paths"]["avatar"]["photo"].relative_to(test_data_dir["root"])),
        preview_key=str(test_data_dir["paths"]["avatar"]["preview"].relative_to(test_data_dir["root"]))
    )
    
    avatar2 = UserAvatar(
        user_id=test_user.id,
        photo_key="non_existent.png",
        preview_key="non_existent_preview.png"
    )
    
    async_session.add_all([avatar1, avatar2])
    await async_session.commit()
    
    # Запускаем миграцию
    migrator = DataMigrator(async_session)
    await migrator.init_storage()
    
    # Миграция данных
    await migrator.migrate_avatars()
    
    # Проверяем статистику
    assert migrator.stats["avatars"]["total"] == 2
    assert migrator.stats["avatars"]["success"] == 1
    assert migrator.stats["avatars"]["failed"] == 1
    
    # Валидация
    success = await migrator.validate_migration()
    assert success, "Validation should succeed for partially migrated data"

@pytest.mark.asyncio
async def test_avatar_migration(test_bucket, test_user, async_session):
    """Тест миграции аватаров"""
    avatar_service = AvatarService(async_session)
    
    # Создаем тестовые данные
    avatar_data = b"test avatar image data"
    preview_data = b"test avatar preview data"
    
    # Сохраняем аватар
    avatar = await avatar_service.save_avatar(
        user_id=test_user.id,
        photo_data=avatar_data,
        preview_data=preview_data
    )
    
    assert avatar.user_id == test_user.id
    assert avatar.photo_key.startswith("avatars/")
    assert avatar.preview_key.startswith("avatars/")
    
    # Проверяем, что файлы доступны в MinIO
    photo_data = await storage_utils.download_file(test_bucket, avatar.photo_key)
    preview_data = await storage_utils.download_file(test_bucket, avatar.preview_key)
    
    assert photo_data == avatar_data
    assert preview_data == preview_data

@pytest.mark.asyncio
async def test_transcript_migration(test_bucket, test_user, async_session):
    """Тест миграции транскриптов"""
    transcript_service = TranscriptService(async_session)
    
    # Создаем тестовые данные
    audio_data = b"test audio data"
    transcript_data = b"test transcript text"
    
    # Сохраняем транскрипт
    transcript = await transcript_service.save_transcript(
        user_id=test_user.id,
        audio_data=audio_data,
        transcript_data=transcript_data
    )
    
    assert transcript.user_id == test_user.id
    assert transcript.audio_key.startswith("transcripts/")
    assert transcript.transcript_key.startswith("transcripts/")
    
    # Проверяем, что файлы доступны в MinIO
    audio = await storage_utils.download_file(test_bucket, transcript.audio_key)
    transcript_text = await storage_utils.download_file(test_bucket, transcript.transcript_key)
    
    assert audio == audio_data
    assert transcript_text == transcript_data

@pytest.mark.asyncio
async def test_history_migration(test_bucket, test_user, async_session):
    """Тест миграции истории"""
    history_service = HistoryService(async_session)
    
    # Создаем тестовые данные
    history_data = b"test history data"
    
    # Сохраняем историю
    history = await history_service.save_history(
        user_id=test_user.id,
        content=history_data
    )
    
    assert history.user_id == test_user.id
    assert history.content_key.startswith("documents/")
    
    # Проверяем, что файл доступен в MinIO
    content = await storage_utils.download_file(test_bucket, history.content_key)
    assert content == history_data

@pytest.mark.asyncio
async def test_bulk_migration(test_bucket, test_user, async_session):
    """Тест массовой миграции данных"""
    avatar_service = AvatarService(async_session)
    transcript_service = TranscriptService(async_session)
    history_service = HistoryService(async_session)
    
    # Создаем тестовые данные
    test_data = {
        "avatar": (b"avatar data", b"preview data"),
        "transcript": (b"audio data", b"transcript text"),
        "history": (b"history content",)
    }
    
    # Сохраняем все типы данных
    avatar = await avatar_service.save_avatar(
        user_id=test_user.id,
        photo_data=test_data["avatar"][0],
        preview_data=test_data["avatar"][1]
    )
    
    transcript = await transcript_service.save_transcript(
        user_id=test_user.id,
        audio_data=test_data["transcript"][0],
        transcript_data=test_data["transcript"][1]
    )
    
    history = await history_service.save_history(
        user_id=test_user.id,
        content=test_data["history"][0]
    )
    
    # Проверяем, что все файлы доступны
    assert await storage_utils.download_file(test_bucket, avatar.photo_key) == test_data["avatar"][0]
    assert await storage_utils.download_file(test_bucket, avatar.preview_key) == test_data["avatar"][1]
    assert await storage_utils.download_file(test_bucket, transcript.audio_key) == test_data["transcript"][0]
    assert await storage_utils.download_file(test_bucket, transcript.transcript_key) == test_data["transcript"][1]
    assert await storage_utils.download_file(test_bucket, history.content_key) == test_data["history"][0]

@pytest.mark.asyncio
async def test_migration_cleanup(test_bucket, test_user, async_session):
    """Тест очистки после миграции"""
    avatar_service = AvatarService(async_session)
    
    # Создаем тестовые данные
    avatar = await avatar_service.save_avatar(
        user_id=test_user.id,
        photo_data=b"test data",
        preview_data=b"test preview"
    )
    
    # Удаляем аватар
    await avatar_service.delete_avatar(avatar.id)
    
    # Проверяем, что файлы удалены из MinIO
    with pytest.raises(Exception):
        await storage_utils.download_file(test_bucket, avatar.photo_key)
    
    with pytest.raises(Exception):
        await storage_utils.download_file(test_bucket, avatar.preview_key)
    
    # Проверяем, что запись удалена из БД
    deleted_avatar = await async_session.get(UserAvatar, avatar.id)
    assert deleted_avatar is None 