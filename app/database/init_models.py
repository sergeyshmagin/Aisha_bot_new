"""
Инициализация моделей базы данных
"""
from app.database.base import Base, mapper_registry

# Импортируем все модели для регистрации
from app.database.models.models import (
    User, UserState, Avatar, AvatarPhoto,
    UserTranscript, UserProfile, UserTranscriptCache
)

# Импортируем модели промо-кодов и баланса
from app.database.models.promokode import Promokode
from app.database.models.user_balance import UserBalance

# Импортируем модели генерации
from app.database.models.generation import (
    StyleCategory, StyleSubcategory, StyleTemplate, 
    ImageGeneration, UserFavoriteTemplate, GenerationStatus
)

def init_models():
    """
    Инициализация всех моделей и их связей
    """
    # Конфигурируем все маппинги
    mapper_registry.configure()
    
    return mapper_registry
