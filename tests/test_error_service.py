"""
Тесты для сервиса ошибок.
"""

import pytest
from datetime import datetime
from uuid import UUID

from frontend_bot.services.error_service import ErrorService
from database.models import Error

@pytest.fixture
def error_service(session):
    """Создает экземпляр сервиса ошибок."""
    return ErrorService(session)

@pytest.fixture
def test_error_data():
    """Создает тестовые данные ошибки."""
    return {
        "error_type": "test_error",
        "error_message": "Test error message",
        "error_data": {
            "key1": "value1",
            "key2": "value2"
        },
        "stack_trace": "Test stack trace"
    }

@pytest.mark.asyncio
async def test_create_error(error_service, test_user_data, test_error_data):
    """Тест создания ошибки."""
    # Создаем пользователя
    user = await error_service.create_user(**test_user_data)
    assert user.id == test_user_data["id"]
    
    # Создаем ошибку
    error = await error_service.create_error(
        user_id=user.id,
        **test_error_data
    )
    
    assert isinstance(error.id, UUID)
    assert error.user_id == user.id
    assert error.error_type == test_error_data["error_type"]
    assert error.error_message == test_error_data["error_message"]
    assert error.error_data == test_error_data["error_data"]
    assert error.stack_trace == test_error_data["stack_trace"]
    assert isinstance(error.created_at, datetime)

@pytest.mark.asyncio
async def test_get_error(error_service, test_user_data, test_error_data):
    """Тест получения ошибки."""
    # Создаем пользователя
    user = await error_service.create_user(**test_user_data)
    
    # Создаем ошибку
    error = await error_service.create_error(
        user_id=user.id,
        **test_error_data
    )
    
    # Получаем ошибку
    retrieved_error = await error_service.get_error(error.id)
    assert retrieved_error.id == error.id
    assert retrieved_error.user_id == user.id
    assert retrieved_error.error_type == test_error_data["error_type"]
    assert retrieved_error.error_message == test_error_data["error_message"]
    assert retrieved_error.error_data == test_error_data["error_data"]
    assert retrieved_error.stack_trace == test_error_data["stack_trace"]

@pytest.mark.asyncio
async def test_delete_error(error_service, test_user_data, test_error_data):
    """Тест удаления ошибки."""
    # Создаем пользователя
    user = await error_service.create_user(**test_user_data)
    
    # Создаем ошибку
    error = await error_service.create_error(
        user_id=user.id,
        **test_error_data
    )
    
    # Удаляем ошибку
    await error_service.delete_error(error.id)
    
    # Проверяем, что ошибка удалена
    retrieved_error = await error_service.get_error(error.id)
    assert retrieved_error is None

@pytest.mark.asyncio
async def test_get_user_errors(error_service, test_user_data, test_error_data):
    """Тест получения ошибок пользователя."""
    # Создаем пользователя
    user = await error_service.create_user(**test_user_data)
    
    # Создаем ошибки
    error1 = await error_service.create_error(
        user_id=user.id,
        **test_error_data
    )
    error2 = await error_service.create_error(
        user_id=user.id,
        **{**test_error_data, "error_type": "test_error2"}
    )
    
    # Получаем ошибки пользователя
    user_errors = await error_service.get_user_errors(user.id)
    assert len(user_errors) == 2
    assert all(isinstance(e.id, UUID) for e in user_errors)
    assert all(e.user_id == user.id for e in user_errors)
    assert {e.error_type for e in user_errors} == {"test_error", "test_error2"}

@pytest.mark.asyncio
async def test_get_errors_by_type(error_service, test_user_data, test_error_data):
    """Тест получения ошибок по типу."""
    # Создаем пользователя
    user = await error_service.create_user(**test_user_data)
    
    # Создаем ошибки разных типов
    await error_service.create_error(
        user_id=user.id,
        **test_error_data
    )
    await error_service.create_error(
        user_id=user.id,
        **{**test_error_data, "error_type": "test_error2"}
    )
    
    # Получаем ошибки по типу
    type1_errors = await error_service.get_errors_by_type("test_error")
    assert len(type1_errors) == 1
    assert type1_errors[0].error_type == "test_error"
    
    type2_errors = await error_service.get_errors_by_type("test_error2")
    assert len(type2_errors) == 1
    assert type2_errors[0].error_type == "test_error2"

@pytest.mark.asyncio
async def test_get_errors_by_data(error_service, test_user_data, test_error_data):
    """Тест получения ошибок по данным."""
    # Создаем пользователя
    user = await error_service.create_user(**test_user_data)
    
    # Создаем ошибки с разными данными
    await error_service.create_error(
        user_id=user.id,
        **test_error_data
    )
    await error_service.create_error(
        user_id=user.id,
        **{**test_error_data, "error_type": "test_error2", "error_data": {"key3": "value3"}}
    )
    
    # Получаем ошибки по данным
    errors_with_key1 = await error_service.get_errors_by_data("key1", "value1")
    assert len(errors_with_key1) == 1
    assert errors_with_key1[0].error_data["key1"] == "value1"
    
    errors_with_key3 = await error_service.get_errors_by_data("key3", "value3")
    assert len(errors_with_key3) == 1
    assert errors_with_key3[0].error_data["key3"] == "value3" 