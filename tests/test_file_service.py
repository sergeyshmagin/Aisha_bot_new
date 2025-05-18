"""
Тесты для сервиса файлов.
"""

import pytest
from datetime import datetime
from uuid import UUID
import io

from frontend_bot.services.file_service import FileService
from database.models import File

@pytest.fixture
def file_service(session):
    """Создает экземпляр сервиса файлов."""
    return FileService(session)

@pytest.fixture
def test_file_data():
    """Создает тестовые данные файла."""
    return {
        "file_name": "test_file",
        "file_type": "text/plain",
        "file_size": 1024,
        "file_path": "/path/to/test_file.txt",
        "file_data": {
            "key1": "value1",
            "key2": "value2"
        }
    }

@pytest.mark.asyncio
async def test_create_file(file_service, test_user_data, test_file_data):
    """Тест создания файла."""
    # Создаем пользователя
    user = await file_service.create_user(**test_user_data)
    assert user.id == test_user_data["id"]
    
    # Создаем файл
    file = await file_service.create_file(
        user_id=user.id,
        **test_file_data
    )
    
    assert isinstance(file.id, UUID)
    assert file.user_id == user.id
    assert file.file_name == test_file_data["file_name"]
    assert file.file_type == test_file_data["file_type"]
    assert file.file_size == test_file_data["file_size"]
    assert file.file_path == test_file_data["file_path"]
    assert file.file_data == test_file_data["file_data"]
    assert isinstance(file.created_at, datetime)
    assert isinstance(file.updated_at, datetime)

@pytest.mark.asyncio
async def test_get_file(file_service, test_user_data, test_file_data):
    """Тест получения файла."""
    # Создаем пользователя
    user = await file_service.create_user(**test_user_data)
    
    # Создаем файл
    file = await file_service.create_file(
        user_id=user.id,
        **test_file_data
    )
    
    # Получаем файл
    retrieved_file = await file_service.get_file(file.id)
    assert retrieved_file.id == file.id
    assert retrieved_file.user_id == user.id
    assert retrieved_file.file_name == test_file_data["file_name"]
    assert retrieved_file.file_type == test_file_data["file_type"]
    assert retrieved_file.file_size == test_file_data["file_size"]
    assert retrieved_file.file_path == test_file_data["file_path"]
    assert retrieved_file.file_data == test_file_data["file_data"]

@pytest.mark.asyncio
async def test_get_user_files(file_service, test_user_data, test_file_data):
    """Тест получения файлов пользователя."""
    # Создаем пользователя
    user = await file_service.create_user(**test_user_data)
    
    # Создаем файлы
    file1 = await file_service.create_file(
        user_id=user.id,
        **test_file_data
    )
    file2 = await file_service.create_file(
        user_id=user.id,
        **{**test_file_data, "file_name": "test_file2"}
    )
    
    # Получаем файлы пользователя
    user_files = await file_service.get_user_files(user.id)
    assert len(user_files) == 2
    assert all(isinstance(f.id, UUID) for f in user_files)
    assert all(f.user_id == user.id for f in user_files)
    assert {f.file_name for f in user_files} == {"test_file", "test_file2"}

@pytest.mark.asyncio
async def test_update_file(file_service, test_user_data, test_file_data):
    """Тест обновления файла."""
    # Создаем пользователя
    user = await file_service.create_user(**test_user_data)
    
    # Создаем файл
    file = await file_service.create_file(
        user_id=user.id,
        **test_file_data
    )
    
    # Обновляем файл
    updated_data = {
        "file_name": "updated_file",
        "file_type": "text/markdown",
        "file_size": 2048,
        "file_path": "/path/to/updated_file.md",
        "file_data": {
            "key3": "value3",
            "key4": "value4"
        }
    }
    
    updated_file = await file_service.update_file(
        file.id,
        **updated_data
    )
    
    assert updated_file.id == file.id
    assert updated_file.user_id == user.id
    assert updated_file.file_name == updated_data["file_name"]
    assert updated_file.file_type == updated_data["file_type"]
    assert updated_file.file_size == updated_data["file_size"]
    assert updated_file.file_path == updated_data["file_path"]
    assert updated_file.file_data == updated_data["file_data"]
    assert updated_file.updated_at > file.updated_at

@pytest.mark.asyncio
async def test_delete_file(file_service, test_user_data, test_file_data):
    """Тест удаления файла."""
    # Создаем пользователя
    user = await file_service.create_user(**test_user_data)
    
    # Создаем файл
    file = await file_service.create_file(
        user_id=user.id,
        **test_file_data
    )
    
    # Удаляем файл
    await file_service.delete_file(file.id)
    
    # Проверяем, что файл удален
    retrieved_file = await file_service.get_file(file.id)
    assert retrieved_file is None

@pytest.mark.asyncio
async def test_get_files_by_type(file_service, test_user_data, test_file_data):
    """Тест получения файлов по типу."""
    # Создаем пользователя
    user = await file_service.create_user(**test_user_data)
    
    # Создаем файлы разных типов
    await file_service.create_file(
        user_id=user.id,
        **test_file_data
    )
    await file_service.create_file(
        user_id=user.id,
        **{**test_file_data, "file_name": "test_file2", "file_type": "text/markdown"}
    )
    
    # Получаем файлы по типу
    plain_files = await file_service.get_files_by_type("text/plain")
    assert len(plain_files) == 1
    assert plain_files[0].file_type == "text/plain"
    
    markdown_files = await file_service.get_files_by_type("text/markdown")
    assert len(markdown_files) == 1
    assert markdown_files[0].file_type == "text/markdown"

@pytest.mark.asyncio
async def test_get_files_by_data(file_service, test_user_data, test_file_data):
    """Тест получения файлов по данным."""
    # Создаем пользователя
    user = await file_service.create_user(**test_user_data)
    
    # Создаем файлы с разными данными
    await file_service.create_file(
        user_id=user.id,
        **test_file_data
    )
    await file_service.create_file(
        user_id=user.id,
        **{**test_file_data, "file_name": "test_file2", "file_data": {"key3": "value3"}}
    )
    
    # Получаем файлы по данным
    files_with_key1 = await file_service.get_files_by_data("key1", "value1")
    assert len(files_with_key1) == 1
    assert files_with_key1[0].file_data["key1"] == "value1"
    
    files_with_key3 = await file_service.get_files_by_data("key3", "value3")
    assert len(files_with_key3) == 1
    assert files_with_key3[0].file_data["key3"] == "value3"

@pytest.mark.asyncio
async def test_get_file_content(file_service, test_user_data, test_file_data):
    """Тест получения содержимого файла."""
    # Создаем пользователя
    user = await file_service.create_user(**test_user_data)
    
    # Создаем файл
    file = await file_service.create_file(
        user_id=user.id,
        **test_file_data
    )
    
    # Получаем содержимое файла
    content = await file_service.get_file_content(file.id)
    assert content == test_file_data["file_data"]

@pytest.mark.asyncio
async def test_get_file_stream(file_service, test_user_data, test_file_data):
    """Тест получения потока файла."""
    # Создаем пользователя
    user = await file_service.create_user(**test_user_data)
    
    # Создаем файл
    file = await file_service.create_file(
        user_id=user.id,
        **test_file_data
    )
    
    # Получаем поток файла
    stream = await file_service.get_file_stream(file.id)
    assert isinstance(stream, io.BytesIO)
    assert stream.read() == test_file_data["file_data"] 