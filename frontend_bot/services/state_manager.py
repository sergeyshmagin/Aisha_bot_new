"""
Модуль для управления состояниями пользователя (user_states).
В будущем можно заменить реализацию на Redis.
"""

import os
import json
import logging

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
STATE_FILE = os.path.join(STORAGE_DIR, "state.json")

logger = logging.getLogger("state_manager")
logging.basicConfig(level=logging.INFO)

# Загружает состояния из файла

def _load_states():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return {}

# Сохраняет состояния в файл

def _save_states(states):
    os.makedirs(STORAGE_DIR, exist_ok=True)
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(states, f, ensure_ascii=False, indent=2)
        logger.info(
            f"[state_manager] Состояния сохранены: {states}"
        )
    except Exception as e:
        logger.error(f"Не удалось сохранить state.json: {e}")


def set_state(user_id, state):
    states = _load_states()
    states[str(user_id)] = state
    _save_states(states)
    logger.info(
        f"[state_manager] set_state: user_id={user_id}, state={state}"
    )


def get_state(user_id):
    states = _load_states()
    value = states.get(str(user_id))
    logger.info(
        f"[state_manager] get_state: user_id={user_id}, state={value}"
    )
    return value


def clear_state(user_id):
    states = _load_states()
    removed = states.pop(str(user_id), None)
    _save_states(states)
    logger.info(
        f"[state_manager] clear_state: user_id={user_id}, removed={removed}"
    ) 