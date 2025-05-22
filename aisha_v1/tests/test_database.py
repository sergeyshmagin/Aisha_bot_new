"""
Тесты для работы с базой данных.
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database.config import AsyncSessionLocal, Base
from database.models import User

@pytest.fixture(scope="session")
def event_loop():
    """Создаем event loop для тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Создаем тестовую базу данных."""
    async with AsyncSessionLocal() as session:
        await session.run_sync(Base.metadata.create_all)
        yield session
        await session.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_user(test_db: AsyncSession):
    """Тест создания пользователя."""
    user = User(
        telegram_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    assert user.id is not None
    assert user.telegram_id == 123456789
    assert user.username == "test_user"

@pytest.mark.asyncio
async def test_create_message(test_db: AsyncSession):
    """Тест создания сообщения."""
    user = User(
        telegram_id=987654321,
        username="message_user",
        first_name="Message",
        last_name="User"
    )
    test_db.add(user)
    await test_db.commit()
    
    message = Message(
        user_id=user.id,
        text="Test message",
        message_type="text"
    )
    test_db.add(message)
    await test_db.commit()
    await test_db.refresh(message)
    
    assert message.id is not None
    assert message.user_id == user.id
    assert message.text == "Test message"
    assert message.message_type == "text" 