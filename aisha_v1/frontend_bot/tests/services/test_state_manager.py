"""
Тесты для менеджера состояний пользователей.
"""

import pytest
from pathlib import Path
from frontend_bot.services.state_manager import StateManager
from frontend_bot.shared.file_operations import AsyncFileManager

@pytest.fixture
async def temp_dir(tmp_path):
    """Создает временную директорию для тестов."""
    test_dir = tmp_path / "test_dir"
    await AsyncFileManager.ensure_dir(test_dir)
    yield test_dir
    await AsyncFileManager.safe_rmtree(test_dir)

@pytest.fixture
async def state_manager(temp_dir):
    """Создает экземпляр StateManager для тестов."""
    manager = StateManager(storage_dir=temp_dir)
    yield manager
    # Очищаем состояние после тестов
    await AsyncFileManager.safe_rmtree(temp_dir)

@pytest.mark.asyncio
async def test_get_state_empty(state_manager):
    """Тест получения состояния для нового пользователя."""
    state = await state_manager.get_state("123")
    assert state is None

@pytest.mark.asyncio
async def test_set_get_state(state_manager):
    """Тест установки и получения состояния."""
    user_id = "123"
    test_state = {"key": "value", "nested": {"data": 42}}
    
    # Устанавливаем состояние
    await state_manager.set_state(user_id, test_state)
    
    # Получаем состояние
    state = await state_manager.get_state(user_id)
    assert state == test_state

@pytest.mark.asyncio
async def test_clear_state(state_manager):
    """Тест очистки состояния."""
    user_id = "123"
    test_state = {"key": "value"}
    
    # Устанавливаем состояние
    await state_manager.set_state(user_id, test_state)
    
    # Очищаем состояние
    await state_manager.clear_state(user_id)
    
    # Проверяем, что состояние очищено
    state = await state_manager.get_state(user_id)
    assert state is None

@pytest.mark.asyncio
async def test_cleanup_state(state_manager):
    """Тест полной очистки данных пользователя."""
    user_id = "123"
    test_state = {"key": "value"}
    
    # Устанавливаем состояние
    await state_manager.set_state(user_id, test_state)
    
    # Очищаем все данные
    await state_manager.cleanup_state(user_id)
    
    # Проверяем, что состояние очищено
    state = await state_manager.get_state(user_id)
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
    
    # Создаем новый экземпляр StateManager
    new_manager = StateManager(storage_dir=state_manager.storage_dir)
    
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
    import asyncio
    
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