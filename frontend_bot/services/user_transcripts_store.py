import aiofiles
import asyncio
import json
from typing import Dict, Optional

_STORE_PATH = "storage/user_transcripts.json"
_LOCK = asyncio.Lock()
_cache: Dict[str, str] = {}


async def _load():
    global _cache
    try:
        async with aiofiles.open(_STORE_PATH, "r", encoding="utf-8") as f:
            data = await f.read()
            _cache = json.loads(data)
    except FileNotFoundError:
        _cache = {}


async def _save():
    async with _LOCK:
        async with aiofiles.open(_STORE_PATH, "w", encoding="utf-8") as f:
            await f.write(json.dumps(_cache))


async def get(user_id: int) -> Optional[str]:
    if not _cache:
        await _load()
    return _cache.get(str(user_id))


async def set(user_id: int, path: str):
    if not _cache:
        await _load()
    _cache[str(user_id)] = path
    await _save()


async def remove(user_id: int):
    if not _cache:
        await _load()
    _cache.pop(str(user_id), None)
    await _save()


async def clear():
    global _cache
    _cache = {}
    await _save()


async def all() -> Dict[int, str]:
    if not _cache:
        await _load()
    return {int(k): v for k, v in _cache.items()}
