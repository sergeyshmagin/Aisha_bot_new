import aiohttp
import os
from frontend_bot.config import BACKEND_URL

async def send_photo_for_animation(photo_path: str, emotion: str) -> str:
    url = f"{BACKEND_URL}/animate-photo"

    async with aiohttp.ClientSession() as session:
        with open(photo_path, "rb") as f:
            form = aiohttp.FormData()
            form.add_field("file", f, filename="photo.jpg", content_type="image/jpeg")
            form.add_field("emotion", emotion)

            async with session.post(url, data=form) as resp:
                if resp.status != 200:
                    raise Exception(f"Backend error: {resp.status}")
                data = await resp.json()
                return data["video_path"]
