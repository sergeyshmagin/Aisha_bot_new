"""
Центральный файл для импорта всех моделей базы данных.
Используется для автогенерации миграций Alembic.
"""

from app.database.base import Base

# Импортируем все модели для регистрации в метаданных
from app.database.models.models import (
    User, UserState, Avatar, AvatarPhoto,
    UserTranscript, UserProfile, UserTranscriptCache
)
from app.database.models.promokode import Promokode
from app.database.models.user_balance import UserBalance
from app.database.models.generation import (
    StyleCategory, StyleSubcategory, StyleTemplate, 
    ImageGeneration, UserFavoriteTemplate, GenerationStatus
)

# Базовый класс для всех моделей
__all__ = [
    "Base", "User", "UserState", "Avatar", "AvatarPhoto",
    "UserTranscript", "UserProfile", "UserTranscriptCache",
    "Promokode", "UserBalance", "StyleCategory", "StyleSubcategory", 
    "StyleTemplate", "ImageGeneration", "UserFavoriteTemplate", "GenerationStatus"
] 