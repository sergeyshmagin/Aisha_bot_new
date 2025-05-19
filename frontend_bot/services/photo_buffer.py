"""
Асинхронные функции для буферизации фото в Redis (устойчиво к race condition).
"""
import base64
import json
from frontend_bot.shared.redis_client import redis_client

REDIS_PHOTO_TTL = 300  # 5 минут

def get_photo_buffer_key(user_id):
    return f"photo_buffer:{user_id}"

async def buffer_photo_redis(user_id, photo_bytes, meta):
    key = get_photo_buffer_key(user_id)
    data = {
        "photo": base64.b64encode(photo_bytes).decode(),
        "meta": meta,
    }
    await redis_client.lpush(key, json.dumps(data).encode())
    await redis_client.expire(key, REDIS_PHOTO_TTL)

async def get_buffered_photos_redis(user_id):
    key = get_photo_buffer_key(user_id)
    photos = []
    while True:
        data = await redis_client.rpop(key)
        if not data:
            break
        obj = json.loads(data)
        obj["photo"] = base64.b64decode(obj["photo"])
        photos.append(obj)
    return photos

async def clear_photo_buffer_redis(user_id):
    key = get_photo_buffer_key(user_id)
    await redis_client.delete(key) 