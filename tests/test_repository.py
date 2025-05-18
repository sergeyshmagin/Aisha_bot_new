"""
Тесты для репозитория базы данных.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from frontend_bot.repositories.user_repository import UserRepository
from tests.utils import create_test_user, create_test_message

@pytest.mark.asyncio
async def test_user_repository(test_db: AsyncSession):
    """Тест репозитория пользователей."""
    # Создаем репозиторий
    user_repo = UserRepository(test_db)
    
    # Создаем тестового пользователя
    user_data = create_test_user(
        telegram_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    
    # Добавляем пользователя
    user = await user_repo.create(**user_data)
    assert user.id is not None
    assert user.telegram_id == user_data["telegram_id"]
    
    # Получаем пользователя по telegram_id
    found_user = await user_repo.get_by_telegram_id(user_data["telegram_id"])
    assert found_user is not None
    assert found_user.id == user.id
    
    # Обновляем пользователя
    updated_data = {"username": "updated_user"}
    updated_user = await user_repo.update(user.id, **updated_data)
    assert updated_user.username == updated_data["username"]
    
    # Удаляем пользователя
    await user_repo.delete(user.id)
    deleted_user = await user_repo.get_by_telegram_id(user_data["telegram_id"])
    assert deleted_user is None

@pytest.mark.asyncio
async def test_message_repository(test_db: AsyncSession):
    """Тест репозитория сообщений."""
    # Создаем репозитории
    user_repo = UserRepository(test_db)
    message_repo = MessageRepository(test_db)
    
    # Создаем тестового пользователя
    user_data = create_test_user(
        telegram_id=987654321,
        username="message_user",
        first_name="Message",
        last_name="User"
    )
    user = await user_repo.create(**user_data)
    
    # Создаем тестовое сообщение
    message_data = create_test_message(
        user_id=user.id,
        text="Test message",
        message_type="text"
    )
    
    # Добавляем сообщение
    message = await message_repo.create(**message_data)
    assert message.id is not None
    assert message.user_id == user.id
    
    # Получаем сообщения пользователя
    user_messages = await message_repo.get_by_user_id(user.id)
    assert len(user_messages) == 1
    assert user_messages[0].id == message.id
    
    # Обновляем сообщение
    updated_data = {"text": "Updated message"}
    updated_message = await message_repo.update(message.id, **updated_data)
    assert updated_message.text == updated_data["text"]
    
    # Удаляем сообщение
    await message_repo.delete(message.id)
    deleted_message = await message_repo.get_by_id(message.id)
    assert deleted_message is None 