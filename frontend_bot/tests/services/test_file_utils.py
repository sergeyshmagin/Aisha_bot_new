"""
Тесты для утилит работы с файлами.
"""

import pytest
from pathlib import Path
from frontend_bot.services.file_utils import FileUtils
from frontend_bot.config import MAX_FILE_SIZE

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
async def test_save_file(file_utils):
    """Тест сохранения файла."""
    file_data = b"test file content"
    file_name = "test.txt"
    
    file_path = await file_utils.save_file(file_data, file_name)
    
    assert file_path.is_absolute()
    assert file_path.suffix == ".txt"
    assert await file_utils.get_file_size(file_path) == len(file_data)

@pytest.mark.asyncio
async def test_get_file_size(file_utils):
    """Тест получения размера файла."""
    file_data = b"test content"
    file_name = "test.txt"
    
    file_path = await file_utils.save_file(file_data, file_name)
    size = await file_utils.get_file_size(file_path)
    
    assert size == len(file_data)
    
    # Проверка несуществующего файла
    assert await file_utils.get_file_size(Path("nonexistent.txt")) is None

@pytest.mark.asyncio
async def test_is_file_too_large(file_utils):
    """Тест проверки размера файла."""
    # Создаем файл меньше максимального размера
    small_data = b"small content"
    small_file = await file_utils.save_file(small_data, "small.txt")
    assert not await file_utils.is_file_too_large(small_file)
    
    # Создаем файл больше максимального размера
    large_data = b"x" * (MAX_FILE_SIZE + 1)
    large_file = await file_utils.save_file(large_data, "large.txt")
    assert await file_utils.is_file_too_large(large_file)
    
    # Проверка несуществующего файла
    assert not await file_utils.is_file_too_large(Path("nonexistent.txt"))

@pytest.mark.asyncio
async def test_get_file_type(file_utils):
    """Тест определения типа файла."""
    # Текстовый файл
    text_file = await file_utils.save_file(b"text content", "test.txt")
    assert await file_utils.get_file_type(text_file) == "text/plain"
    
    # Изображение
    image_file = await file_utils.save_file(b"image data", "test.jpg")
    assert await file_utils.get_file_type(image_file) == "image/jpeg"
    
    # Неизвестный тип
    unknown_file = await file_utils.save_file(b"data", "test.xyz")
    assert await file_utils.get_file_type(unknown_file) == "application/octet-stream"

@pytest.mark.asyncio
async def test_is_valid_file_type(file_utils):
    """Тест проверки допустимого типа файла."""
    # Создаем файлы разных типов
    text_file = await file_utils.save_file(b"text content", "test.txt")
    image_file = await file_utils.save_file(b"image data", "test.jpg")
    
    # Проверяем допустимые типы
    allowed_types = ["text/plain", "image/jpeg"]
    assert await file_utils.is_valid_file_type(text_file, allowed_types)
    assert await file_utils.is_valid_file_type(image_file, allowed_types)
    
    # Проверяем недопустимый тип
    assert not await file_utils.is_valid_file_type(text_file, ["image/jpeg"])
    assert not await file_utils.is_valid_file_type(image_file, ["text/plain"])

@pytest.mark.asyncio
async def test_delete_file(file_utils):
    """Тест удаления файла."""
    file_data = b"test content"
    file_name = "test.txt"
    
    file_path = await file_utils.save_file(file_data, file_name)
    assert await file_utils.get_file_size(file_path) is not None
    
    await file_utils.delete_file(file_path)
    assert await file_utils.get_file_size(file_path) is None
    
    # Должно работать без ошибок при повторном удалении
    await file_utils.delete_file(file_path)

@pytest.mark.asyncio
async def test_list_files(file_utils):
    """Тест получения списка файлов."""
    # Создаем тестовые файлы
    files = [
        ("test1.txt", b"content1"),
        ("test2.jpg", b"content2"),
        ("test3.txt", b"content3")
    ]
    
    for file_name, file_data in files:
        await file_utils.save_file(file_data, file_name)
    
    # Получаем все файлы
    all_files = await file_utils.list_files()
    assert len(all_files) == len(files)
    
    # Получаем только txt файлы
    txt_files = await file_utils.list_files("*.txt")
    assert len(txt_files) == 2
    assert all(f.suffix == ".txt" for f in txt_files)
    
    # Получаем только jpg файлы
    jpg_files = await file_utils.list_files("*.jpg")
    assert len(jpg_files) == 1
    assert all(f.suffix == ".jpg" for f in jpg_files) 