import os
import json
from datetime import datetime
from typing import List, Dict, Any
from frontend_bot.utils.logger import get_logger

logger = get_logger('history')

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
HISTORY_FILE = os.path.join(STORAGE_DIR, 'history.json')


def load_history() -> Dict[str, List[Dict[str, Any]]]:
    """Загрузить историю обработок из файла."""
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_history(history: Dict[str, List[Dict[str, Any]]]) -> None:
    """Сохранить историю обработок в файл."""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_history_entry(
    user_id: str, file: str, file_type: str, result_type: str
) -> None:
    """Добавить запись в историю пользователя."""
    history = load_history()
    entry = {
        'file': os.path.basename(file),
        'type': file_type,
        'result': result_type,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    if user_id not in history:
        history[user_id] = []
    history[user_id].append(entry)
    save_history(history)
    logger.info(f"History entry added for user {user_id}: {entry}")


def get_user_history(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Получить последние записи истории пользователя."""
    history = load_history()
    return history.get(user_id, [])[-limit:]


def remove_last_history_entry(user_id: str) -> None:
    """Удалить последнюю запись из истории пользователя."""
    history = load_history()
    if user_id in history and history[user_id]:
        history[user_id].pop()
        save_history(history)
        logger.info(f"Last history entry removed for user {user_id}") 