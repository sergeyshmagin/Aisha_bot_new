"""
Сервис для работы с аватарами
"""
import asyncio
from pathlib import Path
from typing import List, Optional, Union

import aiofiles
from aiogram.types import PhotoSize
from pydantic import BaseModel

from aisha_v2.app.core.config import settings
from aisha_v2.app.core.logger import get_logger
from aisha_v2.app.services.storage import StorageService
from aisha_v2.app.services.base import BaseService

logger = get_logger(__name__)

class AvatarResult(BaseModel):
    """Результат обработки аватара"""
    file_id: str
    width: int
    height: int
    file_size: int
    file_path: Optional[str] = None
    style: Optional[str] = None

class AvatarService(BaseService):
    """
    Сервис для работы с аватарами:
    - Сохранение в MinIO
    - Применение стилей
    - Генерация новых аватаров
    """

    def __init__(self):
        super().__init__()
        self.temp_dir = Path(settings.TEMP_DIR) / "avatars"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def process_avatar(
        self,
        photo: Union[PhotoSize, List[PhotoSize]],
        user_id: int,
        style: Optional[str] = None
    ) -> AvatarResult:
        """
        Обрабатывает аватар:
        1. Скачивает файл
        2. Применяет стиль
        3. Сохраняет в MinIO
        
        Args:
            photo: Фото или список фото (берется самое большое)
            user_id: ID пользователя
            style: Стиль для аватара
            
        Returns:
            AvatarResult: Результат обработки
        """
        try:
            # Берем самое большое фото из списка
            if isinstance(photo, list):
                photo = max(photo, key=lambda x: x.file_size)
            
            # 1. Скачиваем файл
            file_path = await self._download_avatar(photo)
            
            # 2. Применяем стиль
            if style:
                file_path = await self._apply_style(file_path, style)
            
            # 3. Сохраняем в MinIO
            storage = StorageService()
            
            # Читаем данные из файла
            async with aiofiles.open(file_path, 'rb') as f:
                file_data = await f.read()
                
            # Имя объекта в MinIO
            object_name = f"{user_id}/{Path(file_path).name}"
            
            # Загружаем в MinIO
            minio_path = await storage.upload_file(
                bucket="avatars",
                object_name=object_name,
                data=file_data,
                content_type="image/jpeg"
            )
            
            return AvatarResult(
                file_id=photo.file_id,
                width=photo.width,
                height=photo.height,
                file_size=photo.file_size,
                file_path=minio_path,
                style=style
            )
            
        except Exception as e:
            logger.exception("Ошибка при обработке аватара")
            raise
        finally:
            # Очищаем временные файлы
            await self._cleanup_temp_files(file_path)

    async def generate_avatar(
        self,
        user_id: int,
        style: str,
        prompt: Optional[str] = None
    ) -> AvatarResult:
        """
        Генерирует новый аватар
        
        Args:
            user_id: ID пользователя
            style: Стиль для аватара
            prompt: Описание для генерации
            
        Returns:
            AvatarResult: Результат генерации
        """
        try:
            # TODO: Реализовать генерацию через Stable Diffusion
            raise NotImplementedError("Генерация аватаров пока не реализована")
            
        except Exception as e:
            logger.exception("Ошибка при генерации аватара")
            raise

    async def get_user_avatars(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[AvatarResult]:
        """
        Получает список аватаров пользователя
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество результатов
            
        Returns:
            List[AvatarResult]: Список аватаров
        """
        try:
            storage = StorageService()
            # TODO: Реализовать получение списка аватаров из MinIO
            return []
                
        except Exception as e:
            logger.exception("Ошибка при получении списка аватаров")
            raise

    async def _download_avatar(self, photo: PhotoSize) -> Path:
        """Скачивает аватар во временную директорию"""
        file_path = self.temp_dir / f"{photo.file_id}.jpg"
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(await photo.download())
            
        return file_path

    async def _apply_style(self, file_path: Path, style: str) -> Path:
        """Применяет стиль к аватару"""
        styled_path = file_path.parent / f"{style}_{file_path.name}"
        
        # TODO: Реализовать применение стилей через Stable Diffusion
        # Пока просто копируем файл
        async with aiofiles.open(file_path, "rb") as src:
            async with aiofiles.open(styled_path, "wb") as dst:
                await dst.write(await src.read())
                
        return styled_path

    async def _cleanup_temp_files(self, *file_paths: Path):
        """Удаляет временные файлы"""
        for path in file_paths:
            if path and path.exists():
                try:
                    path.unlink()
                except Exception as e:
                    logger.error(f"Ошибка при удалении {path}: {e}") 