"""
Основной файл менеджера галереи
Обратная совместимость с модульной структурой
"""

# Импортируем из новой модульной структуры
from .management.main import GalleryManager as GalleryManagerMain
from .management.favorites import FavoritesManager
from .management.deletion import DeletionManager
from .management.regeneration import RegenerationManager
from .management.stats import GalleryStatsManager
from .management.prompt_viewer import PromptViewer

# Создаем основной класс с делегированием к модулям
class GalleryManager(GalleryManagerMain):
    """Основной менеджер галереи с обратной совместимостью"""
    
    def __init__(self):
        super().__init__()
        self.deletion_manager = DeletionManager()
        self.regeneration_manager = RegenerationManager()
        self.stats_manager = GalleryStatsManager()
    
    async def request_delete_confirmation(self, callback):
        """Запрашивает подтверждение удаления (делегирует к DeletionManager)"""
        await self.deletion_manager.request_delete_confirmation(callback)
    
    async def regenerate_image(self, callback):
        """Повторная генерация изображения (делегирует к RegenerationManager)"""
        await self.regeneration_manager.regenerate_image(callback)
    
    async def show_gallery_stats(self, callback):
        """Показывает статистику галереи (делегирует к GalleryStatsManager)"""
        await self.stats_manager.show_gallery_stats(callback)

# Экспортируем для обратной совместимости
__all__ = [
    "GalleryManager", 
    "FavoritesManager", 
    "DeletionManager", 
    "RegenerationManager",
    "GalleryStatsManager",
    "PromptViewer"
] 