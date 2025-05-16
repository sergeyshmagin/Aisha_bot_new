"""
Тесты для RedisStateManager.
"""

import pytest
import asyncio
from frontend_bot.services.redis_state_manager import RedisStateManager
from frontend_bot.shared import redis_client

@pytest.fixture(autouse=True)
async def cleanup_redis():
    """Очищает Redis до и после каждого теста."""
    await redis_client.init()
    await redis_client.delete_pattern("state:*")
    yield
    await redis_client.delete_pattern("state:*")
    await redis_client.close()

@pytest.fixture
def state_manager():
    """Фикстура для RedisStateManager."""
    return RedisStateManager()

@pytest.mark.asyncio
async def test_set_and_get_state(state_manager):
    """Проверяет установку и получение состояния."""
    user_id = "123"
    state = {"status": "test", "data": {"key": "value"}}
    
    await state_manager.set_state(user_id, state)
    result = await state_manager.get_state(user_id)
    
    assert result == state

@pytest.mark.asyncio
async def test_clear_state(state_manager):
    """Проверяет очистку состояния."""
    user_id = "123"
    state = {"status": "test"}
    
    await state_manager.set_state(user_id, state)
    await state_manager.clear_state(user_id)
    result = await state_manager.get_state(user_id)
    
    assert result is None

@pytest.mark.asyncio
async def test_cleanup_state(state_manager):
    """Проверяет очистку всех данных пользователя."""
    user_id = "123"
    state = {"status": "test"}
    
    await state_manager.set_state(user_id, state)
    await state_manager.cleanup_state(user_id)
    result = await state_manager.get_state(user_id)
    
    assert result is None

@pytest.mark.asyncio
async def test_state_expiration(state_manager):
    """Проверяет истечение срока действия состояния."""
    user_id = "123"
    state = {"status": "test"}
    
    # Устанавливаем состояние с TTL = 1 секунда
    await state_manager._redis.set_json(
        state_manager._get_key(user_id),
        state,
        expire=1
    )
    
    # Проверяем, что состояние доступно
    result = await state_manager.get_state(user_id)
    assert result == state
    
    # Ждем 2 секунды
    await asyncio.sleep(2)
    
    # Проверяем, что состояние истекло
    result = await state_manager.get_state(user_id)
    assert result is None

@pytest.mark.asyncio
async def test_get_state_empty(state_manager):
    """Тест получения состояния для нового пользователя."""
    state = await state_manager.get_state("123")
    assert state is None

@pytest.mark.asyncio
async def test_multiple_users(state_manager):
    """Тест работы с несколькими пользователями."""
    states = {
        "123": {"key": "value1"},
        "456": {"key": "value2"},
        "789": {"key": "value3"}
    }
    
    # Устанавливаем состояния для всех пользователей
    for user_id, state in states.items():
        await state_manager.set_state(user_id, state)
    
    # Проверяем состояния
    for user_id, expected_state in states.items():
        state = await state_manager.get_state(user_id)
        assert state == expected_state

@pytest.mark.asyncio
async def test_state_persistence(state_manager):
    """Тест сохранения состояния между перезапусками."""
    user_id = "123"
    test_state = {"key": "value"}
    
    # Устанавливаем состояние
    await state_manager.set_state(user_id, test_state)
    
    # Создаем новый экземпляр RedisStateManager
    new_manager = RedisStateManager()
    
    # Проверяем, что состояние сохранилось
    state = await new_manager.get_state(user_id)
    assert state == test_state

@pytest.mark.asyncio
async def test_invalid_state(state_manager):
    """Тест обработки некорректных данных."""
    user_id = "123"
    
    # Попытка установить некорректное состояние
    with pytest.raises(Exception):
        await state_manager.set_state(user_id, {"key": object()})  # object() не сериализуется в JSON

@pytest.mark.asyncio
async def test_concurrent_state_updates(state_manager):
    """Тест конкурентного обновления состояний."""
    async def update_state(user_id, value):
        state = await state_manager.get_state(user_id) or {}
        state["value"] = value
        await state_manager.set_state(user_id, state)
    
    # Обновляем состояние одного пользователя конкурентно
    user_id = "123"
    tasks = [update_state(user_id, i) for i in range(5)]
    await asyncio.gather(*tasks)
    
    # Проверяем, что последнее значение сохранилось
    state = await state_manager.get_state(user_id)
    assert state["value"] == 4  # Последнее значение из range(5) 