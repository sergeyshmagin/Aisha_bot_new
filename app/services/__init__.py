"""
Сервисы приложения
"""
from app.services.audio_processing.service import AudioService as AudioProcessingService
from app.services.avatar_db import AvatarService  # Соответствует best practices: avatar_db для БД, avatar/ для файлов
from app.services.images.service import ImageProcessingService
from app.services.storage import StorageService
from app.services.text_processing import TextProcessingService
from app.services.user import UserService

__all__ = [
    "AudioProcessingService",
    "AvatarService",
    "ImageProcessingService",
    "StorageService",
    "TextProcessingService",
    "UserService",
]
