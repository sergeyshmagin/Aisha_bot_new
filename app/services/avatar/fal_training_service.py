"""
FAL AI Training Service - Сервис для обучения аватаров с автовыбором модели
Критическая реализация из плана avatar_implementation_plan.md
"""
import asyncio
import aiohttp
import json
import uuid
from typing import Dict, Any, Optional
from uuid import UUID

from app.core.config import settings
from app.core.logger import get_logger
from app.core.di import get_user_service, get_avatar_service
from app.utils.avatar_utils import (
    format_finetune_comment,
    generate_trigger_word,
    format_training_duration
)

logger = get_logger(__name__)

class FALTrainingService:
    """
    Сервис для обучения аватаров через FAL AI с автовыбором модели
    
    Поддерживает:
    - Портретный тип обучения (Flux LoRA Portrait Trainer) 
    - Художественный тип обучения (Flux Pro Trainer)
    - Полный тестовый режим для отладки без затрат
    - Webhook simulation для тестирования UX
    """
    
    def __init__(self):
        self.test_mode = settings.AVATAR_TEST_MODE
        self.webhook_url = settings.FAL_WEBHOOK_URL
        self.logger = logger
        
        # Импорты FAL клиентов (только в не-тестовом режиме)
        self.fal_client = None
        if not self.test_mode:
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
                    logger.warning("FAL_API_KEY/FAL_KEY не установлен, переключение в тестовый режим")
                    self.test_mode = True
            except ImportError:
                logger.warning("fal_client не установлен, работа только в тестовом режиме")
                self.test_mode = True
    
    async def start_avatar_training(
        self, 
        avatar_id: UUID,
        training_type: str,  # "portrait" или "style"
        training_data_url: str,
        user_preferences: Optional[Dict] = None
    ) -> str:
        """
        Запускает обучение аватара с автоматическим выбором оптимальной модели
        
        Args:
            avatar_id: ID аватара
            training_type: Тип обучения (portrait/style)
            training_data_url: URL к архиву с фотографиями
            user_preferences: Пользовательские настройки (speed/balanced/quality)
            
        Returns:
            request_id или finetune_id для отслеживания
        """
        try:
            # 🧪 ТЕСТОВЫЙ РЕЖИМ - имитация обучения без реальных запросов
            if self.test_mode:
                logger.info(f"🧪 ТЕСТ РЕЖИМ: Пропускаем отправку на обучение для аватара {avatar_id}, тип: {training_type}")
                return await self._simulate_training(avatar_id, training_type)
            
            # Получаем настройки качества
            quality_preset = user_preferences.get("quality", "balanced") if user_preferences else "balanced"
            settings_preset = self._get_quality_preset(quality_preset)
            
            # Генерируем уникальный триггер
            trigger = f"TOK_{avatar_id.hex[:8]}"
            
            # Настраиваем webhook с типом обучения
            webhook_url = self._get_webhook_url(training_type)
            
            if training_type == "portrait":
                # 🎭 ПОРТРЕТНЫЙ СТИЛЬ → Flux LoRA Portrait Trainer API
                preset = settings_preset["portrait"]
                
                result = await self._train_portrait_model(
                    images_data_url=training_data_url,
                    trigger_phrase=trigger,
                    steps=preset["steps"],
                    learning_rate=preset["learning_rate"],
                    webhook_url=webhook_url
                )
                
                logger.info(f"🎭 Портретное обучение запущено для аватара {avatar_id}: {result}")
                return result
                
            else:
                # 🎨 ХУДОЖЕСТВЕННЫЙ СТИЛЬ → Flux Pro Trainer API
                preset = settings_preset["general"]
                
                # Используем оптимизированный trigger_word
                trigger = generate_trigger_word(str(avatar_id))
                
                result = await self._train_general_model(
                    images_data_url=training_data_url,
                    trigger_word=trigger,
                    iterations=preset["iterations"],
                    learning_rate=preset["learning_rate"],
                    priority=preset.get("priority", "quality"),
                    webhook_url=webhook_url,
                    avatar_id=avatar_id
                )
                
                logger.info(f"🎨 Художественное обучение запущено для аватара {avatar_id}: {result}")
                return result.get("finetune_id") or result.get("request_id")
                
        except Exception as e:
            logger.exception(f"Ошибка при запуске обучения аватара {avatar_id}: {e}")
            raise
    
    async def _simulate_training(self, avatar_id: UUID, training_type: str) -> str:
        """
        🧪 Имитация обучения для тестового режима
        """
        mock_request_id = f"test_{avatar_id.hex[:8]}_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"🧪 ТЕСТ РЕЖИМ: Имитация обучения {training_type} для аватара {avatar_id}")
        logger.info(f"🧪 Сгенерирован тестовый request_id: {mock_request_id}")
        
        # Имитируем задержку
        await asyncio.sleep(1)
        
        # Через некоторое время можно вызвать webhook с тестовыми данными
        if self.webhook_url and hasattr(settings, 'FAL_ENABLE_WEBHOOK_SIMULATION') and settings.FAL_ENABLE_WEBHOOK_SIMULATION:
            asyncio.create_task(self._simulate_webhook_callback(
                mock_request_id, 
                avatar_id, 
                training_type
            ))
        
        return mock_request_id
    
    async def _simulate_webhook_callback(
        self, 
        request_id: str, 
        avatar_id: UUID, 
        training_type: str
    ):
        """
        🧪 Имитация webhook callback для тестового режима
        """
        # Получаем длительность тестового обучения
        duration = getattr(settings, 'FAL_MOCK_TRAINING_DURATION', 30)
        
        logger.info(f"🧪 Имитация обучения {training_type}, завершение через {duration} секунд")
        
        # Задержка перед "завершением" обучения
        await asyncio.sleep(duration)
        
        webhook_data = {
            "request_id": request_id,
            "avatar_id": str(avatar_id),
            "training_type": training_type,
            "status": "completed",
            "result": {
                "test_mode": True,
                "mock_model_url": f"https://test.example.com/models/{request_id}.safetensors",
                "diffusers_lora_file": {
                    "url": f"https://test.example.com/models/{request_id}.safetensors",
                    "file_name": f"test_model_{training_type}.safetensors"
                }
            }
        }
        
        try:
            webhook_url = self._get_webhook_url(training_type)
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=webhook_data) as response:
                    logger.info(f"🧪 Тестовый webhook отправлен: {response.status}")
        except Exception as e:
            logger.warning(f"🧪 Ошибка отправки тестового webhook: {e}")
    
    async def _train_portrait_model(
        self,
        images_data_url: str,
        trigger_phrase: str,
        steps: int,
        learning_rate: float,
        webhook_url: Optional[str] = None
    ) -> str:
        """
        Обучение портретной модели через Flux LoRA Portrait Trainer
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
        
        # Запускаем обучение с webhook
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.fal_client.submit(
                "fal-ai/flux-lora-portrait-trainer",
                arguments=config,
                webhook_url=webhook_url
            )
        )
        
        return result.request_id
    
    async def _train_general_model(
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
        """
        # ИСПРАВЛЕНИЕ: В тестовом режиме не проверяем FAL клиент
        if not self.test_mode and not self.fal_client:
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
        
        # Конфигурация для flux-pro-trainer с оптимизированными параметрами
        config = {
            "data_url": images_data_url,
            "mode": settings.FAL_PRO_MODE,
            "iterations": iterations,
            "learning_rate": learning_rate,
            "priority": priority,
            "finetune_type": settings.FAL_PRO_FINETUNE_TYPE,
            "lora_rank": settings.FAL_PRO_LORA_RANK,
            "captioning": settings.FAL_PRO_CAPTIONING,
            "trigger_word": trigger_word,
            "finetune_comment": finetune_comment,
        }
        
        if webhook_url:
            config["webhook_url"] = webhook_url
        
        logger.info(f"🎨 Запуск flux-pro-trainer: {finetune_comment}, trigger: {trigger_word}")
        logger.info(f"🎨 Параметры: iterations={iterations}, lr={learning_rate}, priority={priority}")
        
        # ИСПРАВЛЕНИЕ: В тестовом режиме возвращаем мок результат
        if self.test_mode:
            mock_request_id = f"test_{avatar_id.hex[:8] if avatar_id else 'unknown'}_{uuid.uuid4().hex[:8]}"
            logger.info(f"🧪 ТЕСТ РЕЖИМ: Возвращаем мок request_id: {mock_request_id}")
            return {
                "finetune_id": mock_request_id,
                "request_id": mock_request_id
            }
        
        # Запускаем обучение
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.fal_client.submit(
                "fal-ai/flux-pro-trainer",
                arguments=config
            )
        )
        
        return {
            "finetune_id": result.request_id,
            "request_id": result.request_id
        }
    
    def _get_webhook_url(self, training_type: str) -> Optional[str]:
        """
        Формирует URL webhook с учетом типа обучения
        Теперь использует новый API сервер с SSL
        """
        if not self.webhook_url:
            return None
            
        # Используем новый endpoint API сервера
        base_url = "https://aibots.kz:8443/api/v1/avatar/status_update"
        
        # Добавляем параметр типа обучения
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}training_type={training_type}"
    
    async def check_training_status(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """Проверяет статус обучения"""
        try:
            # 🧪 Тестовый режим
            if self.test_mode:
                return await self._simulate_status_check(request_id, training_type)
            
            if not self.fal_client:
                raise RuntimeError("FAL client не инициализирован")
            
            # Проверяем статус через FAL API
            if training_type == "portrait":
                endpoint = "fal-ai/flux-lora-portrait-trainer"
            else:
                endpoint = "fal-ai/flux-pro-trainer"
            
            status = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.fal_client.status(endpoint, request_id, with_logs=True)
            )
            
            return status
                
        except Exception as e:
            logger.exception(f"Ошибка проверки статуса {request_id}: {e}")
            raise
    
    async def _simulate_status_check(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """🧪 Имитация проверки статуса для тестового режима"""
        
        # Простая логика: если запрос "новый" - в процессе, если "старый" - завершен
        import time
        current_time = time.time()
        
        # Для тестовых request_id вычисляем "возраст"
        if request_id.startswith("test_"):
            # Используем последние 8 символов как псевдо-timestamp
            mock_duration = getattr(settings, 'FAL_MOCK_TRAINING_DURATION', 30)
            
            # Имитируем прогресс
            elapsed = min(mock_duration, 25)  # Максимум 25 секунд для демо
            progress = min(100, int((elapsed / mock_duration) * 100))
            
            if progress < 100:
                return {
                    "status": "in_progress",
                    "progress": progress,
                    "logs": [f"🧪 Тестовое обучение {training_type} в процессе... {progress}%"],
                    "request_id": request_id
                }
            else:
                return {
                    "status": "completed",
                    "progress": 100,
                    "logs": [f"🧪 Тестовое обучение {training_type} завершено!"],
                    "request_id": request_id
                }
        
        # Для неизвестных request_id
        return {
            "status": "unknown",
            "progress": 0,
            "logs": [f"🧪 Неизвестный request_id: {request_id}"],
            "request_id": request_id
        }
    
    async def get_training_result(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """Получает результат обучения"""
        try:
            # 🧪 Тестовый режим
            if self.test_mode:
                return {
                    "test_mode": True,
                    "request_id": request_id,
                    "training_type": training_type,
                    "mock_model_url": f"https://test.example.com/models/{request_id}.safetensors",
                    "diffusers_lora_file": {
                        "url": f"https://test.example.com/models/{request_id}.safetensors",
                        "file_name": f"test_model_{training_type}.safetensors"
                    }
                }
            
            if not self.fal_client:
                raise RuntimeError("FAL client не инициализирован")
            
            # Получаем результат через FAL API
            if training_type == "portrait":
                endpoint = "fal-ai/flux-lora-portrait-trainer"
            else:
                endpoint = "fal-ai/flux-pro-trainer"
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.fal_client.result(endpoint, request_id)
            )
            
            return result
                
        except Exception as e:
            logger.exception(f"Ошибка получения результата {request_id}: {e}")
            raise
    
    def _get_quality_preset(self, quality: str) -> Dict[str, Any]:
        """Возвращает настройки качества из конфигурации"""
        presets = {
            "fast": settings.FAL_PRESET_FAST,
            "balanced": settings.FAL_PRESET_BALANCED,
            "quality": settings.FAL_PRESET_QUALITY
        }
        return presets.get(quality, settings.FAL_PRESET_BALANCED)
    
    def get_training_type_info(self, training_type: str) -> Dict[str, Any]:
        """Возвращает информацию о типе обучения"""
        
        info = {
            "portrait": {
                "name": "Портретный",
                "description": "Специально для фотографий людей",
                "speed": "⭐⭐⭐⭐ (3-15 минут)",
                "quality_portraits": "⭐⭐⭐⭐⭐",
                "best_for": ["Селфи", "Портреты", "Фото людей"],
                "technology": "Flux LoRA Portrait Trainer"
            },
            "style": {
                "name": "Художественный", 
                "description": "Универсальный для любого контента",
                "speed": "⭐⭐⭐ (5-30 минут)",
                "quality_portraits": "⭐⭐⭐⭐",
                "best_for": ["Стили", "Объекты", "Архитектура"],
                "technology": "Flux Pro Trainer"
            }
        }
        
        return info.get(training_type, info["portrait"])
    
    def is_test_mode(self) -> bool:
        """Возвращает состояние тестового режима"""
        return self.test_mode
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Возвращает сводку конфигурации сервиса"""
        return {
            "test_mode": self.test_mode,
            "webhook_url": self.webhook_url,
            "fal_client_available": self.fal_client is not None,
            "api_key_configured": bool(settings.FAL_API_KEY),
            "supported_training_types": ["portrait", "style"],
            "quality_presets": ["fast", "balanced", "quality"]
        } 