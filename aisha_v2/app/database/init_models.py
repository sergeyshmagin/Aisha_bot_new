"""
Инициализация моделей базы данных
"""
from aisha_v2.app.database.base import Base, mapper_registry

# Импортируем все модели для регистрации
from aisha_v2.app.database.models import (
    User, UserBalance, UserState, Avatar, AvatarPhoto,
    UserTranscript, UserProfile, UserTranscriptCache
)

def init_models():
    """
    Инициализация всех моделей и их связей
    """
    # Конфигурируем все маппинги
    mapper_registry.configure()
    
    return mapper_registry
