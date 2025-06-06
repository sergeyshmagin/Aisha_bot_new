"""
Основной файл просмотрщика галереи
Обратная совместимость с модульной структурой
"""

# Импортируем из новой модульной структуры
from .viewer.main import GalleryViewer as GalleryViewerMain
from .cache.ultra_fast_cache import UltraFastGalleryCache, ultra_gallery_cache
# from .management.prompt_viewer import PromptViewer  # LEGACY - заменен на PromptDisplayService

# Создаем основной класс с делегированием к модулям
class GalleryViewer(GalleryViewerMain):
    """Основной просмотрщик галереи с обратной совместимостью"""
    
    def __init__(self):
        super().__init__()
        # self.prompt_viewer = PromptViewer()  # LEGACY - заменен на PromptDisplayService
    
    async def show_full_prompt(self, callback):
        """Показывает полный промпт (использует единый PromptDisplayService)"""
        from app.utils.prompt_display import prompt_display_service
        await prompt_display_service.show_full_prompt(callback, return_callback="my_gallery")

# Экспортируем для обратной совместимости
__all__ = ["GalleryViewer", "UltraFastGalleryCache", "ultra_gallery_cache"] 