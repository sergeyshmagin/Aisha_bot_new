"""
Асинхронный кэш транскриптов пользователей через Redis.
"""
from typing import Optional, Dict
from frontend_bot.shared.redis_client import redis_client
from frontend_bot.config import CACHE_TTL

_PREFIX = "transcript:"
_TTL = CACHE_TTL

async def get(user_id: int) -> Optional[str]:
    key = f"{_PREFIX}{user_id}"
    return await redis_client.get(key)

async def set(user_id: int, path: str) -> None:
    key = f"{_PREFIX}{user_id}"
    await redis_client.set(key, path, expire=_TTL)

async def remove(user_id: int) -> None:
    key = f"{_PREFIX}{user_id}"
    await redis_client.delete(key)

async def clear() -> None:
    await redis_client.delete_pattern(f"{_PREFIX}*")

async def all() -> Dict[int, str]:
    keys = await redis_client._client.keys(f"{_PREFIX}*")
    result = {}
    for key in keys:
        value = await redis_client.get(key)
        if value is not None:
            user_id = int(key.replace(_PREFIX, ""))
            result[user_id] = value
    return result 