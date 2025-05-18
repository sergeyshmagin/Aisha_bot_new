"""
Тесты для сервиса состояний.
"""

import pytest
from datetime import datetime
from uuid import UUID

from frontend_bot.services.state_service import StateService
from database.models import UserState

@pytest.fixture
def state_service(session):
    """Создает экземпляр сервиса состояний."""
    return StateService(session)

@pytest.fixture
def test_state_data():
    """Создает тестовые данные состояния."""
    return {
        "state_name": "test_state",
        "state_type": "test_type",
        "state_data": {
            "key1": "value1",
            "key2": "value2"
        }
    }

@pytest.mark.asyncio
async def test_create_state(state_service, test_user_data, test_state_data):
    """Тест создания состояния."""
    # Создаем пользователя
    user = await state_service.create_user(**test_user_data)
    assert user.id == test_user_data["id"]
    
    # Создаем состояние
    state = await state_service.create_state(
        user_id=user.id,
        **test_state_data
    )
    
    assert isinstance(state.id, UUID)
    assert state.user_id == user.id
    assert state.state_name == test_state_data["state_name"]
    assert state.state_type == test_state_data["state_type"]
    assert state.state_data == test_state_data["state_data"]
    assert isinstance(state.created_at, datetime)
    assert isinstance(state.updated_at, datetime)

@pytest.mark.asyncio
async def test_get_state(state_service, test_user_data, test_state_data):
    """Тест получения состояния."""
    # Создаем пользователя
    user = await state_service.create_user(**test_user_data)
    
    # Создаем состояние
    state = await state_service.create_state(
        user_id=user.id,
        **test_state_data
    )
    
    # Получаем состояние
    retrieved_state = await state_service.get_state(state.id)
    assert retrieved_state.id == state.id
    assert retrieved_state.user_id == user.id
    assert retrieved_state.state_name == test_state_data["state_name"]
    assert retrieved_state.state_type == test_state_data["state_type"]
    assert retrieved_state.state_data == test_state_data["state_data"]

@pytest.mark.asyncio
async def test_get_user_states(state_service, test_user_data, test_state_data):
    """Тест получения состояний пользователя."""
    # Создаем пользователя
    user = await state_service.create_user(**test_user_data)
    
    # Создаем состояния
    state1 = await state_service.create_state(
        user_id=user.id,
        **test_state_data
    )
    state2 = await state_service.create_state(
        user_id=user.id,
        **{**test_state_data, "state_name": "test_state2"}
    )
    
    # Получаем состояния пользователя
    user_states = await state_service.get_user_states(user.id)
    assert len(user_states) == 2
    assert all(isinstance(s.id, UUID) for s in user_states)
    assert all(s.user_id == user.id for s in user_states)
    assert {s.state_name for s in user_states} == {"test_state", "test_state2"}

@pytest.mark.asyncio
async def test_get_states_by_type(state_service, test_user_data, test_state_data):
    """Тест получения состояний по типу."""
    # Создаем пользователя
    user = await state_service.create_user(**test_user_data)
    
    # Создаем состояния разных типов
    await state_service.create_state(
        user_id=user.id,
        **test_state_data
    )
    await state_service.create_state(
        user_id=user.id,
        **{**test_state_data, "state_name": "test_state2", "state_type": "test_type2"}
    )
    
    # Получаем состояния по типу
    type1_states = await state_service.get_states_by_type("test_type")
    assert len(type1_states) == 1
    assert type1_states[0].state_type == "test_type"
    
    type2_states = await state_service.get_states_by_type("test_type2")
    assert len(type2_states) == 1
    assert type2_states[0].state_type == "test_type2"

@pytest.mark.asyncio
async def test_get_states_by_data(state_service, test_user_data, test_state_data):
    """Тест получения состояний по данным."""
    # Создаем пользователя
    user = await state_service.create_user(**test_user_data)
    
    # Создаем состояния с разными данными
    await state_service.create_state(
        user_id=user.id,
        **test_state_data
    )
    await state_service.create_state(
        user_id=user.id,
        **{**test_state_data, "state_name": "test_state2", "state_data": {"key3": "value3"}}
    )
    
    # Получаем состояния по данным
    states_with_key1 = await state_service.get_states_by_data("key1", "value1")
    assert len(states_with_key1) == 1
    assert states_with_key1[0].state_data["key1"] == "value1"
    
    states_with_key3 = await state_service.get_states_by_data("key3", "value3")
    assert len(states_with_key3) == 1
    assert states_with_key3[0].state_data["key3"] == "value3"

