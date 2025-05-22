"""Тесты для state_utils.py."""

import pytest
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from frontend_bot.services.state_utils import (
    get_state_pg,
    set_state_pg,
    clear_state_pg,
    cleanup_state_pg,
    get_edit_mode,
    set_edit_mode,
    get_current_avatar_id,
    set_current_avatar_id,
    States,
    EditModes,
)

pytestmark = pytest.mark.asyncio

async def test_set_and_get_state(session: AsyncSession):
    """Тест установки и получения состояния."""
    user_id = uuid4()
    test_state = {"test": "data"}
    
    # Устанавливаем состояние
    await set_state_pg(user_id, test_state, session)
    
    # Получаем состояние
    state = await get_state_pg(user_id, session)
    assert state == test_state

async def test_set_and_get_string_state(session: AsyncSession):
    """Тест установки и получения строкового состояния."""
    user_id = uuid4()
    test_state = "test_state"
    
    # Устанавливаем состояние
    await set_state_pg(user_id, test_state, session)
    
    # Получаем состояние
    state = await get_state_pg(user_id, session)
    assert state == {"state": test_state}

async def test_clear_state(session: AsyncSession):
    """Тест очистки состояния."""
    user_id = uuid4()
    test_state = {"test": "data"}
    
    # Устанавливаем состояние
    await set_state_pg(user_id, test_state, session)
    
    # Очищаем состояние
    await clear_state_pg(user_id, session)
    
    # Проверяем, что состояние очищено
    state = await get_state_pg(user_id, session)
    assert state is None

async def test_cleanup_state(session: AsyncSession):
    """Тест полной очистки данных пользователя."""
    user_id = uuid4()
    test_state = {"test": "data"}
    
    # Устанавливаем состояние
    await set_state_pg(user_id, test_state, session)
    
    # Очищаем все данные
    await cleanup_state_pg(user_id, session)
    
    # Проверяем, что данные очищены
    state = await get_state_pg(user_id, session)
    assert state is None

async def test_edit_mode(session: AsyncSession):
    """Тест работы с режимом редактирования."""
    user_id = uuid4()
    
    # Проверяем начальное состояние
    mode = await get_edit_mode(user_id, session)
    assert mode is None
    
    # Устанавливаем режим
    await set_edit_mode(user_id, EditModes.CREATE, session)
    mode = await get_edit_mode(user_id, session)
    assert mode == EditModes.CREATE
    
    # Меняем режим
    await set_edit_mode(user_id, EditModes.EDIT, session)
    mode = await get_edit_mode(user_id, session)
    assert mode == EditModes.EDIT

async def test_current_avatar_id(session: AsyncSession):
    """Тест работы с ID текущего аватара."""
    user_id = uuid4()
    avatar_id = "test_avatar_123"
    
    # Проверяем начальное состояние
    current_id = await get_current_avatar_id(user_id, session)
    assert current_id is None
    
    # Устанавливаем ID
    await set_current_avatar_id(user_id, avatar_id, session)
    current_id = await get_current_avatar_id(user_id, session)
    assert current_id == avatar_id

async def test_state_persistence(session: AsyncSession):
    """Тест сохранения состояния между сессиями."""
    user_id = uuid4()
    test_state = {"test": "data"}
    
    # Устанавливаем состояние
    await set_state_pg(user_id, test_state, session)
    
    # Получаем состояние в новой сессии
    new_session = AsyncSession(session.get_bind())
    state = await get_state_pg(user_id, new_session)
    
    assert state == test_state
    await new_session.close() 