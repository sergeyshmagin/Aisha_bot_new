"""
Тесты для моделей базы данных.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from tests.utils import create_test_user

@pytest.mark.asyncio
async def test_create_user(test_db: AsyncSession):
    """Тест создания пользователя."""
    # Создаем тестового пользователя
    user_data = create_test_user(
        telegram_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    user = User(**user_data)
    
    # Добавляем пользователя в базу данных
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    # Проверяем, что пользователь создан
    assert user.id is not None
    assert user.telegram_id == user_data["telegram_id"]
    assert user.username == user_data["username"]
    assert user.first_name == user_data["first_name"]
    assert user.last_name == user_data["last_name"]

@pytest.mark.asyncio
async def test_create_message(test_db: AsyncSession):
    """Тест создания сообщения."""
    # Создаем тестового пользователя
    user_data = create_test_user(
        telegram_id=987654321,
        username="message_user",
        first_name="Message",
        last_name="User"
    )
    user = User(**user_data)
    test_db.add(user)
    await test_db.commit()
    
    # Создаем тестовое сообщение
    message_data = create_test_message(
        user_id=user.id,
        text="Test message",
        message_type="text"
    )
    message = Message(**message_data)
    
    # Добавляем сообщение в базу данных
    test_db.add(message)
    await test_db.commit()
    await test_db.refresh(message)
    
    # Проверяем, что сообщение создано
    assert message.id is not None
    assert message.user_id == user.id
    assert message.text == message_data["text"]
    assert message.message_type == message_data["message_type"]
    
    # Проверяем связь с пользователем
    assert message.user == user
    assert message in user.messages 