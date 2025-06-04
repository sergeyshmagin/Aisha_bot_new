"""
Модуль для работы с хранилищем изображений
"""
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.core.logger import get_logger
from app.database.models.generation import ImageGeneration

logger = get_logger(__name__)


class ImageStorage:
    """Управление хранением изображений"""
    
    def __init__(self):
        self._storage = None
    
    def _get_storage(self):
        """Получает MinIO хранилище"""
        if not self._storage:
            from app.services.storage.minio import MinioStorage
            self._storage = MinioStorage()
        return self._storage
    
    async def save_images_to_minio(self, generation: ImageGeneration, fal_urls: List[str]) -> List[str]:
        """
        Сохраняет изображения из FAL AI в MinIO для постоянного хранения
        
        Args:
            generation: Объект генерации
            fal_urls: Список URL изображений из FAL AI
            
        Returns:
            List[str]: Список URL сохраненных изображений в MinIO
        """
        try:
            storage = self._get_storage()
            saved_urls = []
            
            logger.info(f"[MinIO] Начинаем сохранение {len(fal_urls)} изображений для генерации {generation.id}")
            
            for i, fal_url in enumerate(fal_urls):
                try:
                    logger.info(f"[MinIO] Скачиваем изображение {i+1}/{len(fal_urls)}: {fal_url}")
                    
                    # Скачиваем изображение с FAL AI
                    image_data = await self._download_image(fal_url)
                    if not image_data:
                        continue
                    
                    # Генерируем путь для сохранения в MinIO
                    object_path = self._generate_storage_path(generation.id, i + 1)
                    
                    # Сохраняем в MinIO
                    bucket = "generated"
                    logger.info(f"[MinIO] Загружаем в MinIO: bucket={bucket}, path={object_path}")
                    
                    success = await storage.upload_file(
                        bucket=bucket,
                        object_name=object_path,
                        data=image_data,
                        content_type="image/jpeg"
                    )
                    
                    if success:
                        # Генерируем presigned URL для доступа
                        minio_url = await storage.generate_presigned_url(
                            bucket=bucket,
                            object_name=object_path,
                            expires=86400  # 1 день
                        )
                        
                        if minio_url:
                            saved_urls.append(minio_url)
                            logger.info(f"[MinIO] ✅ Изображение {i+1} сохранено: {object_path}")
                        else:
                            logger.warning(f"[MinIO] ❌ Не удалось получить presigned URL для {object_path}")
                    else:
                        logger.warning(f"[MinIO] ❌ Не удалось загрузить изображение {i+1} в MinIO")
                        
                except Exception as e:
                    logger.exception(f"[MinIO] Ошибка сохранения изображения {i+1} в MinIO: {e}")
                    continue
            
            if saved_urls:
                logger.info(f"[MinIO] ✅ Успешно сохранено {len(saved_urls)}/{len(fal_urls)} изображений в MinIO")
            else:
                logger.warning(f"[MinIO] ❌ Не удалось сохранить ни одного изображения в MinIO")
                
            return saved_urls
            
        except Exception as e:
            logger.exception(f"[MinIO] Критическая ошибка сохранения в MinIO: {e}")
            return []
    
    async def delete_images_from_minio(self, result_urls: List[str], generation_id: UUID):
        """
        Удаляет изображения из MinIO
        
        Args:
            result_urls: Список URL для удаления
            generation_id: ID генерации для логирования
        """
        try:
            storage = self._get_storage()
            
            for url in result_urls:
                try:
                    # Извлекаем путь объекта из URL
                    object_name = self._extract_object_name_from_url(url)
                    if object_name:
                        await storage.delete_file("generated", object_name)
                        logger.info(f"[MinIO Delete] Удален объект {object_name} для генерации {generation_id}")
                    
                except Exception as e:
                    logger.warning(f"[MinIO Delete] Ошибка удаления объекта из URL {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.exception(f"[MinIO Delete] Критическая ошибка удаления изображений: {e}")
    
    async def _download_image(self, url: str) -> Optional[bytes]:
        """
        Скачивает изображение по URL
        
        Args:
            url: URL изображения
            
        Returns:
            Optional[bytes]: Данные изображения или None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        content_type = response.headers.get('content-type', 'image/jpeg')
                        logger.info(f"[MinIO] Изображение скачано: {len(image_data)} байт, Content-Type: {content_type}")
                        return image_data
                    else:
                        logger.warning(f"[MinIO] Ошибка скачивания изображения {url}: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.exception(f"[MinIO] Ошибка скачивания изображения {url}: {e}")
            return None
    
    def _generate_storage_path(self, generation_id: UUID, image_index: int) -> str:
        """
        Генерирует путь для сохранения изображения
        
        Args:
            generation_id: ID генерации
            image_index: Индекс изображения
            
        Returns:
            str: Путь для сохранения
        """
        date_str = datetime.now().strftime("%Y/%m/%d")
        filename = f"{generation_id}_{image_index:02d}.jpg"
        return f"{date_str}/{filename}"
    
    def _extract_object_name_from_url(self, url: str) -> Optional[str]:
        """
        Извлекает имя объекта из URL MinIO
        
        Args:
            url: URL изображения
            
        Returns:
            Optional[str]: Имя объекта или None
        """
        try:
            # Простая логика извлечения пути из URL
            # В реальности может быть более сложной в зависимости от структуры URL
            if "/generated/" in url:
                return url.split("/generated/")[1].split("?")[0]
            return None
        except Exception as e:
            logger.warning(f"Ошибка извлечения имени объекта из URL {url}: {e}")
            return None 