"""
Тесты для сервиса транскрибации.
"""

import pytest
import os
from pathlib import Path
import aiofiles
import json
import asyncio
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from frontend_bot.services.transcribe_service import (
    ensure_transcribe_dirs,
    save_transcribe_file,
    get_user_transcribe_files,
    delete_transcribe_file,
    cleanup_user_transcribe_files,
    save_audio_file
)
from frontend_bot.shared.file_operations import AsyncFileManager
import logging

@pytest.fixture
def temp_dir(tmp_path):
    """Создает временную директорию для тестов."""
    return tmp_path

@pytest.fixture
async def setup_transcribe_dirs(temp_dir):
    """Создает необходимые директории для тестов."""
    await ensure_transcribe_dirs(temp_dir)
    return temp_dir

@pytest.mark.asyncio
async def test_ensure_transcribe_dirs(temp_dir):
    """Тест создания директорий."""
    print(f"[DEBUG] temp_dir: {temp_dir}")
    await asyncio.wait_for(ensure_transcribe_dirs(temp_dir), timeout=3)
    exists = await AsyncFileManager.exists(temp_dir / "transcribe")
    print(f"[DEBUG] exists: {exists}")
    assert exists

@pytest.mark.asyncio
async def test_save_transcribe_file(temp_dir):
    """Тест сохранения файла."""
    user_id = str(uuid4())
    await ensure_transcribe_dirs(temp_dir)
    file_data = b"test_file_data"
    file_name = "test_file.txt"
    file_path = await save_transcribe_file(user_id, file_data, file_name, temp_dir)
    assert os.path.exists(file_path)
    assert file_path.name == file_name

@pytest.mark.asyncio
async def test_get_user_transcribe_files(temp_dir):
    """Тест получения списка файлов."""
    user_id = str(uuid4())
    await ensure_transcribe_dirs(temp_dir)
    await save_transcribe_file(user_id, b"file1", "file1.txt", temp_dir)
    await save_transcribe_file(user_id, b"file2", "file2.txt", temp_dir)
    files = await get_user_transcribe_files(user_id, temp_dir)
    assert len(files) == 2
    names = [f.name for f in files]
    assert "file1.txt" in names
    assert "file2.txt" in names

@pytest.mark.asyncio
async def test_delete_transcribe_file(temp_dir):
    """Тест удаления файла."""
    user_id = str(uuid4())
    await ensure_transcribe_dirs(temp_dir)
    file_name = "test_file.txt"
    await save_transcribe_file(user_id, b"test_data", file_name, temp_dir)
    
    # Удаляем файл
    result = await delete_transcribe_file(user_id, file_name, temp_dir)
    assert result is True
    
    # Проверяем, что файл удален
    files = await get_user_transcribe_files(user_id, temp_dir)
    assert len(files) == 0

@pytest.mark.asyncio
async def test_cleanup_user_transcribe_files(temp_dir):
    """Тест очистки файлов пользователя."""
    user_id = str(uuid4())
    await ensure_transcribe_dirs(temp_dir)
    await save_transcribe_file(user_id, b"file1", "file1.txt", temp_dir)
    await save_transcribe_file(user_id, b"file2", "file2.txt", temp_dir)
    
    await cleanup_user_transcribe_files(user_id, temp_dir)
    files = await get_user_transcribe_files(user_id, temp_dir)
    assert len(files) == 0

@pytest.mark.asyncio
async def test_save_audio_file(tmp_path):
    """Тест сохранения аудиофайла через save_audio_file с мок-ботом."""
    class MockBot:
        async def get_file(self, file_id):
            return MagicMock(file_path="mock/path/to/file.ogg")
        async def download_file(self, file_path):
            return b"audio-bytes"
    bot = MockBot()
    file_id = "test_file_id"
    ext = ".ogg"
    storage_dir = str(tmp_path)
    temp_file = await save_audio_file(file_id, ext, bot, storage_dir)
    assert os.path.exists(temp_file)
    with open(temp_file, "rb") as f:
        data = f.read()
    assert data == b"audio-bytes"
    os.remove(temp_file) 