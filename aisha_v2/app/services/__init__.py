"""
Сервисы приложения
"""
from aisha_v2.app.services.audio.service import AudioProcessingService
from aisha_v2.app.services.avatar_db import AvatarService  # Соответствует best practices: avatar_db для БД, avatar/ для файлов
from aisha_v2.app.services.images.service import ImageProcessingService
from aisha_v2.app.services.storage import StorageService
from aisha_v2.app.services.text_processing import TextProcessingService
from aisha_v2.app.services.user import UserService

__all__ = [
    "AudioProcessingService",
    "AvatarService",
    "ImageProcessingService",
    "StorageService",
    "TextProcessingService",
    "UserService",
]
