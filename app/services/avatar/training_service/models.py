"""
Модели данных и конфигурация для сервиса обучения аватаров
Выделено из app/services/avatar/training_service.py для соблюдения правила ≤500 строк
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime


class TrainingStatus(Enum):
    """Статусы обучения от FAL AI"""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TrainingConfig:
    """Конфигурация обучения аватара"""
    learning_rate: float = 0.0001
    steps: int = 1000
    batch_size: int = 1
    resolution: int = 512
    trigger_word: Optional[str] = None
    custom_params: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует конфигурацию в словарь"""
        config = {
            "learning_rate": self.learning_rate,
            "steps": self.steps,
            "batch_size": self.batch_size,
            "resolution": self.resolution
        }
        
        if self.trigger_word:
            config["trigger_word"] = self.trigger_word
            
        if self.custom_params:
            config.update(self.custom_params)
            
        return config


@dataclass
class TrainingProgress:
    """Информация о прогрессе обучения"""
    avatar_id: str
    status: str
    progress: int
    created_at: Optional[datetime] = None
    training_started_at: Optional[datetime] = None
    training_completed_at: Optional[datetime] = None
    finetune_id: Optional[str] = None
    fal_request_id: Optional[str] = None
    training_duration_seconds: Optional[float] = None
    fal_status: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class WebhookData:
    """Данные webhook от FAL AI"""
    request_id: str
    status: str
    progress: int = 0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookData":
        """Создает WebhookData из словаря"""
        return cls(
            request_id=data.get("request_id", ""),
            status=data.get("status", ""),
            progress=data.get("progress", 0),
            message=data.get("message", ""),
            result=data.get("result")
        ) 