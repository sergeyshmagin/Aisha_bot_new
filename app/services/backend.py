"""
Сервис для работы с Backend API
"""
from typing import Dict, Optional

import aiohttp
from aiohttp import ClientTimeout

from app.core.config import settings
from app.services.base import BaseService
from app.shared.utils.backend import get_backend_headers


class BackendService(BaseService):
    """
    Сервис для работы с Backend API
    """

    def __init__(self, session: aiohttp.ClientSession, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.http = session
        self.timeout = ClientTimeout(total=settings.BACKEND_TIMEOUT)

    async def enhance_photo(self, photo_data: bytes) -> Optional[bytes]:
        """
        Улучшить фото через GFPGAN
        """
        url = f"{settings.BACKEND_API_URL}/enhance"
        headers = get_backend_headers(settings.BACKEND_API_KEY)
        
        try:
            async with self.http.post(
                url,
                data={"photo": photo_data},
                headers=headers,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    return await response.read()
                return None
        except aiohttp.ClientError:
            return None

    async def train_avatar(self, user_id: int, avatar_id: str, photos: list[bytes]) -> Optional[str]:
        """
        Запустить тренировку аватара
        
        Returns:
            str: ID тренировки или None в случае ошибки
        """
        url = f"{settings.BACKEND_API_URL}/train"
        headers = get_backend_headers(settings.BACKEND_API_KEY)
        
        try:
            data = {
                "user_id": user_id,
                "avatar_id": avatar_id,
                "photos": photos
            }
            async with self.http.post(
                url,
                json=data,
                headers=headers,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("training_id")
                return None
        except aiohttp.ClientError:
            return None

    async def check_training_status(self, training_id: str) -> Optional[Dict]:
        """
        Проверить статус тренировки
        
        Returns:
            Dict с информацией о статусе или None в случае ошибки
        """
        url = f"{settings.BACKEND_API_URL}/status/{training_id}"
        headers = get_backend_headers(settings.BACKEND_API_KEY)
        
        try:
            async with self.http.get(
                url,
                headers=headers,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except aiohttp.ClientError:
            return None

    async def generate_photo(self, avatar_id: str, prompt: str) -> Optional[bytes]:
        """
        Сгенерировать фото с помощью обученной модели
        
        Returns:
            bytes: сгенерированное фото или None в случае ошибки
        """
        url = f"{settings.BACKEND_API_URL}/generate"
        headers = get_backend_headers(settings.BACKEND_API_KEY)
        
        try:
            data = {
                "avatar_id": avatar_id,
                "prompt": prompt
            }
            async with self.http.post(
                url,
                json=data,
                headers=headers,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    return await response.read()
                return None
        except aiohttp.ClientError:
            return None