@pytest.mark.asyncio
async def test_update_state(state_service, test_user_data, test_state_data):
    """Тест обновления состояния."""
    # Создаем пользователя
    user = await state_service.create_user(**test_user_data)
    
    # Создаем состояние
    state = await state_service.create_state(
        user_id=user.id,
        **test_state_data
    )
    
    # Обновляем состояние
    updated_data = {
        "state_name": "updated_state",
        "state_type": "updated_type",
        "state_data": {
            "key3": "value3",
            "key4": "value4"
        }
    }
    
    updated_state = await state_service.update_state(
        state.id,
        **updated_data
    )
    
    assert updated_state.id == state.id
    assert updated_state.user_id == user.id
    assert updated_state.state_name == updated_data["state_name"]
    assert updated_state.state_type == updated_data["state_type"]
    assert updated_state.state_data == updated_data["state_data"]
    assert updated_state.updated_at > state.updated_at

@pytest.mark.asyncio
async def test_delete_state(state_service, test_user_data, test_state_data):
    """Тест удаления состояния."""
    # Создаем пользователя
    user = await state_service.create_user(**test_user_data)
    
    # Создаем состояние
    state = await state_service.create_state(
        user_id=user.id,
        **test_state_data
    )
    
    # Удаляем состояние
    await state_service.delete_state(state.id)
    
    # Проверяем, что состояние удалено
    retrieved_state = await state_service.get_state(state.id)
    assert retrieved_state is None

@pytest.mark.asyncio
async def test_delete_user_state(state_service, test_user_data, test_state_data):
    """Тест удаления состояния пользователя."""
    # Создаем пользователя
    user = await state_service.create_user(**test_user_data)
    
    # Создаем состояние
    await state_service.create_state(
        user_id=user.id,
        state_data=test_state_data["state_data"]
    )
    
    # Удаляем состояние пользователя
    await state_service.delete_user_state(user.id)
    
    # Проверяем, что состояние удалено
    user_state = await state_service.get_user_state(user.id)
    assert user_state is None

@pytest.mark.asyncio
async def test_get_states_by_state(state_service, test_user_data, test_state_data):
    """Тест получения состояний по значению."""
    # Создаем пользователей
    user1 = await state_service.create_user(**test_user_data)
    user2 = await state_service.create_user(**{**test_user_data, "id": UUID(int=2)})
    
    # Создаем состояния с разными значениями
    await state_service.create_state(
        user_id=user1.id,
        **test_state_data
    )
    await state_service.create_state(
        user_id=user2.id,
        **{**test_state_data, "state_name": "test_state2"}
    )
    
    # Получаем состояния по значению
    active_states = await state_service.get_states_by_state("test_state")
    assert len(active_states) == 1
    assert active_states[0].state_name == "test_state"
    
    inactive_states = await state_service.get_states_by_state("test_state2")
    assert len(inactive_states) == 1
    assert inactive_states[0].state_name == "test_state2"

@pytest.mark.asyncio
async def test_get_states_by_data(state_service, test_user_data, test_state_data):
    """Тест получения состояний по данным."""
    # Создаем пользователей
    user1 = await state_service.create_user(**test_user_data)
    user2 = await state_service.create_user(**{**test_user_data, "id": UUID(int=2)})
    
    # Создаем состояния с разными данными
    await state_service.create_state(
        user_id=user1.id,
        **test_state_data
    )
    await state_service.create_state(
        user_id=user2.id,
        **{**test_state_data, "state_name": "test_state2", "state_data": {"key3": "value3"}}
    )
    
    # Получаем состояния по данным
    states_with_key1 = await state_service.get_states_by_data("key1", "value1")
    assert len(states_with_key1) == 1
    assert states_with_key1[0].state_data["key1"] == "value1"
    
    states_with_key3 = await state_service.get_states_by_data("key3", "value3")
    assert len(states_with_key3) == 1
    assert states_with_key3[0].state_data["key3"] == "value3" 