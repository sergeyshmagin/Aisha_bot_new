"""
Модели данных и конфигурация для FAL Training Service
Выделено из app/services/avatar/fal_training_service.py для соблюдения правила ≤500 строк
"""
from typing import Dict, Any, Optional
from uuid import UUID
from dataclasses import dataclass

from app.core.config import settings@dataclass
class TrainingConfig:
    """Конфигурация обучения аватара"""
    avatar_id: UUID
    training_type: str  # "portrait" или "style"
    training_data_url: str
    user_preferences: Optional[Dict] = None
    
    def get_quality_preset(self) -> str:
        """Получает пресет качества из пользовательских настроек"""
        if not self.user_preferences:
            return "balanced"
        return self.user_preferences.get("quality", "balanced")@dataclass
class TrainingRequest:
    """Данные запроса на обучение"""
    request_id: str
    avatar_id: UUID
    training_type: str
    config: Dict[str, Any]
    webhook_url: Optional[str] = Noneclass FALConfigManager:
    """Менеджер конфигурации FAL AI"""
    
    @staticmethod
    def get_quality_preset(quality: str) -> Dict[str, Any]:
        """Возвращает настройки качества из конфигурации"""
        presets = {
            "fast": settings.FAL_PRESET_FAST,
            "balanced": settings.FAL_PRESET_BALANCED,
            "quality": settings.FAL_PRESET_QUALITY
        }
        return presets.get(quality, settings.FAL_PRESET_BALANCED)
    
    @staticmethod
    def get_training_type_info(training_type: str) -> Dict[str, Any]:
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
    
    @staticmethod
    def get_config_summary(test_mode: bool, webhook_url: str, fal_client_available: bool) -> Dict[str, Any]:
        """Возвращает сводку конфигурации сервиса"""
        return {
            "test_mode": test_mode,
            "webhook_url": webhook_url,
            "fal_client_available": fal_client_available,
            "api_key_configured": bool(settings.FAL_API_KEY),
            "supported_training_types": ["portrait", "style"],
            "quality_presets": ["fast", "balanced", "quality"]
        }class WebhookURLBuilder:
    """Построитель URL для webhook"""
    
    @staticmethod
    def build_webhook_url(base_webhook_url: str, training_type: str) -> Optional[str]:
        """
        Формирует URL webhook с учетом типа обучения
        Теперь использует новый API сервер с SSL
        """
        from app.core.logger import get_logger
        logger = get_logger(__name__)
        
        logger.info(f"🔗 ФОРМИРОВАНИЕ WEBHOOK URL:")
        logger.info(f"   Training type: {training_type}")
        logger.info(f"   Base webhook URL: {base_webhook_url}")
        
        if not base_webhook_url:
            logger.warning(f"   ❌ Base webhook URL пустой!")
            return None
            
        # Используем новый endpoint API сервера
        base_url = "https://aibots.kz:8443/api/v1/avatar/status_update"
        logger.info(f"   Используем base_url: {base_url}")
        
        # Добавляем параметр типа обучения
        separator = "&" if "?" in base_url else "?"
        final_url = f"{base_url}{separator}training_type={training_type}"
        
        logger.info(f"   Separator: '{separator}'")
        logger.info(f"   ✅ Итоговый webhook URL: {final_url}")
        
        return final_url
