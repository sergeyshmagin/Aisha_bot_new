"""
Тесты для сервиса истории.
"""

import pytest
from datetime import datetime
from uuid import UUID

from frontend_bot.services.history_service import HistoryService
from database.models import UserHistory

@pytest.fixture
def history_service(session):
    """Создает экземпляр сервиса истории."""
    return HistoryService(session)

@pytest.mark.asyncio
async def test_create_history(history_service, test_user_data, test_history_data):
    """Тест создания записи истории."""
    # Создаем пользователя
    user = await history_service.create_user(**test_user_data)
    assert user.id == test_user_data["id"]
    
    # Создаем запись истории
    history = await history_service.create_history(
        user_id=user.id,
        content_key=test_history_data["content_key"]
    )
    
    assert isinstance(history.id, UUID)
    assert history.user_id == user.id
    assert history.content_key == test_history_data["content_key"]
    assert isinstance(history.created_at, datetime)

@pytest.mark.asyncio
async def test_get_history(history_service, test_user_data, test_history_data):
    """Тест получения записи истории."""
    # Создаем пользователя
    user = await history_service.create_user(**test_user_data)
    
    # Создаем запись истории
    history = await history_service.create_history(
        user_id=user.id,
        content_key=test_history_data["content_key"]
    )
    
    # Получаем запись истории
    retrieved_history = await history_service.get_history(history.id)
    assert retrieved_history.id == history.id
    assert retrieved_history.user_id == user.id
    assert retrieved_history.content_key == test_history_data["content_key"]

@pytest.mark.asyncio
async def test_get_user_history(history_service, test_user_data, test_history_data):
    """Тест получения истории пользователя."""
    # Создаем пользователя
    user = await history_service.create_user(**test_user_data)
    
    # Создаем несколько записей истории
    history1 = await history_service.create_history(
        user_id=user.id,
        content_key=test_history_data["content_key"]
    )
    history2 = await history_service.create_history(
        user_id=user.id,
        content_key=test_history_data["content_key"]
    )
    
    # Получаем историю пользователя
    user_history = await history_service.get_user_history(user.id)
    assert len(user_history) == 2
    assert all(isinstance(h.id, UUID) for h in user_history)
    assert all(h.user_id == user.id for h in user_history)

@pytest.mark.asyncio
async def test_delete_history(history_service, test_user_data, test_history_data):
    """Тест удаления записи истории."""
    # Создаем пользователя
    user = await history_service.create_user(**test_user_data)
    
    # Создаем запись истории
    history = await history_service.create_history(
        user_id=user.id,
        content_key=test_history_data["content_key"]
    )
    
    # Удаляем запись истории
    await history_service.delete_history(history.id)
    
    # Проверяем, что запись удалена
    retrieved_history = await history_service.get_history(history.id)
    assert retrieved_history is None

@pytest.mark.asyncio
async def test_delete_user_history(history_service, test_user_data, test_history_data):
    """Тест удаления всей истории пользователя."""
    # Создаем пользователя
    user = await history_service.create_user(**test_user_data)
    
    # Создаем несколько записей истории
    await history_service.create_history(
        user_id=user.id,
        content_key=test_history_data["content_key"]
    )
    await history_service.create_history(
        user_id=user.id,
        content_key=test_history_data["content_key"]
    )
    
    # Удаляем всю историю пользователя
    await history_service.delete_user_history(user.id)
    
    # Проверяем, что все записи удалены
    user_history = await history_service.get_user_history(user.id)
    assert len(user_history) == 0 