"""
Асинхронные утилиты для работы с состоянием пользователя через PostgreSQL.

Состояния пользователя:
1. Основные состояния:
   - main_menu: Главное меню
   - avatar_create: Создание аватара
   - avatar_edit: Редактирование аватара
   - avatar_confirm: Подтверждение аватара
   - avatar_enter_name: Ввод имени аватара
   - transcribe_txt: Обработка текстового транскрипта
   - transcribe_audio: Обработка аудио транскрипта

2. Дополнительные данные:
   - edit_mode: Режим редактирования (create/edit)
   - current_avatar_id: ID текущего аватара
   - photos: Список фотографий
   - gender: Пол аватара
   - title: Название аватара
   - class_name: Класс аватара
   - finetune_id: ID обучения
   - finetune_status: Статус обучения

Использование:
    await get_state(user_id, session)
    await set_state(user_id, state, session)
    await clear_state(user_id, session)
    await cleanup_state(user_id, session)
"""

from typing import Dict, Any, Optional, Union, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from frontend_bot.repositories.state_repository import StateRepository
from frontend_bot.utils.logger import get_logger
import traceback

logger = get_logger(__name__)

# Типы состояний
StateType = Union[str, Dict[str, Any]]
StateData = Dict[str, Any]

# Константы состояний
class States:
    MAIN_MENU = "main_menu"
    AVATAR_CREATE = "avatar_create"
    AVATAR_EDIT = "avatar_edit"
    AVATAR_CONFIRM = "avatar_confirm"
    AVATAR_ENTER_NAME = "avatar_enter_name"
    TRANSCRIBE_TXT = "transcribe_txt"
    TRANSCRIBE_AUDIO = "transcribe_audio"

# Константы режимов
class EditModes:
    CREATE = "create"
    EDIT = "edit"

async def get_state_pg(user_id: UUID, session: AsyncSession) -> Optional[StateData]:
    """
    Получает состояние пользователя из PostgreSQL.
    
    Args:
        user_id: ID пользователя (UUID)
        session: асинхронная сессия SQLAlchemy
        
    Returns:
        Optional[StateData]: Состояние пользователя или None
        
    Raises:
        Exception: При ошибке получения состояния
    """
    try:
        repo = StateRepository(session)
        state = await repo.get_state(user_id)
        return state.state_data if state else None
    except Exception as e:
        logger.error(f"Ошибка при получении состояния пользователя {user_id}: {e}")
        raise

async def set_state_pg(user_id: UUID, state: StateType, session: AsyncSession) -> None:
    """
    Устанавливает состояние пользователя в PostgreSQL.
    
    Args:
        user_id: ID пользователя (UUID)
        state: Новое состояние (строка или словарь)
        session: асинхронная сессия SQLAlchemy
        
    Raises:
        Exception: При ошибке установки состояния
    """
    try:
        repo = StateRepository(session)
        state_data = {"state": state} if isinstance(state, str) else state
        await repo.set_state(user_id, state_data)
        # Логируем подробности
        logger.warning(f"[set_state_pg] user_id={user_id} state={state_data} (caller: {traceback.format_stack(limit=3)})")
    except Exception as e:
        logger.error(f"Ошибка при установке состояния пользователя {user_id}: {e}")
        raise

async def clear_state_pg(user_id: UUID, session: AsyncSession) -> None:
    """
    Очищает состояние пользователя в PostgreSQL.
    
    Args:
        user_id: ID пользователя (UUID)
        session: асинхронная сессия SQLAlchemy
        
    Raises:
        Exception: При ошибке очистки состояния
    """
    try:
        repo = StateRepository(session)
        await repo.clear_state(user_id)
        # Логируем подробности
        logger.warning(f"[clear_state_pg] user_id={user_id} (caller: {traceback.format_stack(limit=3)})")
    except Exception as e:
        logger.error(f"Ошибка при очистке состояния пользователя {user_id}: {e}")
        raise

async def cleanup_state_pg(user_id: UUID, session: AsyncSession) -> None:
    """
    Очищает все данные пользователя в PostgreSQL.
    
    Args:
        user_id: ID пользователя (UUID)
        session: асинхронная сессия SQLAlchemy
        
    Raises:
        Exception: При ошибке очистки данных
    """
    try:
        repo = StateRepository(session)
        await repo.clear_state(user_id)
        logger.debug(f"Очищены все данные пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при очистке данных пользователя {user_id}: {e}")
        raise

async def get_edit_mode(user_id: UUID, session: AsyncSession) -> Optional[str]:
    """
    Получает режим редактирования пользователя.
    
    Args:
        user_id: ID пользователя (UUID)
        session: асинхронная сессия SQLAlchemy
        
    Returns:
        Optional[str]: Режим редактирования или None
    """
    state = await get_state_pg(user_id, session)
    return state.get("edit_mode") if state else None

async def set_edit_mode(user_id: UUID, mode: str, session: AsyncSession) -> None:
    """
    Устанавливает режим редактирования пользователя.
    
    Args:
        user_id: ID пользователя (UUID)
        mode: Режим редактирования (create/edit)
        session: асинхронная сессия SQLAlchemy
    """
    state = await get_state_pg(user_id, session) or {}
    state["edit_mode"] = mode
    await set_state_pg(user_id, state, session)

async def get_current_avatar_id(user_id: UUID, session: AsyncSession) -> Optional[str]:
    """
    Получает ID текущего аватара пользователя.
    
    Args:
        user_id: ID пользователя (UUID)
        session: асинхронная сессия SQLAlchemy
        
    Returns:
        Optional[str]: ID аватара или None
    """
    state = await get_state_pg(user_id, session)
    return state.get("current_avatar_id") if state else None

async def set_current_avatar_id(user_id: UUID, avatar_id: str, session: AsyncSession) -> None:
    """
    Устанавливает ID текущего аватара пользователя.
    
    Args:
        user_id: ID пользователя (UUID)
        avatar_id: ID аватара
        session: асинхронная сессия SQLAlchemy
    """
    state = await get_state_pg(user_id, session) or {}
    state["current_avatar_id"] = avatar_id
    await set_state_pg(user_id, state, session)

# Алиасы для обратной совместимости
get_state = get_state_pg
set_state = set_state_pg
clear_state = clear_state_pg
cleanup_state = cleanup_state_pg

__all__ = [
    'get_state',
    'set_state',
    'clear_state',
    'cleanup_state',
    'get_state_pg',
    'set_state_pg',
    'clear_state_pg',
    'cleanup_state_pg',
    'get_edit_mode',
    'set_edit_mode',
    'get_current_avatar_id',
    'set_current_avatar_id',
    'States',
    'EditModes'
] 