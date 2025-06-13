"""
Модели базы данных
"""

# Импортируем основные модели
from app.database.models.models import *

# Импортируем модели генерации
from app.database.models.generation import *

# Импортируем модели настроек пользователя
from app.database.models.user_settings import UserSettings

from .user_balance import UserBalance
from .promokode import Promokode, PromokodeUsage, PromokodeType

__all__ = [
    # Основные модели пользователей и аватаров
    "User",
    "UserSettings", 
    "Avatar",
    "AvatarPhoto",
    "AvatarStatus",
    "AvatarGender",
    "AvatarType", 
    "AvatarTrainingType",
    "UserPhoto",
    "FALTrainingTask",
    "TranscriptRecord",
    "UserTranscript",
    "UserState",
    "Base",
    
    # Модели баланса и транзакций
    "UserBalance",
    
    # Модели промокодов
    "Promokode",
    "PromokodeUsage", 
    "PromokodeType",
    
    # Модели генерации изображений
    "ImageGeneration",
    "GenerationStatus",
    "StyleCategory", 
    "StyleTemplate",
]
