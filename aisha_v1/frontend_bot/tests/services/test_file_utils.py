"""
Тесты для утилит работы с файлами.
"""

import pytest
from pathlib import Path
from frontend_bot.services.file_utils import FileUtils
from frontend_bot.config import settings
import os
import shutil
import tempfile
from frontend_bot.services.file_utils import (
    async_exists, async_makedirs, async_remove, async_rmtree, async_getsize, is_audio_file_ffmpeg
)
import aiofiles
import json

@pytest.fixture
def temp_dir(tmp_path):
    """Создает временную директорию для тестов."""
    return tmp_path

@pytest.fixture
async def setup_file_utils(temp_dir):
    """Создает экземпляр FileUtils для тестов."""
    return FileUtils(temp_dir)

@pytest.fixture
async def file_utils(tmp_path):
    """Создает экземпляр FileUtils с временной директорией."""
    utils = FileUtils(storage_dir=tmp_path)
    yield utils
    # Очистка после тестов
    await utils._ensure_storage_dir()
    files = await utils.list_files()
    for file in files:
        await utils.delete_file(file)

@pytest.mark.asyncio
async def test_save_file(setup_file_utils):
    """Тест сохранения файла."""
    file_data = b"test data"
    file_name = "test.txt"
    file_path = await setup_file_utils.save_file(file_data, file_name)
    assert await async_exists(file_path)
    assert file_path.read_bytes() == file_data

@pytest.mark.asyncio
async def test_get_file_size(setup_file_utils):
    """Тест получения размера файла."""
    file_path = setup_file_utils.storage_dir / "test.txt"
    file_path.write_bytes(b"hello")
    size = await setup_file_utils.get_file_size(file_path)
    assert size == 5

@pytest.mark.asyncio
async def test_is_file_too_large(setup_file_utils):
    """Тест проверки превышения размера файла."""
    file_path = setup_file_utils.storage_dir / "large.txt"
    file_path.write_bytes(b"x" * (settings.MAX_FILE_SIZE + 1))
    assert await setup_file_utils.is_file_too_large(file_path)

@pytest.mark.asyncio
async def test_get_file_type(setup_file_utils):
    """Тест определения типа файла."""
    file_path = setup_file_utils.storage_dir / "test.txt"
    file_path.write_bytes(b"hello")
    file_type = await setup_file_utils.get_file_type(file_path)
    assert file_type == "text/plain"

@pytest.mark.asyncio
async def test_is_valid_file_type(setup_file_utils):
    """Тест проверки допустимого типа файла."""
    file_path = setup_file_utils.storage_dir / "test.txt"
    file_path.write_bytes(b"hello")
    assert await setup_file_utils.is_valid_file_type(file_path, ["text/plain"])

@pytest.mark.asyncio
async def test_delete_file(setup_file_utils):
    """Тест удаления файла."""
    file_path = setup_file_utils.storage_dir / "test.txt"
    file_path.write_bytes(b"hello")
    assert await async_exists(file_path)
    await setup_file_utils.delete_file(file_path)
    assert not await async_exists(file_path)

@pytest.mark.asyncio
async def test_list_files(setup_file_utils):
    """Тест получения списка файлов."""
    file_path = setup_file_utils.storage_dir / "test.txt"
    file_path.write_bytes(b"hello")
    files = await setup_file_utils.list_files("*.txt")
    assert len(files) == 1
    assert files[0].name == "test.txt"

@pytest.mark.asyncio
async def test_async_exists_and_makedirs(temp_dir):
    """Тест проверки существования и создания директории."""
    dir_path = temp_dir / "testdir"
    assert not await async_exists(dir_path)
    await async_makedirs(dir_path)
    assert await async_exists(dir_path)

@pytest.mark.asyncio
async def test_async_remove_and_getsize(temp_dir):
    """Тест удаления файла и получения его размера."""
    file_path = temp_dir / "testfile.txt"
    file_path.write_bytes(b"hello")
    assert await async_exists(file_path)
    size = await async_getsize(file_path)
    assert size == 5
    await async_remove(file_path)
    assert not await async_exists(file_path)

@pytest.mark.asyncio
async def test_async_rmtree(temp_dir):
    """Тест рекурсивного удаления директории."""
    dir_path = temp_dir / "testdir"
    await async_makedirs(dir_path)
    file_path = dir_path / "testfile.txt"
    file_path.write_bytes(b"hello")
    assert await async_exists(dir_path)
    await async_rmtree(dir_path)
    assert not await async_exists(dir_path)

@pytest.mark.asyncio
async def test_is_audio_file_ffmpeg(temp_dir):
    """Тест проверки аудиофайла."""
    file_path = temp_dir / "test.mp3"
    file_path.write_bytes(b"fake audio data")
    assert await is_audio_file_ffmpeg(file_path) 