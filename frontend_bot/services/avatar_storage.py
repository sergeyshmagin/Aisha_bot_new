"""Сервис для хранения аватаров пользователя в JSON-файле."""

import json
import os
import asyncio
import aiofiles
from frontend_bot.services.file_utils import async_exists


AVATAR_PATH = os.path.join(os.path.dirname(__file__), "avatars.json")


_storage_lock = asyncio.Lock()


# Загружаем все аватары из файла
async def load_avatars():
    if not await async_exists(AVATAR_PATH):
        return {}
    async with _storage_lock:
        async with aiofiles.open(AVATAR_PATH, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)


# Сохраняем все аватары в файл
async def save_avatars(data):
    async with _storage_lock:
        async with aiofiles.open(AVATAR_PATH, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))


# Получить список аватаров пользователя
async def get_user_avatars(user_id):
    data = await load_avatars()
    return data.get(str(user_id), [])


# Установить список аватаров пользователя
async def set_user_avatars(user_id, avatars):
    data = await load_avatars()
    data[str(user_id)] = avatars
    await save_avatars(data)
