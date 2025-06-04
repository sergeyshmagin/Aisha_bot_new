"""
Модуль обучения моделей в FAL AI
"""
import asyncio
from typing import Dict, List, Optional, Any
from uuid import UUID

import fal_client

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class FalTrainer:
    """Обучение моделей в FAL AI"""
    
    def __init__(self):
        self.api_key = settings.FAL_API_KEY
        self.test_mode = settings.AVATAR_TEST_MODE
        
        # Настраиваем FAL клиент
        if self.api_key:
            fal_client.api_key = self.api_key
    
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
        """
        Запускает портретное обучение через flux-lora-portrait-trainer
        
        Args:
            images_data_url: URL архива с изображениями
            trigger_phrase: Триггерная фраза для модели
            steps: Количество шагов обучения
            learning_rate: Скорость обучения
            multiresolution_training: Многоразрешенное обучение
            subject_crop: Обрезка субъекта
            create_masks: Создание масок
            webhook_url: URL для webhook уведомлений
            
        Returns:
            Optional[str]: request_id обучения
        """
        try:
            if self.test_mode:
                logger.info("[FAL Trainer] Тестовый режим - симуляция портретного обучения")
                await asyncio.sleep(0.1)
                return f"test_portrait_request_{hash(images_data_url) % 10000}"
            
            logger.info(f"[FAL Trainer] Запуск портретного обучения: trigger='{trigger_phrase}', steps={steps}")
            
            # Подготавливаем параметры для FAL AI
            arguments = {
                "images_data_url": images_data_url,
                "steps": steps,
                "learning_rate": learning_rate,
                "multiresolution_training": multiresolution_training,
                "subject_crop": subject_crop,
                "create_masks": create_masks
            }
            
            # Добавляем триггерную фразу если указана
            if trigger_phrase:
                arguments["trigger_phrase"] = trigger_phrase
            
            # Добавляем webhook если указан
            if webhook_url:
                arguments["webhook_url"] = webhook_url
            
            logger.debug(f"[FAL Trainer] Параметры обучения: {arguments}")
            
            # Запускаем обучение через FAL AI
            result = fal_client.submit(
                "fal-ai/flux-lora-portrait-trainer",
                arguments=arguments
            )
            
            request_id = result.request_id
            logger.info(f"[FAL Trainer] Портретное обучение запущено: request_id={request_id}")
            
            return request_id
            
        except Exception as e:
            logger.exception(f"[FAL Trainer] Ошибка запуска портретного обучения: {e}")
            return None
    
    async def train_avatar_with_config(
        self,
        data_url: str,
        user_id: UUID,
        avatar_id: UUID,
        training_config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Запускает обучение аватара с конфигурацией
        
        Args:
            data_url: URL архива с фотографиями
            user_id: ID пользователя
            avatar_id: ID аватара
            training_config: Конфигурация обучения
            
        Returns:
            Optional[str]: request_id обучения
        """
        try:
            training_type = training_config.get("training_type", "portrait")
            
            if training_type == "portrait":
                return await self._train_portrait_avatar(
                    data_url=data_url,
                    user_id=user_id,
                    avatar_id=avatar_id,
                    config=training_config
                )
            else:
                logger.error(f"[FAL Trainer] Неподдерживаемый тип обучения: {training_type}")
                raise ValueError(f"Неподдерживаемый тип обучения: {training_type}")
                
        except Exception as e:
            logger.exception(f"[FAL Trainer] Ошибка обучения аватара {avatar_id}: {e}")
            return None
    
    async def _train_portrait_avatar(
        self,
        data_url: str,
        user_id: UUID,
        avatar_id: UUID,
        config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Запускает портретное обучение аватара
        
        Args:
            data_url: URL архива с фотографиями
            user_id: ID пользователя
            avatar_id: ID аватара
            config: Конфигурация обучения
            
        Returns:
            Optional[str]: request_id
        """
        try:
            # Получаем настройки портретного обучения
            trigger_phrase = config.get("trigger_phrase", f"PERSON_{avatar_id.hex[:8]}")
            steps = config.get("steps", settings.FAL_PORTRAIT_STEPS)
            learning_rate = config.get("learning_rate", settings.FAL_PORTRAIT_LEARNING_RATE)
            multiresolution_training = config.get("multiresolution_training", settings.FAL_PORTRAIT_MULTIRESOLUTION)
            subject_crop = config.get("subject_crop", settings.FAL_PORTRAIT_SUBJECT_CROP)
            create_masks = config.get("create_masks", settings.FAL_PORTRAIT_CREATE_MASKS)
            webhook_url = config.get("webhook_url", settings.FAL_WEBHOOK_URL)
            
            logger.info(f"[FAL Trainer] Портретное обучение аватара {avatar_id}: trigger='{trigger_phrase}', steps={steps}")
            
            # Запускаем портретное обучение
            request_id = await self.train_portrait_model(
                images_data_url=data_url,
                trigger_phrase=trigger_phrase,
                steps=steps,
                learning_rate=learning_rate,
                multiresolution_training=multiresolution_training,
                subject_crop=subject_crop,
                create_masks=create_masks,
                webhook_url=webhook_url
            )
            
            return request_id
            
        except Exception as e:
            logger.exception(f"[FAL Trainer] Ошибка портретного обучения аватара {avatar_id}: {e}")
            return None
    
    def get_training_config_summary(self) -> Dict[str, Any]:
        """
        Получает сводку конфигурации обучения
        
        Returns:
            Dict[str, Any]: Сводка конфигурации
        """
        return {
            "portrait_steps": settings.FAL_PORTRAIT_STEPS,
            "portrait_learning_rate": settings.FAL_PORTRAIT_LEARNING_RATE,
            "portrait_multiresolution": settings.FAL_PORTRAIT_MULTIRESOLUTION,
            "portrait_subject_crop": settings.FAL_PORTRAIT_SUBJECT_CROP,
            "portrait_create_masks": settings.FAL_PORTRAIT_CREATE_MASKS,
            "webhook_url": settings.FAL_WEBHOOK_URL,
            "test_mode": self.test_mode,
            "api_available": bool(self.api_key)
        }
    
    def is_available(self) -> bool:
        """Проверяет доступность FAL AI для обучения"""
        return bool(self.api_key) or self.test_mode 