"""
Тесты для асинхронного менеджера файловых операций.
"""

import os
import pytest
from pathlib import Path
from frontend_bot.shared.file_operations import AsyncFileManager

@pytest.fixture
async def temp_dir(tmp_path):
    """Создает временную директорию для тестов."""
    test_dir = tmp_path / "test_dir"
    await AsyncFileManager.ensure_dir(test_dir)
    yield test_dir
    await AsyncFileManager.safe_rmtree(test_dir)

@pytest.mark.asyncio
async def test_ensure_dir(temp_dir):
    """Тест создания директории."""
    test_path = temp_dir / "subdir"
    await AsyncFileManager.ensure_dir(test_path)
    assert await AsyncFileManager.exists(test_path)

@pytest.mark.asyncio
async def test_safe_remove(temp_dir):
    """Тест безопасного удаления файла."""
    test_file = temp_dir / "test.txt"
    await AsyncFileManager.write_file(test_file, "test content")
    assert await AsyncFileManager.exists(test_file)
    
    await AsyncFileManager.safe_remove(test_file)
    assert not await AsyncFileManager.exists(test_file)
    
    # Должно работать без ошибок при повторном удалении
    await AsyncFileManager.safe_remove(test_file)

@pytest.mark.asyncio
async def test_safe_rmtree(temp_dir):
    """Тест рекурсивного удаления директории."""
    subdir = temp_dir / "subdir"
    await AsyncFileManager.ensure_dir(subdir)
    test_file = subdir / "test.txt"
    await AsyncFileManager.write_file(test_file, "test content")
    
    assert await AsyncFileManager.exists(subdir)
    await AsyncFileManager.safe_rmtree(subdir)
    assert not await AsyncFileManager.exists(subdir)
    
    # Должно работать без ошибок при повторном удалении
    await AsyncFileManager.safe_rmtree(subdir)

@pytest.mark.asyncio
async def test_exists(temp_dir):
    """Тест проверки существования файла."""
    test_file = temp_dir / "test.txt"
    assert not await AsyncFileManager.exists(test_file)
    
    await AsyncFileManager.write_file(test_file, "test content")
    assert await AsyncFileManager.exists(test_file)

@pytest.mark.asyncio
async def test_get_size(temp_dir):
    """Тест получения размера файла."""
    test_file = temp_dir / "test.txt"
    content = "test content"
    await AsyncFileManager.write_file(test_file, content)
    
    size = await AsyncFileManager.get_size(test_file)
    assert size == len(content.encode())
    
    # Проверка несуществующего файла
    assert await AsyncFileManager.get_size(temp_dir / "nonexistent.txt") is None

@pytest.mark.asyncio
async def test_list_dir(temp_dir):
    """Тест получения списка файлов в директории."""
    # Создаем тестовые файлы
    files = ["file1.txt", "file2.txt", "file3.txt"]
    for file in files:
        await AsyncFileManager.write_file(temp_dir / file, "test content")
    
    # Получаем список файлов
    listed_files = await AsyncFileManager.list_dir(temp_dir)
    assert set(listed_files) == set(files)

@pytest.mark.asyncio
async def test_read_write_file(temp_dir):
    """Тест чтения и записи текстового файла."""
    test_file = temp_dir / "test.txt"
    content = "test content"
    
    # Запись
    await AsyncFileManager.write_file(test_file, content)
    assert await AsyncFileManager.exists(test_file)
    
    # Чтение
    read_content = await AsyncFileManager.read_file(test_file)
    assert read_content == content

@pytest.mark.asyncio
async def test_read_write_binary(temp_dir):
    """Тест чтения и записи бинарного файла."""
    test_file = temp_dir / "test.bin"
    content = b"test binary content"
    
    # Запись
    await AsyncFileManager.write_binary(test_file, content)
    assert await AsyncFileManager.exists(test_file)
    
    # Чтение
    read_content = await AsyncFileManager.read_binary(test_file)
    assert read_content == content

@pytest.mark.asyncio
async def test_file_encoding(temp_dir):
    """Тест работы с разными кодировками."""
    test_file = temp_dir / "test.txt"
    content = "тестовый контент"
    
    # Запись в UTF-8
    await AsyncFileManager.write_file(test_file, content, encoding="utf-8")
    read_content = await AsyncFileManager.read_file(test_file, encoding="utf-8")
    assert read_content == content
    
    # Запись в CP1251
    await AsyncFileManager.write_file(test_file, content, encoding="cp1251")
    read_content = await AsyncFileManager.read_file(test_file, encoding="cp1251")
    assert read_content == content

@pytest.mark.asyncio
async def test_nested_directories(temp_dir):
    """Тест работы с вложенными директориями."""
    # Создаем структуру директорий
    nested_dir = temp_dir / "level1" / "level2" / "level3"
    await AsyncFileManager.ensure_dir(nested_dir)
    
    # Проверяем создание
    assert await AsyncFileManager.exists(nested_dir)
    
    # Создаем файл в глубокой директории
    test_file = nested_dir / "test.txt"
    await AsyncFileManager.write_file(test_file, "test content")
    assert await AsyncFileManager.exists(test_file)
    
    # Удаляем всю структуру
    await AsyncFileManager.safe_rmtree(temp_dir / "level1")
    assert not await AsyncFileManager.exists(nested_dir)

@pytest.mark.asyncio
async def test_concurrent_operations(temp_dir):
    """Тест конкурентных операций с файлами."""
    import asyncio
    
    async def write_file(i):
        file_path = temp_dir / f"file_{i}.txt"
        await AsyncFileManager.write_file(file_path, f"content_{i}")
        return file_path
    
    # Создаем несколько файлов конкурентно
    tasks = [write_file(i) for i in range(5)]
    file_paths = await asyncio.gather(*tasks)
    
    # Проверяем, что все файлы созданы
    for path in file_paths:
        assert await AsyncFileManager.exists(path)
        content = await AsyncFileManager.read_file(path)
        assert content.startswith("content_")

@pytest.mark.asyncio
async def test_error_handling(temp_dir):
    """Тест обработки ошибок."""
    # Попытка чтения несуществующего файла
    with pytest.raises(FileNotFoundError):
        await AsyncFileManager.read_file(temp_dir / "nonexistent.txt")
    
    # Попытка записи в несуществующую директорию
    with pytest.raises(FileNotFoundError):
        await AsyncFileManager.write_file(temp_dir / "nonexistent" / "test.txt", "content")
    
    # Попытка удаления несуществующего файла (должно работать без ошибок)
    await AsyncFileManager.safe_remove(temp_dir / "nonexistent.txt")

@pytest.mark.asyncio
async def test_large_file_operations(temp_dir):
    """Тест работы с большими файлами."""
    # Создаем большой файл (1MB)
    large_content = "x" * (1024 * 1024)
    test_file = temp_dir / "large.txt"
    
    # Запись
    await AsyncFileManager.write_file(test_file, large_content)
    assert await AsyncFileManager.exists(test_file)
    
    # Проверка размера
    size = await AsyncFileManager.get_size(test_file)
    assert size == len(large_content.encode())
    
    # Чтение
    read_content = await AsyncFileManager.read_file(test_file)
    assert len(read_content) == len(large_content) 