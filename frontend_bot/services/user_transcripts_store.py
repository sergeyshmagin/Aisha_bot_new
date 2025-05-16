import aiofiles
import asyncio
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_STORE_PATH = "storage/user_transcripts.json"
_LOCK = asyncio.Lock()
_cache: Dict[str, str] = {}


async def _load():
    global _cache
    try:
        logger.info(f"[DEBUG] Loading transcripts from {_STORE_PATH}")
        async with aiofiles.open(_STORE_PATH, "r", encoding="utf-8") as f:
            data = await f.read()
            _cache = json.loads(data)
        logger.info(f"[DEBUG] Loaded {len(_cache)} transcripts")
    except FileNotFoundError:
        logger.info("[DEBUG] No transcripts file found, initializing empty cache")
        _cache = {}


async def _save():
    async with _LOCK:
        logger.info(f"[DEBUG] Saving {len(_cache)} transcripts to {_STORE_PATH}")
        async with aiofiles.open(_STORE_PATH, "w", encoding="utf-8") as f:
            await f.write(json.dumps(_cache))


async def get(user_id: int) -> Optional[str]:
    if not _cache:
        await _load()
    path = _cache.get(str(user_id))
    logger.info(f"[DEBUG] Getting transcript for user {user_id}: {path}")
    return path


async def set(user_id: int, path: str):
    if not _cache:
        await _load()
    logger.info(f"[DEBUG] Setting transcript for user {user_id}: {path}")
    _cache[str(user_id)] = path
    await _save()


async def remove(user_id: int):
    if not _cache:
        await _load()
    logger.info(f"[DEBUG] Removing transcript for user {user_id}")
    _cache.pop(str(user_id), None)
    await _save()


async def clear():
    global _cache
    logger.info("[DEBUG] Clearing all transcripts")
    _cache = {}
    await _save()


async def all() -> Dict[int, str]:
    if not _cache:
        await _load()
    return {int(k): v for k, v in _cache.items()}
