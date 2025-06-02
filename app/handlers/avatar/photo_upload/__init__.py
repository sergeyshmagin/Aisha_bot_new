"""
Модуль загрузки фотографий для аватаров
Рефакторинг app/handlers/avatar/photo_upload.py (924 строки → модули)
"""
from .main_handler import PhotoUploadHandler
from .upload_handler import UploadHandler
from .gallery_handler import GalleryHandler
from .progress_handler import ProgressHandler
from .models import PhotoUploadState

# Создаем экземпляр и router для совместимости
photo_handler = PhotoUploadHandler()
router = photo_handler.router

# Регистрируем обработчики синхронно
photo_handler._register_handlers_sync()

__all__ = [
    "PhotoUploadHandler",
    "router",
    "photo_handler",
    "UploadHandler", 
    "GalleryHandler",
    "ProgressHandler",
    "PhotoUploadState"
]
