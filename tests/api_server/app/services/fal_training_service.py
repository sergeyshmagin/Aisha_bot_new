"""
Сервис для обучения аватаров через FAL AI
Поддерживает автоматическую подготовку данных и отправку на обучение
"""
import asyncio
import aiohttp
import zipfile
import io
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path
from uuid import UUID

import fal_client
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.logger import get_webhook_logger

logger = get_webhook_logger()

class FALTrainingService:
    """Сервис для обучения аватаров через FAL AI"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Настройка FAL клиента
        fal_api_key = settings.effective_fal_api_key
        if fal_api_key:
            import os
            os.environ['FAL_KEY'] = fal_api_key
    
    async def start_avatar_training(
        self,
        avatar_id: UUID,
        photos: List[Dict[str, Any]]  # Изменено: принимаем список словарей вместо объектов
    ) -> str:
        """
        Запускает обучение аватара через FAL AI
        
        Args:
            avatar_id: ID аватара
            photos: Список фотографий для обучения (словари с minio_key и другими данными)
            
        Returns:
            request_id от FAL AI
        """
        try:
            logger.info(f"[FAL TRAINING] Начинаем обучение аватара {avatar_id}, фотографий: {len(photos)}")
            
            # Подготавливаем данные для обучения
            training_data_url = await self._prepare_training_data(avatar_id, photos)
            
            # Для простоты используем портретный тип по умолчанию
            request_id = await self._train_portrait_avatar(avatar_id, training_data_url)
            
            logger.info(f"[FAL TRAINING] Обучение запущено. request_id: {request_id}")
            return request_id
            
        except Exception as e:
            logger.exception(f"[FAL TRAINING] Ошибка запуска обучения аватара {avatar_id}: {e}")
            raise
    
    async def _prepare_training_data(
        self,
        avatar_id: UUID,
        photos: List[Dict[str, Any]]
    ) -> str:
        """
        Подготавливает данные для обучения (создает ZIP архив)
        
        Args:
            avatar_id: ID аватара
            photos: Список фотографий
            
        Returns:
            URL к ZIP архиву в MinIO
        """
        try:
            logger.info(f"[FAL TRAINING] Подготовка данных для аватара {avatar_id}, фотографий: {len(photos)}")
            
            # Создаем ZIP архив в памяти
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, photo in enumerate(photos):
                    # Для тестирования создаем заглушки
                    # В реальной реализации здесь будет скачивание из MinIO
                    
                    # Определяем расширение файла
                    minio_key = photo.get('minio_key', f'photo_{i}.jpg')
                    file_extension = Path(minio_key).suffix or '.jpg'
                    
                    # Добавляем заглушку изображения в архив
                    filename = f"image_{i+1:03d}{file_extension}"
                    # Заглушка - в реальности здесь будет photo_data из MinIO
                    zip_file.writestr(filename, b"fake_image_data")
                    
                    # Создаем простое описание для каждого изображения
                    caption = f"[trigger] person"
                    caption_filename = f"image_{i+1:03d}.txt"
                    zip_file.writestr(caption_filename, caption)
            
            # Получаем данные архива
            zip_data = zip_buffer.getvalue()
            zip_buffer.close()
            
            # Для тестирования возвращаем заглушку URL
            # В реальной реализации здесь будет загрузка в MinIO
            training_data_url = f"https://test.example.com/training_data/{avatar_id}/training_photos.zip"
            
            logger.info(f"[FAL TRAINING] Данные подготовлены: {training_data_url}")
            return training_data_url
            
        except Exception as e:
            logger.exception(f"[FAL TRAINING] Ошибка подготовки данных: {e}")
            raise
    
    async def _train_portrait_avatar(
        self,
        avatar_id: UUID,
        training_data_url: str
    ) -> str:
        """
        Запускает обучение портретного аватара через FLUX LoRA Portrait Trainer
        """
        try:
            # Параметры для портретного обучения
            arguments = {
                "images_data_url": training_data_url,
                "trigger_phrase": f"TOK_{avatar_id.hex[:8]}",
                "steps": 1000,
                "learning_rate": 0.0002,
                "multiresolution_training": True,
                "subject_crop": True,
                "create_masks": True
            }
            
            # Webhook URL с указанием типа обучения
            webhook_url = f"{settings.FAL_WEBHOOK_URL}?training_type=portrait"
            
            logger.info(f"[FAL TRAINING] Запуск Portrait Trainer с параметрами: {arguments}")
            
            # Отправляем запрос
            handler = await fal_client.submit_async(
                "fal-ai/flux-lora-portrait-trainer",
                arguments=arguments,
                webhook_url=webhook_url
            )
            
            request_id = handler.request_id
            logger.info(f"[FAL TRAINING] Portrait Trainer запущен. request_id: {request_id}")
            
            return request_id
            
        except Exception as e:
            logger.exception(f"[FAL TRAINING] Ошибка запуска Portrait Trainer: {e}")
            raise
    
    async def check_training_status(
        self,
        request_id: str,
        training_type: str = "portrait"
    ) -> Dict[str, Any]:
        """
        Проверяет статус обучения в FAL AI
        """
        try:
            if training_type == "portrait":
                endpoint = "fal-ai/flux-lora-portrait-trainer"
            else:
                endpoint = "fal-ai/flux-pro-trainer"
            
            status = await fal_client.status_async(
                endpoint,
                request_id,
                with_logs=True
            )
            
            # Обрабатываем разные типы ответов от FAL AI
            if hasattr(status, 'status'):
                # Объект со статусом
                result = {
                    "status": status.status,
                    "logs": getattr(status, 'logs', []),
                    "request_id": request_id
                }
            elif isinstance(status, dict):
                # Словарь
                result = status
            else:
                # Другие типы (например InProgress)
                result = {
                    "status": str(type(status).__name__).lower(),
                    "logs": [],
                    "request_id": request_id,
                    "raw_status": str(status)
                }
            
            logger.debug(f"[FAL TRAINING] Статус {request_id}: {result}")
            return result
            
        except Exception as e:
            logger.exception(f"[FAL TRAINING] Ошибка проверки статуса: {e}")
            return {
                "status": "error",
                "error": str(e),
                "request_id": request_id
            }
    
    async def get_training_result(
        self,
        request_id: str,
        training_type: str = "portrait"
    ) -> Dict[str, Any]:
        """
        Получает результат обучения из FAL AI
        """
        try:
            if training_type == "portrait":
                endpoint = "fal-ai/flux-lora-portrait-trainer"
            else:
                endpoint = "fal-ai/flux-pro-trainer"
            
            result = await fal_client.result_async(endpoint, request_id)
            
            logger.info(f"[FAL TRAINING] Результат получен для {request_id}")
            return result
            
        except Exception as e:
            logger.exception(f"[FAL TRAINING] Ошибка получения результата: {e}")
            raise 