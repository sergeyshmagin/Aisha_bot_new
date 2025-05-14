import os
import json
from datetime import datetime
from typing import List, Dict, Any
from frontend_bot.utils.logger import get_logger
import aiofiles
from frontend_bot.services.file_utils import async_exists

logger = get_logger("history")

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
HISTORY_FILE = os.path.join(STORAGE_DIR, "history.json")


def _ensure_storage_dir():
    os.makedirs(STORAGE_DIR, exist_ok=True)


async def load_history() -> Dict[str, List[Dict[str, Any]]]:
    """Загрузить историю обработок из файла."""
    if not await async_exists(HISTORY_FILE):
        return {}
    try:
        async with aiofiles.open(HISTORY_FILE, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)
    except Exception:
        return {}


async def save_history(history: Dict[str, List[Dict[str, Any]]]) -> None:
    """Сохранить историю обработок в файл."""
    _ensure_storage_dir()
    try:
        async with aiofiles.open(HISTORY_FILE, "w", encoding="utf-8") as f:
            await f.write(json.dumps(history, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.error(f"Не удалось сохранить history.json: {e}")


async def add_history_entry(
    user_id: str, file: str, file_type: str, result_type: str
) -> None:
    """Добавить запись в историю пользователя."""
    history = await load_history()
    entry = {
        "file": os.path.basename(file),
        "type": file_type,
        "result": result_type,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    if user_id not in history:
        history[user_id] = []
    history[user_id].append(entry)
    await save_history(history)
    logger.info(f"History entry added for user {user_id}: {entry}")


async def get_user_history(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Получить последние записи истории пользователя."""
    history = await load_history()
    return history.get(user_id, [])[-limit:]


async def remove_last_history_entry(user_id: str) -> None:
    """Удалить последнюю запись из истории пользователя."""
    history = await load_history()
    if user_id in history and history[user_id]:
        history[user_id].pop()
        await save_history(history)
        logger.info(f"Last history entry removed for user {user_id}")
