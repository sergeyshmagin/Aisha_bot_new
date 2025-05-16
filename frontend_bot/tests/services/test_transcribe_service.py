"""
Тесты для сервиса транскрибации.
"""

import pytest
import os
from pathlib import Path
import aiofiles
import json
from frontend_bot.services.transcribe_service import (
    ensure_transcribe_dirs,
    save_transcribe_file,
    get_user_transcribe_files,
    delete_transcribe_file,
    cleanup_user_transcribe_files
)

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
    await ensure_transcribe_dirs(temp_dir)
    assert os.path.exists(temp_dir / "transcribe")

@pytest.mark.asyncio
async def test_save_transcribe_file(temp_dir):
    """Тест сохранения файла."""
    file_data = b"test_file_data"
    file_name = "test_file.txt"
    file_path = await save_transcribe_file("123", file_data, file_name, temp_dir)
    assert os.path.exists(file_path)
    assert file_path.name == file_name

@pytest.mark.asyncio
async def test_get_user_transcribe_files(temp_dir):
    """Тест получения списка файлов."""
    # Создаем тестовые файлы
    await save_transcribe_file("123", b"file1", "file1.txt", temp_dir)
    await save_transcribe_file("123", b"file2", "file2.txt", temp_dir)
    
    files = await get_user_transcribe_files("123", temp_dir)
    assert len(files) == 2
    assert all(f.name.endswith(".txt") for f in files)

@pytest.mark.asyncio
async def test_delete_transcribe_file(temp_dir):
    """Тест удаления файла."""
    # Создаем тестовый файл
    file_name = "test_file.txt"
    await save_transcribe_file("123", b"test_data", file_name, temp_dir)
    
    # Удаляем файл
    result = await delete_transcribe_file("123", file_name, temp_dir)
    assert result is True
    
    # Проверяем, что файл удален
    files = await get_user_transcribe_files("123", temp_dir)
    assert len(files) == 0

@pytest.mark.asyncio
async def test_cleanup_user_transcribe_files(temp_dir):
    """Тест очистки файлов пользователя."""
    # Создаем тестовые файлы
    await save_transcribe_file("123", b"file1", "file1.txt", temp_dir)
    await save_transcribe_file("123", b"file2", "file2.txt", temp_dir)
    
    await cleanup_user_transcribe_files("123", temp_dir)
    files = await get_user_transcribe_files("123", temp_dir)
    assert len(files) == 0 