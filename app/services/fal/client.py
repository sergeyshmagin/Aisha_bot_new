"""
FAL AI клиент для обучения моделей аватаров (рефакторинг)
Модульная архитектура для лучшей поддержки и читаемости
"""
import asyncio
from typing import Dict, List, Optional, Any
from uuid import UUID

import fal_client

from app.core.config import settings
from app.core.logger import get_logger
from app.services.fal.files.file_manager import FalFileManager
from app.services.fal.training.trainer import FalTrainer
from app.services.fal.status.status_checker import FalStatusChecker

logger = get_logger(__name__)


class FalAIClient:
    """
    Клиент для работы с FAL AI API (рефакторинг)
    
    Основные функции:
    - Обучение персональных моделей (finetune)
    - Мониторинг прогресса обучения
    - Генерация изображений с обученными моделями
    - Управление файлами и архивами
    """

    def __init__(self):
        self.logger = logger
        self.api_key = settings.FAL_API_KEY
        self.test_mode = settings.AVATAR_TEST_MODE
        
        # Инициализируем модули
        self.file_manager = FalFileManager()
        self.trainer = FalTrainer()
        self.status_checker = FalStatusChecker()
        
        # Настраиваем FAL клиент
        if self.api_key:
            fal_client.api_key = self.api_key
        else:
            logger.debug("FAL_API_KEY не установлен, работа в тестовом режиме")

    async def train_avatar(
        self,
        user_id: UUID,
        avatar_id: UUID,
        name: str,
        gender: str,
        photo_urls: List[str],
        training_config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Запускает обучение аватара на FAL AI
        
        Args:
            user_id: ID пользователя
            avatar_id: ID аватара
            name: Имя аватара
            gender: Пол аватара
            photo_urls: Список URL фотографий в MinIO
            training_config: Конфигурация обучения (включая training_type)
            
        Returns:
            Optional[str]: request_id или None при ошибке
            
        Raises:
            RuntimeError: При критических ошибках
        """
        try:
            if self.test_mode:
                logger.info(f"[FAL TEST MODE] Симуляция обучения аватара {avatar_id}")
                # В тестовом режиме возвращаем мок request_id
                mock_request_id = f"test_request_{avatar_id}"
                await asyncio.sleep(0.1)  # Симуляция задержки
                return mock_request_id
            
            # Получаем тип обучения из конфигурации
            training_type = training_config.get("training_type", "portrait") if training_config else "portrait"
            
            logger.info(
                f"[FAL AI] Начало обучения аватара {avatar_id}: "
                f"user_id={user_id}, name='{name}', gender={gender}, "
                f"photos={len(photo_urls)}, training_type={training_type}"
            )
            
            # 1. Скачиваем фотографии и создаем архив
            data_url = await self.file_manager.download_and_create_archive(photo_urls, avatar_id)
            
            if not data_url:
                raise RuntimeError("Не удалось скачать фотографии для создания архива")
            
            # 2. Запускаем обучение
            if training_type == "portrait":
                request_id = await self.trainer.train_avatar_with_config(
                    data_url=data_url,
                    user_id=user_id,
                    avatar_id=avatar_id,
                    training_config=training_config or {}
                )
            else:
                logger.error(f"[FAL AI] Неподдерживаемый тип обучения: {training_type}")
                raise ValueError(f"Неподдерживаемый тип обучения: {training_type}")
            
            logger.info(f"[FAL AI] Обучение запущено успешно: request_id={request_id}")
            return request_id
            
        except Exception as e:
            logger.exception(f"[FAL AI] Критическая ошибка при обучении аватара {avatar_id}: {e}")
            raise RuntimeError(f"Ошибка обучения аватара: {str(e)}")
        
        finally:
            # Очищаем временные файлы
            await self.file_manager.cleanup_temp_files()

    async def get_training_status(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """
        Получает статус обучения модели
        
        Args:
            request_id: ID обучения FAL AI
            training_type: Тип обучения
            
        Returns:
            Dict[str, Any]: Статус обучения
        """
        return await self.status_checker.get_training_status(request_id, training_type)

    # Методы делегирования для обратной совместимости
    async def download_and_create_archive(self, photo_urls: List[str], avatar_id: UUID) -> Optional[str]:
        """Скачивает фотографии и создает архив"""
        return await self.file_manager.download_and_create_archive(photo_urls, avatar_id)
    
    async def download_photos_from_minio(self, photo_urls: List[str], avatar_id: UUID) -> List:
        """Скачивает фотографии из MinIO"""
        return await self.file_manager.download_photos_from_minio(photo_urls, avatar_id)
    
    async def create_and_upload_archive(self, photo_paths: List, avatar_id: UUID) -> Optional[str]:
        """Создает и загружает архив"""
        return await self.file_manager.create_and_upload_archive(photo_paths, avatar_id)
    
    async def train_portrait_model(
        self,
        images_data_url: str,
        trigger_phrase: Optional[str] = None,
        steps: int = 1000,
        learning_rate: float = 0.0002,
        multiresolution_training: bool = True,
        subject_crop: bool = True,
        create_masks: bool = False,
        webhook_url: Optional[str] = None
    ) -> Optional[str]:
        """Запускает портретное обучение"""
        return await self.trainer.train_portrait_model(
            images_data_url=images_data_url,
            trigger_phrase=trigger_phrase,
            steps=steps,
            learning_rate=learning_rate,
            multiresolution_training=multiresolution_training,
            subject_crop=subject_crop,
            create_masks=create_masks,
            webhook_url=webhook_url
        )
    
    async def _cleanup_temp_files(self):
        """Очищает временные файлы"""
        await self.file_manager.cleanup_temp_files()
    
    def parse_webhook_status(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Парсит данные webhook"""
        return self.status_checker.parse_webhook_status(webhook_data)
    
    def is_available(self) -> bool:
        """Проверяет доступность FAL AI"""
        return bool(self.api_key) or self.test_mode
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Получает сводку конфигурации"""
        base_config = {
            "api_available": bool(self.api_key),
            "test_mode": self.test_mode,
            "fal_api_key_set": bool(self.api_key)
        }
        
        # Добавляем конфигурацию обучения
        training_config = self.trainer.get_training_config_summary()
        base_config.update(training_config)
        
        return base_config 