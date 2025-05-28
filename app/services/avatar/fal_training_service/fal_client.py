"""
Клиент FAL AI для обучения моделей
Выделено из app/services/avatar/fal_training_service.py для соблюдения правила ≤500 строк
"""
import json
from typing import Dict, Any, Optional
from uuid import UUID

from app.core.config import settings
from app.core.logger import get_logger
from app.core.di import get_user_service, get_avatar_service
from app.utils.avatar_utils import (
    format_finetune_comment,
    generate_trigger_word
)

logger = get_logger(__name__)


class FALClient:
    """Клиент для работы с FAL AI API"""
    
    def __init__(self):
        self.fal_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Инициализация FAL клиента"""
        try:
            import fal_client
            import os
            
            # Проверяем наличие API ключа
            api_key = settings.effective_fal_api_key
            if api_key:
                # Устанавливаем переменную окружения для FAL клиента
                os.environ['FAL_KEY'] = api_key
                logger.info(f"FAL API ключ установлен: {api_key[:20]}...")
                
                # Инициализируем клиент
                self.fal_client = fal_client
            else:
                logger.warning("FAL_API_KEY/FAL_KEY не установлен")
                
        except ImportError:
            logger.warning("fal_client не установлен")
    
    def is_available(self) -> bool:
        """Проверяет доступность FAL клиента"""
        return self.fal_client is not None
    
    async def train_portrait_model(
        self,
        images_data_url: str,
        trigger_phrase: str,
        steps: int,
        learning_rate: float,
        webhook_url: Optional[str] = None
    ) -> str:
        """
        Обучение портретной модели через Flux LoRA Portrait Trainer
        Исправлено согласно официальной документации FAL AI
        """
        if not self.fal_client:
            raise RuntimeError("FAL client не инициализирован")
        
        # Конфигурация для портретного тренера согласно документации
        config = {
            "images_data_url": images_data_url,
            "trigger_phrase": trigger_phrase,
            "steps": steps,
            "learning_rate": learning_rate,
            "multiresolution_training": settings.FAL_PORTRAIT_MULTIRESOLUTION,
            "subject_crop": settings.FAL_PORTRAIT_SUBJECT_CROP,
            "create_masks": settings.FAL_PORTRAIT_CREATE_MASKS,
        }
        
        logger.info(f"🎭 Запуск flux-lora-portrait-trainer: trigger={trigger_phrase}")
        logger.info(f"🎭 Параметры: steps={steps}, lr={learning_rate}")
        logger.info(f"🎭 Webhook URL: {webhook_url}")
        logger.info(f"🎭 Полная конфигурация: {json.dumps(config, indent=2)}")
        
        # Используем submit_async согласно документации FAL AI
        try:
            # Детальное логирование для отладки webhook
            logger.info(f"🔗 ОТЛАДКА WEBHOOK (ПОРТРЕТ):")
            logger.info(f"   Webhook URL перед отправкой: {webhook_url}")
            logger.info(f"   Тип webhook_url: {type(webhook_url)}")
            logger.info(f"   Webhook пустой?: {not webhook_url}")
            
            if webhook_url:
                logger.info(f"   ✅ Webhook будет передан в FAL AI")
            else:
                logger.warning(f"   ⚠️ Webhook НЕ будет передан (пустой)")
            
            logger.info(f"🚀 Отправка запроса в FAL AI...")
            logger.info(f"   Endpoint: fal-ai/flux-lora-portrait-trainer")
            logger.info(f"   Arguments: {json.dumps(config, indent=2)}")
            logger.info(f"   Webhook URL: {webhook_url}")
            
            handler = await self.fal_client.submit_async(
                "fal-ai/flux-lora-portrait-trainer",
                arguments=config,
                webhook_url=webhook_url
            )
            
            request_id = handler.request_id
            logger.info(f"🎭 Успешно отправлен запрос в FAL AI: {request_id}")
            logger.info(f"🔗 Webhook должен быть настроен для: {webhook_url}")
            
            return request_id
            
        except Exception as e:
            logger.exception(f"Ошибка отправки запроса в FAL AI: {e}")
            logger.error(f"🔗 Webhook URL при ошибке: {webhook_url}")
            raise
    
    async def train_general_model(
        self,
        images_data_url: str,
        trigger_word: str,
        iterations: int,
        learning_rate: float,
        priority: str = "quality",
        webhook_url: Optional[str] = None,
        avatar_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Обучение универсальной модели через Flux Pro Trainer
        Исправлено согласно официальной документации FAL AI
        """
        if not self.fal_client:
            raise RuntimeError("FAL client не инициализирован")
        
        # Получаем данные аватара и пользователя для комментария
        finetune_comment = "Художественный аватар"
        if avatar_id:
            try:
                async with get_avatar_service() as avatar_service:
                    avatar = await avatar_service.get_avatar(avatar_id)
                    if avatar:
                        async with get_user_service() as user_service:
                            user = await user_service.get_user_by_id(avatar.user_id)
                            if user:
                                finetune_comment = format_finetune_comment(
                                    avatar_name=avatar.name,
                                    telegram_username=user.username or f"user_{user.id}"
                                )
            except Exception as e:
                logger.warning(f"Не удалось получить данные для комментария: {e}")
        
        # Конфигурация для flux-pro-trainer согласно официальной документации
        config = {
            "data_url": images_data_url,  # Правильное имя параметра согласно документации
            "mode": settings.FAL_PRO_MODE,
            "finetune_comment": finetune_comment,  # Обязательный параметр согласно документации
            "iterations": iterations,
            "learning_rate": learning_rate,
            "priority": priority,
            "captioning": settings.FAL_PRO_CAPTIONING,
            "trigger_word": trigger_word,
            "lora_rank": settings.FAL_PRO_LORA_RANK,
            "finetune_type": settings.FAL_PRO_FINETUNE_TYPE,
        }
        
        logger.info(f"🎨 Запуск flux-pro-trainer: {finetune_comment}, trigger: {trigger_word}")
        logger.info(f"🎨 Параметры: iterations={iterations}, lr={learning_rate}, priority={priority}")
        logger.info(f"🎨 Webhook URL: {webhook_url}")
        logger.info(f"🎨 Полная конфигурация: {json.dumps(config, indent=2)}")
        
        # Используем submit_async согласно документации FAL AI
        try:
            # Детальное логирование для отладки webhook
            logger.info(f"🔗 ОТЛАДКА WEBHOOK:")
            logger.info(f"   Webhook URL перед отправкой: {webhook_url}")
            logger.info(f"   Тип webhook_url: {type(webhook_url)}")
            logger.info(f"   Webhook пустой?: {not webhook_url}")
            
            if webhook_url:
                logger.info(f"   ✅ Webhook будет передан в FAL AI")
            else:
                logger.warning(f"   ⚠️ Webhook НЕ будет передан (пустой)")
            
            logger.info(f"🚀 Отправка запроса в FAL AI...")
            logger.info(f"   Endpoint: fal-ai/flux-pro-trainer")
            logger.info(f"   Arguments: {json.dumps(config, indent=2)}")
            logger.info(f"   Webhook URL: {webhook_url}")
            
            handler = await self.fal_client.submit_async(
                "fal-ai/flux-pro-trainer",
                arguments=config,
                webhook_url=webhook_url
            )
            
            request_id = handler.request_id
            logger.info(f"🎨 Успешно отправлен запрос в FAL AI: {request_id}")
            logger.info(f"🔗 Webhook должен быть настроен для: {webhook_url}")
            
            return {
                "finetune_id": request_id,
                "request_id": request_id
            }
            
        except Exception as e:
            logger.exception(f"Ошибка отправки запроса в FAL AI: {e}")
            logger.error(f"🔗 Webhook URL при ошибке: {webhook_url}")
            raise
    
    async def check_training_status(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """Проверяет статус обучения согласно документации FAL AI"""
        if not self.fal_client:
            raise RuntimeError("FAL client не инициализирован")
        
        # Проверяем статус через FAL API согласно документации
        if training_type == "portrait":
            endpoint = "fal-ai/flux-lora-portrait-trainer"
        else:
            endpoint = "fal-ai/flux-pro-trainer"
        
        # Используем status_async согласно документации
        status = await self.fal_client.status_async(endpoint, request_id, with_logs=True)
        
        logger.info(f"🔍 Статус обучения {request_id}: {status}")
        return status
    
    async def get_training_result(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """Получает результат обучения согласно документации FAL AI"""
        if not self.fal_client:
            raise RuntimeError("FAL client не инициализирован")
        
        # Получаем результат через FAL API согласно документации
        if training_type == "portrait":
            endpoint = "fal-ai/flux-lora-portrait-trainer"
        else:
            endpoint = "fal-ai/flux-pro-trainer"
        
        # Используем result_async согласно документации
        result = await self.fal_client.result_async(endpoint, request_id)
        
        logger.info(f"🎯 Результат обучения {request_id}: {result}")
        return result 