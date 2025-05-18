"""
Тесты для сервиса пользователей.
"""

import pytest
from datetime import datetime
from uuid import UUID

from frontend_bot.services.user_service import UserService
from database.models import User

@pytest.fixture
def user_service(session):
    """Создает экземпляр сервиса пользователей."""
    return UserService(session)

@pytest.fixture
def test_user_data():
    """Создает тестовые данные пользователя."""
    return {
        "telegram_id": 123456789,
        "username": "test_user",
        "first_name": "Test",
        "last_name": "User",
        "language_code": "ru",
        "user_data": {
            "key1": "value1",
            "key2": "value2"
        }
    }

@pytest.mark.asyncio
async def test_create_user(user_service, test_user_data):
    """Тест создания пользователя."""
    # Создаем пользователя
    user = await user_service.create_user(**test_user_data)
    
    assert isinstance(user.id, UUID)
    assert user.telegram_id == test_user_data["telegram_id"]
    assert user.username == test_user_data["username"]
    assert user.first_name == test_user_data["first_name"]
    assert user.last_name == test_user_data["last_name"]
    assert user.language_code == test_user_data["language_code"]
    assert user.user_data == test_user_data["user_data"]
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)

@pytest.mark.asyncio
async def test_get_user(user_service, test_user_data):
    """Тест получения пользователя."""
    # Создаем пользователя
    user = await user_service.create_user(**test_user_data)
    
    # Получаем пользователя по ID
    retrieved_user = await user_service.get_user(user.id)
    assert retrieved_user.id == user.id
    assert retrieved_user.telegram_id == test_user_data["telegram_id"]
    assert retrieved_user.username == test_user_data["username"]
    assert retrieved_user.first_name == test_user_data["first_name"]
    assert retrieved_user.last_name == test_user_data["last_name"]
    assert retrieved_user.language_code == test_user_data["language_code"]
    assert retrieved_user.user_data == test_user_data["user_data"]
    
    # Получаем пользователя по telegram_id
    retrieved_user_by_telegram = await user_service.get_user_by_telegram_id(test_user_data["telegram_id"])
    assert retrieved_user_by_telegram.id == user.id
    assert retrieved_user_by_telegram.telegram_id == test_user_data["telegram_id"]
    assert retrieved_user_by_telegram.username == test_user_data["username"]
    assert retrieved_user_by_telegram.first_name == test_user_data["first_name"]
    assert retrieved_user_by_telegram.last_name == test_user_data["last_name"]
    assert retrieved_user_by_telegram.language_code == test_user_data["language_code"]
    assert retrieved_user_by_telegram.user_data == test_user_data["user_data"]

@pytest.mark.asyncio
async def test_update_user(user_service, test_user_data):
    """Тест обновления пользователя."""
    # Создаем пользователя
    user = await user_service.create_user(**test_user_data)
    
    # Обновляем пользователя
    updated_data = {
        "username": "updated_user",
        "first_name": "Updated",
        "last_name": "User",
        "language_code": "en",
        "user_data": {
            "key3": "value3",
            "key4": "value4"
        }
    }
    
    updated_user = await user_service.update_user(
        user.id,
        **updated_data
    )
    
    assert updated_user.id == user.id
    assert updated_user.telegram_id == test_user_data["telegram_id"]
    assert updated_user.username == updated_data["username"]
    assert updated_user.first_name == updated_data["first_name"]
    assert updated_user.last_name == updated_data["last_name"]
    assert updated_user.language_code == updated_data["language_code"]
    assert updated_user.user_data == updated_data["user_data"]
    assert updated_user.updated_at > user.updated_at

@pytest.mark.asyncio
async def test_delete_user(user_service, test_user_data):
    """Тест удаления пользователя."""
    # Создаем пользователя
    user = await user_service.create_user(**test_user_data)
    
    # Удаляем пользователя
    await user_service.delete_user(user.id)
    
    # Проверяем, что пользователь удален
    retrieved_user = await user_service.get_user(user.id)
    assert retrieved_user is None

@pytest.mark.asyncio
async def test_get_users_by_language(user_service, test_user_data):
    """Тест получения пользователей по языку."""
    # Создаем пользователей с разными языками
    user1 = await user_service.create_user(**test_user_data)
    user2 = await user_service.create_user(
        **{**test_user_data, "telegram_id": 987654321, "language_code": "en"}
    )
    
    # Получаем пользователей по языку
    ru_users = await user_service.get_users_by_language("ru")
    assert len(ru_users) == 1
    assert ru_users[0].language_code == "ru"
    
    en_users = await user_service.get_users_by_language("en")
    assert len(en_users) == 1
    assert en_users[0].language_code == "en"

@pytest.mark.asyncio
async def test_get_users_by_username(user_service, test_user_data):
    """Тест получения пользователей по имени пользователя."""
    # Создаем пользователей с разными именами
    user1 = await user_service.create_user(**test_user_data)
    user2 = await user_service.create_user(
        **{**test_user_data, "telegram_id": 987654321, "username": "test_user2"}
    )
    
    # Получаем пользователей по имени
    users_with_test = await user_service.get_users_by_username("test_user")
    assert len(users_with_test) == 1
    assert users_with_test[0].username == "test_user"
    
    users_with_test2 = await user_service.get_users_by_username("test_user2")
    assert len(users_with_test2) == 1
    assert users_with_test2[0].username == "test_user2"

@pytest.mark.asyncio
async def test_get_users_by_data(user_service, test_user_data):
    """Тест получения пользователей по данным."""
    # Создаем пользователей с разными данными
    user1 = await user_service.create_user(**test_user_data)
    user2 = await user_service.create_user(
        **{**test_user_data, "telegram_id": 987654321, "user_data": {"key3": "value3"}}
    )
    
    # Получаем пользователей по данным
    users_with_key1 = await user_service.get_users_by_data("key1", "value1")
    assert len(users_with_key1) == 1
    assert users_with_key1[0].user_data["key1"] == "value1"
    
    users_with_key3 = await user_service.get_users_by_data("key3", "value3")
    assert len(users_with_key3) == 1
    assert users_with_key3[0].user_data["key3"] == "value3" 