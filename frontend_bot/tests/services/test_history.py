"""
Тесты для сервиса истории.
"""

import pytest
import os
from pathlib import Path
import aiofiles
import json
from datetime import datetime
from frontend_bot.services.history import (
    ensure_history_dirs,
    get_history_file_path,
    load_history,
    save_history,
    add_history_entry,
    get_user_history,
    clear_user_history
)

@pytest.fixture
def temp_dir(tmp_path):
    """Создает временную директорию для тестов."""
    return tmp_path

@pytest.fixture
async def setup_history_dirs(temp_dir):
    """Создает необходимые директории для тестов."""
    await ensure_history_dirs(temp_dir)
    return temp_dir

@pytest.mark.asyncio
async def test_ensure_history_dirs(temp_dir):
    """Тест создания директорий."""
    await ensure_history_dirs(temp_dir)
    assert os.path.exists(temp_dir / "history")

@pytest.mark.asyncio
async def test_get_history_file_path(temp_dir):
    """Тест получения пути к файлу истории."""
    path = await get_history_file_path("123", temp_dir)
    assert str(path).endswith("123.json")

@pytest.mark.asyncio
async def test_load_history_empty(temp_dir):
    """Тест загрузки пустой истории."""
    history = await load_history("123", temp_dir)
    assert history == []

@pytest.mark.asyncio
async def test_save_and_load_history(temp_dir):
    """Тест сохранения и загрузки истории."""
    test_history = [
        {"file_name": "test1.txt", "file_path": "/path/to/test1.txt"},
        {"file_name": "test2.txt", "file_path": "/path/to/test2.txt"}
    ]
    await save_history("123", test_history, temp_dir)
    loaded_history = await load_history("123", temp_dir)
    assert loaded_history == test_history

@pytest.mark.asyncio
async def test_add_history_entry(temp_dir):
    """Тест добавления записи в историю."""
    await clear_user_history("123", temp_dir)
    await add_history_entry("123", "test.txt", "/path/to/test.txt", temp_dir)
    history = await load_history("123", temp_dir)
    assert len(history) == 1
    assert history[0]["file_name"] == "test.txt"
    assert history[0]["file_path"] == "/path/to/test.txt"
    assert "created_at" in history[0]

@pytest.mark.asyncio
async def test_get_user_history(temp_dir):
    """Тест получения истории пользователя."""
    test_history = [
        {"file_name": "test1.txt", "file_path": "/path/to/test1.txt"},
        {"file_name": "test2.txt", "file_path": "/path/to/test2.txt"}
    ]
    await save_history("123", test_history, temp_dir)
    history = await get_user_history("123", temp_dir)
    assert history == test_history

@pytest.mark.asyncio
async def test_clear_user_history(temp_dir):
    """Тест очистки истории пользователя."""
    test_history = [
        {"file_name": "test1.txt", "file_path": "/path/to/test1.txt"}
    ]
    await save_history("123", test_history, temp_dir)
    await clear_user_history("123", temp_dir)
    history = await load_history("123", temp_dir)
    assert history == []

@pytest.mark.asyncio
async def test_load_history_broken_json(tmp_path):
    """Тест: если файл истории битый, возвращается пустой список."""
    user_id = "broken"
    history_path = await get_history_file_path(user_id, tmp_path)
    await ensure_history_dirs(tmp_path)
    # Записываем битый JSON
    async with aiofiles.open(history_path, "w", encoding="utf-8") as f:
        await f.write("{broken json}")
    history = await load_history(user_id, tmp_path)
    assert history == []

@pytest.mark.asyncio
async def test_save_history_raises_on_error(monkeypatch, tmp_path):
    """Тест: save_history выбрасывает исключение при ошибке записи."""
    user_id = "fail"
    test_history = [{"file_name": "a", "file_path": "/a"}]
    # Подменяем write_file, чтобы выбрасывал ошибку
    from frontend_bot.shared import file_operations
    orig_write_file = file_operations.AsyncFileManager.write_file
    async def fail_write(*args, **kwargs):
        raise IOError("fail write")
    file_operations.AsyncFileManager.write_file = fail_write
    with pytest.raises(IOError):
        await save_history(user_id, test_history, tmp_path)
    # Возвращаем оригинал
    file_operations.AsyncFileManager.write_file = orig_write_file 