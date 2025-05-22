"""
Сервис для обработки изображений
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

class ImageResult(BaseModel):
    """Результат обработки изображения"""
    file_id: str
    width: int
    height: int
    file_size: int
    file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None

class ImageProcessingService(BaseService):
    """
    Сервис для обработки изображений:
    - Сохранение в MinIO
    - Создание превью
    - Поиск по тегам
    """

    def __init__(self):
        super().__init__()
        self.temp_dir = Path(settings.TEMP_DIR) / "images"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def process_image(
        self,
        photo: Union[PhotoSize, List[PhotoSize]],
        user_id: int,
        tags: Optional[List[str]] = None
    ) -> ImageResult:
        """
        Обрабатывает изображение:
        1. Скачивает файл
        2. Создает превью
        3. Сохраняет в MinIO
        
        Args:
            photo: Фото или список фото (берется самое большое)
            user_id: ID пользователя
            tags: Теги для поиска
            
        Returns:
            ImageResult: Результат обработки
        """
        try:
            # Берем самое большое фото из списка
            if isinstance(photo, list):
                photo = max(photo, key=lambda x: x.file_size)
            
            # 1. Скачиваем файл
            file_path = await self._download_image(photo)
            
            # 2. Создаем превью
            thumbnail_path = await self._create_thumbnail(file_path)
            
            # 3. Сохраняем в MinIO
            async with StorageService() as storage:
                minio_path = await storage.upload_file(
                    bucket="images",
                    file_path=file_path,
                    user_id=user_id,
                    metadata={"tags": ",".join(tags) if tags else ""}
                )
                
                thumbnail_minio_path = await storage.upload_file(
                    bucket="thumbnails",
                    file_path=thumbnail_path,
                    user_id=user_id
                )
            
            return ImageResult(
                file_id=photo.file_id,
                width=photo.width,
                height=photo.height,
                file_size=photo.file_size,
                file_path=minio_path,
                thumbnail_path=thumbnail_minio_path
            )
            
        except Exception as e:
            logger.exception("Ошибка при обработке изображения")
            raise
        finally:
            # Очищаем временные файлы
            await self._cleanup_temp_files(file_path, thumbnail_path)

    async def search_images(
        self,
        user_id: int,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[ImageResult]:
        """
        Ищет изображения по тегам
        
        Args:
            user_id: ID пользователя
            tags: Теги для поиска
            limit: Максимальное количество результатов
            
        Returns:
            List[ImageResult]: Список найденных изображений
        """
        try:
            async with StorageService() as storage:
                # TODO: Реализовать поиск по тегам в MinIO
                return []
                
        except Exception as e:
            logger.exception("Ошибка при поиске изображений")
            raise

    async def _download_image(self, photo: PhotoSize) -> Path:
        """Скачивает изображение во временную директорию"""
        file_path = self.temp_dir / f"{photo.file_id}.jpg"
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(await photo.download())
            
        return file_path

    async def _create_thumbnail(self, file_path: Path) -> Path:
        """Создает превью изображения"""
        thumbnail_path = file_path.parent / f"thumb_{file_path.name}"
        
        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i", str(file_path),
            "-vf", "scale=320:-1",
            str(thumbnail_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        return thumbnail_path

    async def _cleanup_temp_files(self, *file_paths: Path):
        """Удаляет временные файлы"""
        for path in file_paths:
            if path and path.exists():
                try:
                    path.unlink()
                except Exception as e:
                    logger.error(f"Ошибка при удалении {path}: {e}") 