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
from app.services.cache_service import cache_service
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
    
    async def get_training_status(self, request_id: str, training_type: str = "portrait") -> Optional[Dict[str, Any]]:
        """
        Получает статус обучения модели с кешированием
        
        Args:
            request_id: ID обучения FAL AI
            training_type: Тип обучения (portrait/style)
            
        Returns:
            Optional[Dict[str, Any]]: Статус обучения или None при ошибке
        """
        try:
            # ✅ Проверяем кеш сначала (TTL 5 минут для статусов)
            cached_status = await cache_service.get_cached_fal_status(request_id)
            if cached_status:
                logger.debug(f"🎯 Получен статус из кеша для {request_id}: {cached_status.get('status')}")
                return cached_status
            
            if not self.is_available():
                logger.warning("FAL клиент недоступен")
                return None
            
            # Если тестовый режим
            if settings.AVATAR_TEST_MODE:
                # В тестовом режиме возвращаем мок статус
                mock_status = {
                    "status": "completed",
                    "progress": 100,
                    "created_at": "2025-05-23T16:00:00Z",
                    "updated_at": "2025-05-23T16:30:00Z",
                    "completed_at": "2025-05-23T16:30:00Z",
                    "message": "Training completed successfully (test mode)",
                    "request_id": request_id
                }
                
                # ✅ Кешируем мок статус
                await cache_service.cache_fal_status(request_id, mock_status, ttl=300)
                
                return mock_status
            
            # Определяем endpoint по типу обучения
            if training_type == "portrait":
                endpoint = "fal-ai/flux-lora-portrait-trainer"
            else:  # style
                endpoint = "fal-ai/flux-pro-trainer"
            
            logger.info(f"🔍 Проверка статуса FAL AI: {request_id} (endpoint: {endpoint})")
            
            # Получаем статус через FAL API
            try:
                result = await self.fal_client.status_async(endpoint, request_id)
                
                if result:
                    status_data = {
                        "status": result.get("status", "unknown"),
                        "progress": result.get("progress", 0),
                        "created_at": result.get("created_at"),
                        "updated_at": result.get("updated_at"),
                        "completed_at": result.get("completed_at"),
                        "message": result.get("message", ""),
                        "request_id": request_id,
                        "endpoint": endpoint
                    }
                    
                    # ✅ Кешируем статус (TTL зависит от статуса)
                    if status_data["status"] in ["completed", "failed", "cancelled"]:
                        # Финальные статусы кешируем на час
                        await cache_service.cache_fal_status(request_id, status_data, ttl=3600)
                    else:
                        # Промежуточные статусы кешируем на 2 минуты
                        await cache_service.cache_fal_status(request_id, status_data, ttl=120)
                    
                    logger.info(f"📋 Статус FAL AI {request_id}: {status_data['status']} ({status_data.get('progress', 0)}%)")
                    return status_data
                else:
                    logger.warning(f"🔍 Пустой ответ от FAL API для {request_id}")
                    return None
                    
            except Exception as api_error:
                logger.error(f"🔍 Ошибка API FAL при получении статуса {request_id}: {api_error}")
                
                # Возвращаем error статус
                error_status = {
                    "status": "error",
                    "message": str(api_error),
                    "request_id": request_id,
                    "endpoint": endpoint
                }
                
                # ✅ Кешируем ошибку на короткое время (1 минута)
                await cache_service.cache_fal_status(request_id, error_status, ttl=60)
                
                return error_status
            
        except Exception as e:
            logger.exception(f"🔍 Общая ошибка получения статуса FAL AI {request_id}: {e}")
            return None
    
    async def submit_training(
        self,
        user_id: UUID,
        avatar_id: UUID,
        data_url: str,
        training_config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Отправляет задачу на обучение в FAL AI
        
        Args:
            user_id: ID пользователя
            avatar_id: ID аватара
            data_url: URL архива с фотографиями
            training_config: Конфигурация обучения
            
        Returns:
            Optional[str]: request_id или None при ошибке
        """
        try:
            if not self.is_available():
                logger.warning("FAL клиент недоступен")
                return None
            
            # Тестовый режим
            if settings.AVATAR_TEST_MODE:
                mock_request_id = f"test_request_{avatar_id}_{user_id}"
                logger.info(f"🧪 [FAL TEST MODE] Симуляция отправки обучения: {mock_request_id}")
                
                # ✅ Кешируем начальный статус
                initial_status = {
                    "status": "queued",
                    "progress": 0,
                    "message": "Training queued (test mode)",
                    "request_id": mock_request_id,
                    "created_at": "2025-05-23T16:00:00Z"
                }
                await cache_service.cache_fal_status(mock_request_id, initial_status, ttl=300)
                
                return mock_request_id
            
            # Получаем тип обучения из конфигурации
            training_type = training_config.get("training_type", "portrait")
            
            logger.info(
                f"🚀 [FAL AI] Отправка обучения аватара {avatar_id}: "
                f"user_id={user_id}, training_type={training_type}"
            )
            
            # Формируем аргументы в зависимости от типа обучения
            if training_type == "portrait":
                # Портретное обучение через flux-lora-portrait-trainer
                arguments = {
                    "images_data_url": data_url,
                    "learning_rate": training_config.get("learning_rate", settings.FAL_PORTRAIT_LEARNING_RATE),
                    "steps": training_config.get("steps", settings.FAL_PORTRAIT_STEPS),
                    "multiresolution_training": training_config.get("multiresolution_training", settings.FAL_PORTRAIT_MULTIRESOLUTION),
                    "subject_crop": training_config.get("subject_crop", settings.FAL_PORTRAIT_SUBJECT_CROP),
                    "create_masks": training_config.get("create_masks", settings.FAL_PORTRAIT_CREATE_MASKS)
                }
                
                # Добавляем trigger_phrase если указан
                if training_config.get("trigger_phrase"):
                    arguments["trigger_phrase"] = training_config["trigger_phrase"]
                
                endpoint = "fal-ai/flux-lora-portrait-trainer"
                
            else:  # style
                # Стилевое обучение через flux-pro-trainer
                arguments = {
                    "data_url": data_url,
                    "mode": training_config.get("mode", "style"),
                    "finetune_comment": format_finetune_comment(user_id, avatar_id),
                    "iterations": training_config.get("iterations", 1000),
                    "priority": training_config.get("priority", "quality"),
                    "captioning": training_config.get("captioning", "fast"),
                    "trigger_word": training_config.get("trigger_word") or generate_trigger_word(),
                    "lora_rank": training_config.get("lora_rank", 16),
                    "finetune_type": training_config.get("finetune_type", "lora"),
                }
                
                endpoint = "fal-ai/flux-pro-trainer"
            
            # Добавляем webhook URL если настроен
            webhook_url = training_config.get("webhook_url") or settings.FAL_WEBHOOK_URL
            
            logger.info(f"🚀 [FAL AI] Отправка на {endpoint}: {arguments}")
            
            # Отправляем задачу на обучение (НЕ ЖДЕМ РЕЗУЛЬТАТ!)
            handler = await self.fal_client.submit_async(
                endpoint,
                arguments=arguments,
                webhook_url=webhook_url
            )
            
            request_id = handler.request_id
            
            logger.info(f"✅ [FAL AI] Задача отправлена, request_id: {request_id}")
            
            # ✅ Кешируем начальный статус
            initial_status = {
                "status": "queued",
                "progress": 0,
                "message": "Training submitted successfully",
                "request_id": request_id,
                "endpoint": endpoint,
                "training_type": training_type,
                "submitted_at": "2025-05-23T16:00:00Z"
            }
            await cache_service.cache_fal_status(request_id, initial_status, ttl=300)
            
            return request_id
            
        except Exception as e:
            logger.exception(f"🚀 [FAL AI] Ошибка отправки задачи на обучение: {e}")
            return None
    
    async def get_training_result(self, request_id: str, training_type: str = "portrait") -> Optional[Dict[str, Any]]:
        """
        Получает результат обучения от FAL AI с кешированием
        
        Args:
            request_id: ID запроса
            training_type: Тип обучения
            
        Returns:
            Optional[Dict[str, Any]]: Результат обучения или None при ошибке
        """
        try:
            if not self.is_available():
                logger.warning("FAL клиент недоступен")
                return None
            
            # Тестовый режим
            if settings.AVATAR_TEST_MODE:
                mock_result = {
                    "status": "completed",
                    "diffusers_lora_file": "https://example.com/test_lora.safetensors",
                    "config_file": "https://example.com/test_config.json",
                    "message": "Training completed successfully (test mode)",
                    "request_id": request_id
                }
                
                # ✅ Кешируем мок результат
                await cache_service.cache_fal_status(request_id, mock_result, ttl=3600)
                
                return mock_result
            
            # Определяем endpoint
            if training_type == "portrait":
                endpoint = "fal-ai/flux-lora-portrait-trainer"
            else:  # style
                endpoint = "fal-ai/flux-pro-trainer"
            
            logger.info(f"📥 [FAL AI] Получение результата {request_id} с {endpoint}")
            
            # Получаем результат через FAL API
            result = await self.fal_client.result_async(endpoint, request_id)
            
            if result:
                # ✅ Кешируем результат (финальные результаты на час)
                await cache_service.cache_fal_status(request_id, result, ttl=3600)
                
                logger.info(f"📥 [FAL AI] Результат получен для {request_id}")
                return result 
            else:
                logger.warning(f"📥 [FAL AI] Пустой результат для {request_id}")
                return None
            
        except Exception as e:
            logger.exception(f"📥 [FAL AI] Ошибка получения результата {request_id}: {e}")
            return None 