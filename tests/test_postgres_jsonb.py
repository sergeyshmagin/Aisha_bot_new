"""
Тесты для JSONB полей в PostgreSQL.
"""

import pytest
from frontend_bot.models.base import User, UserAvatar, UserState
from tests.conftest import generate_telegram_id
from sqlalchemy import text

@pytest.mark.asyncio
async def test_user_state_jsonb(test_session):
    """Тест работы с JSONB полем state_data в таблице user_states."""
    # Создаем пользователя
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user_state"
    )
    test_session.add(user)
    await test_session.flush()
    
    # Создаем состояние пользователя с JSONB данными
    state = UserState(
        user_id=user.id,
        state_data={
            "current_state": "main_menu",
            "last_action": "start",
            "context": {
                "selected_avatar": None,
                "pending_operation": None
            }
        }
    )
    test_session.add(state)
    await test_session.commit()
    
    # Проверяем запрос по JSONB полю
    result = await test_session.execute(
        text("""
        SELECT * FROM user_states 
        WHERE state_data->>'current_state' = 'main_menu'
        AND state_data->'context'->>'selected_avatar' IS NULL
        """),
        {}
    )
    found_state = result.first()
    assert found_state is not None
    assert found_state.user_id == user.id
    assert found_state.state_data["current_state"] == "main_menu"

@pytest.mark.asyncio
async def test_user_avatar_jsonb(test_session):
    """Тест работы с JSONB полем avatar_data в таблице user_avatars."""
    # Создаем пользователя
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user_avatar"
    )
    test_session.add(user)
    await test_session.flush()
    
    # Создаем аватар с JSONB данными
    avatar = UserAvatar(
        user_id=user.id,
        avatar_data={
            "name": "Test Avatar",
            "gender": "male",
            "image_path": "/path/to/avatar.jpg",
            "gen_params": {
                "style": "realistic",
                "age": 25,
                "hair_color": "brown"
            },
            "status": "ready"
        }
    )
    test_session.add(avatar)
    await test_session.commit()
    
    # Проверяем запрос по JSONB полю
    result = await test_session.execute(
        text("""
        SELECT * FROM user_avatars 
        WHERE avatar_data->>'status' = 'ready'
        AND avatar_data->'gen_params'->>'style' = 'realistic'
        """),
        {}
    )
    found_avatar = result.first()
    assert found_avatar is not None
    assert found_avatar.user_id == user.id
    assert found_avatar.avatar_data["name"] == "Test Avatar"

@pytest.mark.asyncio
async def test_jsonb_array_operations(test_session):
    """Тест операций с JSONB массивами."""
    # Создаем пользователя
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user_array"
    )
    test_session.add(user)
    await test_session.flush()
    
    # Создаем состояние с JSONB массивом
    state = UserState(
        user_id=user.id,
        state_data={
            "actions": ["start", "select_avatar", "generate"],
            "permissions": ["basic", "premium"],
            "history": [
                {"action": "start", "timestamp": "2024-01-01T12:00:00"},
                {"action": "select_avatar", "timestamp": "2024-01-01T12:01:00"}
            ]
        }
    )
    test_session.add(state)
    await test_session.commit()
    
    # Проверяем запрос по элементам JSONB массива
    result = await test_session.execute(
        text("""
        SELECT * FROM user_states 
        WHERE state_data->'actions' ? 'select_avatar'
        AND state_data->'permissions' ? 'premium'
        AND state_data->'history' @> '[{"action": "start"}]'
        """),
        {}
    )
    found_state = result.first()
    assert found_state is not None
    assert found_state.user_id == user.id
    assert "select_avatar" in found_state.state_data["actions"]
    assert "premium" in found_state.state_data["permissions"]

@pytest.mark.asyncio
async def test_jsonb_update_operations(test_session):
    """Тест операций обновления JSONB полей."""
    # Создаем пользователя
    user = User(
        telegram_id=generate_telegram_id(),
        username="test_user_update"
    )
    test_session.add(user)
    await test_session.flush()
    
    # Создаем начальное состояние
    state = UserState(
        user_id=user.id,
        state_data={
            "current_state": "main_menu",
            "context": {}
        }
    )
    test_session.add(state)
    await test_session.commit()
    
    # Обновляем JSONB поле
    await test_session.execute(
        text("""
        UPDATE user_states 
        SET state_data = jsonb_set(
            jsonb_set(
                state_data,
                '{context,selected_avatar}',
                '"avatar_123"'
            ),
            '{last_action}',
            '"select_avatar"'
        )
        WHERE user_id = :user_id
        """),
        {"user_id": user.id}
    )
    await test_session.commit()
    
    # Проверяем обновленные данные
    result = await test_session.execute(
        text("""
        SELECT * FROM user_states 
        WHERE user_id = :user_id
        """),
        {"user_id": user.id}
    )
    updated_state = result.first()
    assert updated_state is not None
    assert updated_state.state_data["current_state"] == "main_menu"
    assert updated_state.state_data["context"]["selected_avatar"] == "avatar_123"
    assert updated_state.state_data["last_action"] == "select_avatar" 