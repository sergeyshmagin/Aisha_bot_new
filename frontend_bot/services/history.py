"""
Сервис для работы с историей транскрипций.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import aiofiles
from frontend_bot.config import STORAGE_DIR, HISTORY_DIR
from frontend_bot.shared.file_operations import AsyncFileManager

logger = logging.getLogger(__name__)

async def ensure_history_dirs(storage_dir: Path) -> None:
    """Создает директорию истории для указанного storage_dir."""
    history_dir = storage_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

async def get_history_file_path(user_id: str, storage_dir: Path = STORAGE_DIR) -> Path:
    """Получает путь к файлу истории пользователя."""
    history_dir = storage_dir / HISTORY_DIR
    return history_dir / f"{user_id}.json"

async def load_history(user_id: str, storage_dir: Path = STORAGE_DIR) -> List[Dict[str, Any]]:
    """Загружает историю пользователя."""
    await ensure_history_dirs(storage_dir)
    history_path = await get_history_file_path(user_id, storage_dir)
    
    if not await AsyncFileManager.exists(history_path):
        return []
    
    try:
        content = await AsyncFileManager.read_file(history_path)
        return json.loads(content)
    except Exception as e:
        logger.error(f"Error loading history: {e}")
        return []

async def save_history(user_id: str, history: List[Dict[str, Any]], storage_dir: Path = STORAGE_DIR) -> None:
    """Сохраняет историю пользователя."""
    await ensure_history_dirs(storage_dir)
    history_path = await get_history_file_path(user_id, storage_dir)
    
    try:
        content = json.dumps(history, ensure_ascii=False, indent=2)
        await AsyncFileManager.write_file(history_path, content)
    except Exception as e:
        logger.error(f"Error saving history: {e}")
        raise

async def add_history_entry(user_id: str, file_name: str, file_path: str, storage_dir: Path = STORAGE_DIR) -> None:
    """Добавляет запись в историю транскрипций."""
    history = await load_history(user_id, storage_dir)
    
    entry = {
        "file_name": file_name,
        "file_path": file_path,
        "created_at": datetime.utcnow().isoformat()
    }
    
    history.append(entry)
    await save_history(user_id, history, storage_dir)

async def get_user_history(user_id: str, storage_dir: Path = STORAGE_DIR) -> List[Dict[str, Any]]:
    """Получает историю пользователя."""
    return await load_history(user_id, storage_dir)

async def clear_user_history(user_id: str, storage_dir: Path = STORAGE_DIR) -> None:
    """Очищает историю пользователя."""
    history_path = await get_history_file_path(user_id, storage_dir)
    if await AsyncFileManager.exists(history_path):
        await AsyncFileManager.safe_remove(history_path)
