"""
Модульная структура сервиса обучения аватаров
Рефакторинг app/services/avatar/training_service.py (618 строк → модули)
"""

# Основной сервис
from .main_service import AvatarTrainingService

# Компоненты
from .training_manager import TrainingManager
from .webhook_handler import WebhookHandler
from .progress_tracker import ProgressTracker
from .avatar_validator import AvatarValidator

# Модели
from .models import TrainingConfig, TrainingStatus

__all__ = [
    "AvatarTrainingService",
    "TrainingManager", 
    "WebhookHandler",
    "ProgressTracker",
    "AvatarValidator",
    "TrainingConfig",
    "TrainingStatus"
] 