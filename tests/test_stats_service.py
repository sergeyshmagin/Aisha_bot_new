"""
Тесты для сервиса статистики.
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID

from frontend_bot.services.stats_service import StatsService
from database.models import UserStats

@pytest.fixture
def stats_service(session):
    """Создает экземпляр сервиса статистики."""
    return StatsService(session)

@pytest.fixture
def test_stats_data():
    """Создает тестовые данные статистики."""
    return {
        "messages_count": 100,
        "commands_count": 50,
        "errors_count": 5,
        "last_activity": datetime.utcnow(),
        "stats_data": {
            "key1": "value1",
            "key2": "value2"
        }
    }

@pytest.mark.asyncio
async def test_create_stats(stats_service, test_user_data, test_stats_data):
    """Тест создания статистики."""
    # Создаем пользователя
    user = await stats_service.create_user(**test_user_data)
    assert user.id == test_user_data["id"]
    
    # Создаем статистику
    stats = await stats_service.create_stats(
        user_id=user.id,
        **test_stats_data
    )
    
    assert isinstance(stats.id, UUID)
    assert stats.user_id == user.id
    assert stats.messages_count == test_stats_data["messages_count"]
    assert stats.commands_count == test_stats_data["commands_count"]
    assert stats.errors_count == test_stats_data["errors_count"]
    assert stats.last_activity == test_stats_data["last_activity"]
    assert stats.stats_data == test_stats_data["stats_data"]
    assert isinstance(stats.created_at, datetime)
    assert isinstance(stats.updated_at, datetime)

@pytest.mark.asyncio
async def test_get_stats(stats_service, test_user_data, test_stats_data):
    """Тест получения статистики."""
    # Создаем пользователя
    user = await stats_service.create_user(**test_user_data)
    
    # Создаем статистику
    stats = await stats_service.create_stats(
        user_id=user.id,
        **test_stats_data
    )
    
    # Получаем статистику
    retrieved_stats = await stats_service.get_stats(user.id)
    assert retrieved_stats.id == stats.id
    assert retrieved_stats.user_id == user.id
    assert retrieved_stats.messages_count == test_stats_data["messages_count"]
    assert retrieved_stats.commands_count == test_stats_data["commands_count"]
    assert retrieved_stats.errors_count == test_stats_data["errors_count"]
    assert retrieved_stats.last_activity == test_stats_data["last_activity"]
    assert retrieved_stats.stats_data == test_stats_data["stats_data"]

@pytest.mark.asyncio
async def test_update_stats(stats_service, test_user_data, test_stats_data):
    """Тест обновления статистики."""
    # Создаем пользователя
    user = await stats_service.create_user(**test_user_data)
    
    # Создаем статистику
    stats = await stats_service.create_stats(
        user_id=user.id,
        **test_stats_data
    )
    
    # Обновляем статистику
    updated_data = {
        "messages_count": 200,
        "commands_count": 100,
        "errors_count": 10,
        "last_activity": datetime.utcnow(),
        "stats_data": {
            "key3": "value3",
            "key4": "value4"
        }
    }
    
    updated_stats = await stats_service.update_stats(
        user.id,
        **updated_data
    )
    
    assert updated_stats.id == stats.id
    assert updated_stats.user_id == user.id
    assert updated_stats.messages_count == updated_data["messages_count"]
    assert updated_stats.commands_count == updated_data["commands_count"]
    assert updated_stats.errors_count == updated_data["errors_count"]
    assert updated_stats.last_activity == updated_data["last_activity"]
    assert updated_stats.stats_data == updated_data["stats_data"]
    assert updated_stats.updated_at > stats.updated_at

@pytest.mark.asyncio
async def test_delete_stats(stats_service, test_user_data, test_stats_data):
    """Тест удаления статистики."""
    # Создаем пользователя
    user = await stats_service.create_user(**test_user_data)
    
    # Создаем статистику
    stats = await stats_service.create_stats(
        user_id=user.id,
        **test_stats_data
    )
    
    # Удаляем статистику
    await stats_service.delete_stats(user.id)
    
    # Проверяем, что статистика удалена
    retrieved_stats = await stats_service.get_stats(user.id)
    assert retrieved_stats is None

@pytest.mark.asyncio
async def test_get_active_users(stats_service, test_user_data, test_stats_data):
    """Тест получения активных пользователей."""
    # Создаем пользователей
    user1 = await stats_service.create_user(**test_user_data)
    user2 = await stats_service.create_user(**{**test_user_data, "id": UUID(int=2)})
    
    # Создаем статистику с разной активностью
    now = datetime.utcnow()
    await stats_service.create_stats(
        user_id=user1.id,
        **{**test_stats_data, "last_activity": now}
    )
    await stats_service.create_stats(
        user_id=user2.id,
        **{**test_stats_data, "last_activity": now - timedelta(days=2)}
    )
    
    # Получаем активных пользователей за последние 24 часа
    active_users = await stats_service.get_active_users(timedelta(days=1))
    assert len(active_users) == 1
    assert active_users[0].user_id == user1.id

@pytest.mark.asyncio
async def test_get_top_users(stats_service, test_user_data, test_stats_data):
    """Тест получения топ пользователей."""
    # Создаем пользователей
    user1 = await stats_service.create_user(**test_user_data)
    user2 = await stats_service.create_user(**{**test_user_data, "id": UUID(int=2)})
    
    # Создаем статистику с разным количеством сообщений
    await stats_service.create_stats(
        user_id=user1.id,
        **{**test_stats_data, "messages_count": 200}
    )
    await stats_service.create_stats(
        user_id=user2.id,
        **{**test_stats_data, "messages_count": 100}
    )
    
    # Получаем топ пользователей по количеству сообщений
    top_users = await stats_service.get_top_users("messages_count", limit=1)
    assert len(top_users) == 1
    assert top_users[0].user_id == user1.id
    assert top_users[0].messages_count == 200 