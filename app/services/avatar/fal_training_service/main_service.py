"""
Основной сервис FAL Training Service - координатор
Выделено из app/services/avatar/fal_training_service.py для соблюдения правила ≤500 строк
"""
from typing import Dict, Any, Optional
from uuid import UUID

from app.core.config import settings
from app.core.logger import get_logger
from app.utils.avatar_utils import generate_trigger_word

from .models import TrainingConfig, FALConfigManager, WebhookURLBuilder
from .fal_client import FALClient
from .test_simulator import TestModeSimulator

logger = get_logger(__name__)class FALTrainingService:
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
        
        # Инициализируем компоненты
        self.fal_client = FALClient()
        self.test_simulator = TestModeSimulator(self.webhook_url)
        
        # Проверяем доступность FAL клиента
        if not self.test_mode and not self.fal_client.is_available():
            logger.warning("FAL клиент недоступен, переключение в тестовый режим")
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
                return await self.test_simulator.simulate_training(avatar_id, training_type)
            
            # Создаем конфигурацию обучения
            config = TrainingConfig(
                avatar_id=avatar_id,
                training_type=training_type,
                training_data_url=training_data_url,
                user_preferences=user_preferences
            )
            
            # Получаем настройки качества
            quality_preset = config.get_quality_preset()
            settings_preset = FALConfigManager.get_quality_preset(quality_preset)
            
            # Логируем настройки для отладки
            logger.info(f"🎯 Настройки обучения для {training_type}:")
            logger.info(f"   Quality preset: {quality_preset}")
            logger.info(f"   Settings preset: {settings_preset}")
            
            # Генерируем уникальный триггер
            trigger = f"TOK_{avatar_id.hex[:8]}"
            
            # Настраиваем webhook с типом обучения
            webhook_url = WebhookURLBuilder.build_webhook_url(self.webhook_url, training_type)
            
            # Выбираем модель и запускаем обучение
            if training_type == "portrait":
                # Для портретного типа используем настройки portrait
                portrait_settings = settings_preset["portrait"]
                result = await self.fal_client.train_portrait_model(
                    images_data_url=training_data_url,
                    trigger_phrase=trigger,
                    steps=portrait_settings["steps"],
                    learning_rate=portrait_settings["learning_rate"],
                    webhook_url=webhook_url
                )
                request_id = result
            else:  # style
                # Для художественного типа используем настройки general
                general_settings = settings_preset["general"]
                result = await self.fal_client.train_general_model(
                    images_data_url=training_data_url,
                    trigger_word=trigger,
                    iterations=general_settings["iterations"],
                    learning_rate=general_settings["learning_rate"],
                    priority=general_settings["priority"],
                    webhook_url=webhook_url,
                    avatar_id=avatar_id
                )
                request_id = result["request_id"]
            
            # 🔍 ЗАПУСКАЕМ МОНИТОРИНГ СТАТУСА как резервный механизм
            from .status_checker import status_checker
            await status_checker.start_status_monitoring(avatar_id, request_id, training_type)
            
            logger.info(f"🎨 {training_type.title()} обучение запущено для аватара {avatar_id}: {result}")
            logger.info(f"🔍 Запущен мониторинг статуса для request_id: {request_id}")
            
            return request_id
            
        except Exception as e:
            logger.exception(f"Ошибка запуска обучения аватара {avatar_id}: {e}")
            raise
    
    async def check_training_status(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """Проверяет статус обучения согласно документации FAL AI"""
        try:
            # 🧪 Тестовый режим
            if self.test_mode:
                return await self.test_simulator.simulate_status_check(request_id, training_type)
            
            # Реальная проверка через FAL AI
            return await self.fal_client.check_training_status(request_id, training_type)
                
        except Exception as e:
            logger.exception(f"Ошибка проверки статуса {request_id}: {e}")
            raise
    
    async def get_training_result(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """Получает результат обучения согласно документации FAL AI"""
        try:
            # 🧪 Тестовый режим
            if self.test_mode:
                return self.test_simulator.simulate_training_result(request_id, training_type)
            
            # Реальный результат через FAL AI
            return await self.fal_client.get_training_result(request_id, training_type)
                
        except Exception as e:
            logger.exception(f"Ошибка получения результата {request_id}: {e}")
            raise
    
    def get_training_type_info(self, training_type: str) -> Dict[str, Any]:
        """Возвращает информацию о типе обучения"""
        return FALConfigManager.get_training_type_info(training_type)
    
    def is_test_mode(self) -> bool:
        """Возвращает состояние тестового режима"""
        return self.test_mode
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Возвращает сводку конфигурации сервиса"""
        return FALConfigManager.get_config_summary(
            test_mode=self.test_mode,
            webhook_url=self.webhook_url,
            fal_client_available=self.fal_client.is_available()
        )
    
    # Методы для обратной совместимости
    def _get_quality_preset(self, quality: str) -> Dict[str, Any]:
        """Возвращает настройки качества из конфигурации (для совместимости)"""
        return FALConfigManager.get_quality_preset(quality)
    
    def _get_webhook_url(self, training_type: str) -> Optional[str]:
        """Формирует URL webhook с учетом типа обучения (для совместимости)"""
        return WebhookURLBuilder.build_webhook_url(self.webhook_url, training_type)
    
    async def _simulate_training(self, avatar_id: UUID, training_type: str) -> str:
        """Имитация обучения для тестового режима (для совместимости)"""
        return await self.test_simulator.simulate_training(avatar_id, training_type)
    
    async def _simulate_status_check(self, request_id: str, training_type: str) -> Dict[str, Any]:
        """Имитация проверки статуса для тестового режима (для совместимости)"""
        return await self.test_simulator.simulate_status_check(request_id, training_type)
    
    async def _train_portrait_model(
        self,
        images_data_url: str,
        trigger_phrase: str,
        steps: int,
        learning_rate: float,
        webhook_url: Optional[str] = None
    ) -> str:
        """Обучение портретной модели (для совместимости)"""
        return await self.fal_client.train_portrait_model(
            images_data_url, trigger_phrase, steps, learning_rate, webhook_url
        )
    
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
        """Обучение универсальной модели (для совместимости)"""
        # В тестовом режиме возвращаем мок результат
        if self.test_mode:
            return self.test_simulator.simulate_general_training_result(avatar_id, "style")
        
        return await self.fal_client.train_general_model(
            images_data_url, trigger_word, iterations, learning_rate, 
            priority, webhook_url, avatar_id
        )
