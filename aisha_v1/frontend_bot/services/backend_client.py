import aiohttp
import os
from frontend_bot.config import settings
import aiofiles
import io


async def send_photo_for_animation(photo_path: str, emotion: str) -> str:
    url = f"{settings.BACKEND_URL}/animate-photo"

    async with aiohttp.ClientSession() as session:
        async with aiofiles.open(photo_path, "rb") as f:
            photo_bytes = await f.read()
            form = aiohttp.FormData()
            form.add_field(
                "file",
                io.BytesIO(photo_bytes),
                filename="photo.jpg",
                content_type="image/jpeg",
            )
            form.add_field("emotion", emotion)

            async with session.post(url, data=form) as resp:
                if resp.status != 200:
                    raise Exception(f"Backend error: {resp.status}")
                data = await resp.json()
                return data["video_path"]


async def send_photo_for_enhancement(photo_path: str) -> str:
    url = f"{settings.BACKEND_URL}/gfpgan-enhance?auto=true"
    async with aiohttp.ClientSession() as session:
        async with aiofiles.open(photo_path, "rb") as f:
            photo_bytes = await f.read()
            form = aiohttp.FormData()
            form.add_field(
                "file",
                io.BytesIO(photo_bytes),
                filename="photo.jpg",
                content_type="image/jpeg",
            )
            async with session.post(url, data=form) as resp:
                if resp.status != 200:
                    raise Exception(f"Backend error: {resp.status}")
                ext = os.path.splitext(photo_path)[1].lower()
                if ext == ".png":
                    output_path = photo_path.replace(".png", "_enhanced.png")
                else:
                    output_path = photo_path.replace(".jpg", "_enhanced.jpg")
                async with aiofiles.open(output_path, "wb") as out:
                    await out.write(await resp.read())
                return output_path
