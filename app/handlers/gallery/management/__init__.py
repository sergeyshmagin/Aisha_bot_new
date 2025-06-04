"""
Модуль управления галереей изображений  
Обработка действий пользователя: избранное, удаление, повторение
"""

from .main import GalleryManager
from .favorites import FavoritesManager
from .deletion import DeletionManager
from .regeneration import RegenerationManager
from .stats import GalleryStatsManager
from .prompt_viewer import PromptViewer

__all__ = [
    "GalleryManager",
    "FavoritesManager",
    "DeletionManager", 
    "RegenerationManager",
    "GalleryStatsManager",
    "PromptViewer"
] 