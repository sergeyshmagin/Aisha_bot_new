"""
🎯 Основной менеджер галереи изображений
Рефакторенная версия с модульной архитектурой  
"""
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.shared.handlers.base_handler import BaseHandler
from app.core.logger import get_logger

from .favorites import FavoritesManager
from .deletion import DeletionManager 
from .regeneration import RegenerationManager
from .stats import GalleryStatsManager
# from .prompt_viewer import PromptViewer  # LEGACY - заменен на единый PromptDisplayService

logger = get_logger(__name__)


class GalleryManager(BaseHandler):
    """🎯 Основной менеджер галереи (рефакторенный)"""
    
    def __init__(self):
        # Модульные компоненты
        self.favorites_manager = FavoritesManager()
        self.deletion_manager = DeletionManager()
        self.regeneration_manager = RegenerationManager()
        self.stats_manager = GalleryStatsManager()
        # self.prompt_viewer = PromptViewer()  # LEGACY - заменен на PromptDisplayService
    
    async def show_gallery(self, callback: CallbackQuery, state: FSMContext):
        """Показывает галерею (делегирует в GalleryViewer)"""
        from ..viewer import GalleryViewer
        
        gallery_viewer = GalleryViewer()
        await gallery_viewer.show_gallery_main(callback, state)
    
    async def toggle_favorite(self, callback: CallbackQuery):
        """Переключение избранного (делегирует в FavoritesManager)"""
        await self.favorites_manager.toggle_favorite(callback)
    
    async def delete_image(self, callback: CallbackQuery):
        """Удаление изображения (делегирует в DeletionManager)"""
        await self.deletion_manager.delete_image(callback)
    
    async def regenerate_image(self, callback: CallbackQuery):
        """Повторная генерация (делегирует в RegenerationManager)"""
        await self.regeneration_manager.regenerate_image(callback)
    
    async def show_full_prompt(self, callback: CallbackQuery):
        """Показ полного промпта (использует единый PromptDisplayService)"""
        from app.utils.prompt_display import prompt_display_service
        await prompt_display_service.show_full_prompt(callback, return_callback="my_gallery")
    
    async def show_gallery_stats(self, callback: CallbackQuery):
        """Показ статистики галереи (делегирует в GalleryStatsManager)"""
        await self.stats_manager.show_gallery_stats(callback) 