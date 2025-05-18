"""
Тесты для сервиса логов.
"""

import pytest
from datetime import datetime
from uuid import UUID

from frontend_bot.services.log_service import LogService
from database.models import Log

@pytest.fixture
def log_service(session):
    """Создает экземпляр сервиса логов."""
    return LogService(session)

@pytest.fixture
def test_log_data():
    """Создает тестовые данные лога."""
    return {
        "level": "INFO",
        "message": "Test log message",
        "log_data": {
            "key1": "value1",
            "key2": "value2"
        },
        "source": "test.py",
        "line_number": 42
    }

@pytest.mark.asyncio
async def test_create_log(log_service, test_user_data, test_log_data):
    """Тест создания лога."""
    # Создаем пользователя
    user = await log_service.create_user(**test_user_data)
    assert user.id == test_user_data["id"]
    
    # Создаем лог
    log = await log_service.create_log(
        user_id=user.id,
        level=test_log_data["level"],
        message=test_log_data["message"],
        log_data=test_log_data["log_data"],
        source=test_log_data["source"],
        line_number=test_log_data["line_number"]
    )
    
    assert isinstance(log.id, UUID)
    assert log.user_id == user.id
    assert log.level == test_log_data["level"]
    assert log.message == test_log_data["message"]
    assert log.log_data == test_log_data["log_data"]
    assert log.source == test_log_data["source"]
    assert log.line_number == test_log_data["line_number"]
    assert isinstance(log.created_at, datetime)

@pytest.mark.asyncio
async def test_get_log(log_service, test_user_data, test_log_data):
    """Тест получения лога."""
    # Создаем пользователя
    user = await log_service.create_user(**test_user_data)
    
    # Создаем лог
    log = await log_service.create_log(
        user_id=user.id,
        level=test_log_data["level"],
        message=test_log_data["message"],
        log_data=test_log_data["log_data"],
        source=test_log_data["source"],
        line_number=test_log_data["line_number"]
    )
    
    # Получаем лог
    retrieved_log = await log_service.get_log(log.id)
    assert retrieved_log.id == log.id
    assert retrieved_log.user_id == user.id
    assert retrieved_log.level == test_log_data["level"]
    assert retrieved_log.message == test_log_data["message"]
    assert retrieved_log.log_data == test_log_data["log_data"]
    assert retrieved_log.source == test_log_data["source"]
    assert retrieved_log.line_number == test_log_data["line_number"]

@pytest.mark.asyncio
async def test_get_user_logs(log_service, test_user_data, test_log_data):
    """Тест получения логов пользователя."""
    # Создаем пользователя
    user = await log_service.create_user(**test_user_data)
    
    # Создаем несколько логов
    log1 = await log_service.create_log(
        user_id=user.id,
        level=test_log_data["level"],
        message=test_log_data["message"],
        log_data=test_log_data["log_data"],
        source=test_log_data["source"],
        line_number=test_log_data["line_number"]
    )
    log2 = await log_service.create_log(
        user_id=user.id,
        level="ERROR",
        message="Another test log",
        log_data=test_log_data["log_data"],
        source=test_log_data["source"],
        line_number=test_log_data["line_number"]
    )
    
    # Получаем логи пользователя
    user_logs = await log_service.get_user_logs(user.id)
    assert len(user_logs) == 2
    assert all(isinstance(l.id, UUID) for l in user_logs)
    assert all(l.user_id == user.id for l in user_logs)
    assert {l.level for l in user_logs} == {test_log_data["level"], "ERROR"}

@pytest.mark.asyncio
async def test_delete_log(log_service, test_user_data, test_log_data):
    """Тест удаления лога."""
    # Создаем пользователя
    user = await log_service.create_user(**test_user_data)
    
    # Создаем лог
    log = await log_service.create_log(
        user_id=user.id,
        level=test_log_data["level"],
        message=test_log_data["message"],
        log_data=test_log_data["log_data"],
        source=test_log_data["source"],
        line_number=test_log_data["line_number"]
    )
    
    # Удаляем лог
    await log_service.delete_log(log.id)
    
    # Проверяем, что лог удален
    retrieved_log = await log_service.get_log(log.id)
    assert retrieved_log is None

@pytest.mark.asyncio
async def test_delete_user_logs(log_service, test_user_data, test_log_data):
    """Тест удаления всех логов пользователя."""
    # Создаем пользователя
    user = await log_service.create_user(**test_user_data)
    
    # Создаем несколько логов
    await log_service.create_log(
        user_id=user.id,
        level=test_log_data["level"],
        message=test_log_data["message"],
        log_data=test_log_data["log_data"],
        source=test_log_data["source"],
        line_number=test_log_data["line_number"]
    )
    await log_service.create_log(
        user_id=user.id,
        level="ERROR",
        message="Another test log",
        log_data=test_log_data["log_data"],
        source=test_log_data["source"],
        line_number=test_log_data["line_number"]
    )
    
    # Удаляем все логи пользователя
    await log_service.delete_user_logs(user.id)
    
    # Проверяем, что все логи удалены
    user_logs = await log_service.get_user_logs(user.id)
    assert len(user_logs) == 0

@pytest.mark.asyncio
async def test_get_logs_by_level(log_service, test_user_data, test_log_data):
    """Тест получения логов по уровню."""
    # Создаем пользователя
    user = await log_service.create_user(**test_user_data)
    
    # Создаем несколько логов разных уровней
    await log_service.create_log(
        user_id=user.id,
        level=test_log_data["level"],
        message=test_log_data["message"],
        log_data=test_log_data["log_data"],
        source=test_log_data["source"],
        line_number=test_log_data["line_number"]
    )
    await log_service.create_log(
        user_id=user.id,
        level="ERROR",
        message="Another test log",
        log_data=test_log_data["log_data"],
        source=test_log_data["source"],
        line_number=test_log_data["line_number"]
    )
    
    # Получаем логи по уровню
    info_logs = await log_service.get_logs_by_level(test_log_data["level"])
    assert len(info_logs) == 1
    assert info_logs[0].level == test_log_data["level"]
    
    error_logs = await log_service.get_logs_by_level("ERROR")
    assert len(error_logs) == 1
    assert error_logs[0].level == "ERROR"

@pytest.mark.asyncio
async def test_get_logs_by_source(log_service, test_user_data, test_log_data):
    """Тест получения логов по источнику."""
    # Создаем пользователя
    user = await log_service.create_user(**test_user_data)
    
    # Создаем несколько логов из разных источников
    await log_service.create_log(
        user_id=user.id,
        level=test_log_data["level"],
        message=test_log_data["message"],
        log_data=test_log_data["log_data"],
        source=test_log_data["source"],
        line_number=test_log_data["line_number"]
    )
    await log_service.create_log(
        user_id=user.id,
        level="ERROR",
        message="Another test log",
        log_data=test_log_data["log_data"],
        source="another.py",
        line_number=test_log_data["line_number"]
    )
    
    # Получаем логи по источнику
    test_logs = await log_service.get_logs_by_source(test_log_data["source"])
    assert len(test_logs) == 1
    assert test_logs[0].source == test_log_data["source"]
    
    another_logs = await log_service.get_logs_by_source("another.py")
    assert len(another_logs) == 1
    assert another_logs[0].source == "another.py" 