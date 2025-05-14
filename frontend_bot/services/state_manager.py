"""
Модуль для управления состояниями пользователя (user_states).
В будущем можно заменить реализацию на Redis.
"""

import os
import json
import logging
from typing import Optional
import aiofiles
from frontend_bot.services.file_utils import async_exists

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
STATE_FILE = os.path.join(STORAGE_DIR, "state.json")

logger = logging.getLogger("state_manager")
logging.basicConfig(level=logging.INFO)

# Загружает состояния из файла


async def _load_states():
    if not await async_exists(STATE_FILE):
        return {}
    try:
        async with aiofiles.open(STATE_FILE, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)
    except Exception:
        return {}


# Сохраняет состояния в файл


async def _save_states(states):
    os.makedirs(STORAGE_DIR, exist_ok=True)
    try:
        async with aiofiles.open(STATE_FILE, "w", encoding="utf-8") as f:
            await f.write(json.dumps(states, ensure_ascii=False, indent=2))
        logger.info(f"[state_manager] Состояния сохранены: {states}")
    except Exception as e:
        logger.error(f"Не удалось сохранить state.json: {e}")


fsm_states = {}


async def set_state(user_id, state):
    fsm_states[user_id] = state
    states = await _load_states()
    states[str(user_id)] = state
    await _save_states(states)
    logger.info(f"[state_manager] set_state: user_id={user_id}, state={state}")


async def get_state(user_id):
    states = await _load_states()
    value = states.get(str(user_id))
    logger.info(f"[state_manager] get_state: user_id={user_id}, state={value}")
    return value


async def clear_state(user_id):
    fsm_states.pop(user_id, None)
    states = await _load_states()
    removed = states.pop(str(user_id), None)
    await _save_states(states)
    logger.info(f"[state_manager] clear_state: user_id={user_id}, removed={removed}")


# Хранилище текущего avatar_id для каждого пользователя
_current_avatar_ids = {}


def set_current_avatar_id(user_id: int, avatar_id: str) -> None:
    """Сохраняет текущий avatar_id для пользователя."""
    _current_avatar_ids[user_id] = avatar_id


def get_current_avatar_id(user_id: int) -> Optional[str]:
    """Возвращает текущий avatar_id для пользователя, если есть."""
    return _current_avatar_ids.get(user_id)
