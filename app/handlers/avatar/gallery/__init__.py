"""
Модуль галереи аватаров
Рефакторинг app/handlers/avatar/gallery.py (663 строки → модули)
"""
from .main_handler import GalleryHandler
from .avatar_cards import AvatarCardsHandler
from .photo_gallery import PhotoGalleryHandler
from .avatar_actions import AvatarActionsHandler
from .keyboards import GalleryKeyboards
from .models import GalleryCache

# Создаем экземпляр и router для совместимости
gallery_handler = GalleryHandler()
router = gallery_handler.router

# Регистрируем обработчики синхронно
gallery_handler._register_handlers_sync()

__all__ = [
    "GalleryHandler",
    "router",
    "gallery_handler",
    "AvatarCardsHandler", 
    "PhotoGalleryHandler",
    "AvatarActionsHandler",
    "GalleryKeyboards",
    "GalleryCache"
] 