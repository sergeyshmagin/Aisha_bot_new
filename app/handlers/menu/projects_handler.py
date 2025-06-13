"""
Обработчик раздела "Мои работы"

Управляет отображением всех созданных пользователем материалов:
- Фото (аватары и Imagen4)
- Видео (все платформы)
- Избранное
- Статистика
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.shared.handlers.base_handler import BaseHandler
from app.keyboards.menu.projects import (
    get_projects_menu, 
    get_all_photos_menu, 
    get_all_videos_menu,
    get_favorites_menu
)

logger = logging.getLogger(__name__)


class ProjectsHandler(BaseHandler):
    """Обработчик раздела 'Мои работы'"""
    
    def __init__(self):
        super().__init__()
        self.router = Router(name="projects_menu")
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует обработчики callback_data"""
        # Главное меню проектов
        self.router.callback_query.register(
            self.show_projects_menu,
            F.data == "projects_menu"
        )
        
        # Все фото
        self.router.callback_query.register(
            self.show_all_photos,
            F.data == "all_photos"
        )
        
        # Все видео
        self.router.callback_query.register(
            self.show_all_videos,
            F.data == "all_videos"
        )
        
        # Избранное
        self.router.callback_query.register(
            self.show_favorites,
            F.data == "favorites"
        )
    
    async def show_projects_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает главное меню раздела 'Мои работы'"""
        try:
            await self.safe_edit_message(
                callback.message,
                text=(
                    "🎭 <b>Мои работы</b>\n\n"
                    "Все ваши творческие результаты:\n\n"
                    "🖼️ <b>Все фото</b> - изображения и аватары\n"
                    "🎬 <b>Все видео</b> - видеоролики всех платформ\n"
                    "⭐ <b>Избранное</b> - ваши любимые работы\n"
                    "📊 <b>Статистика</b> - аналитика творчества"
                ),
                reply_markup=get_projects_menu(),
                parse_mode="HTML"
            )
            
            await callback.answer()
            logger.info(f"Показано меню проектов для пользователя {callback.from_user.id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе меню проектов: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def show_all_photos(self, callback: CallbackQuery, state: FSMContext):
        """Показывает меню всех фото"""
        try:
            await self.safe_edit_message(
                callback.message,
                text=(
                    "🖼️ <b>Все фото</b>\n\n"
                    "Ваши изображения по категориям:\n\n"
                    "📸 <b>Фото со мной</b> - аватары и портреты\n"
                    "🖼️ <b>По описанию</b> - Imagen4 генерации\n"
                    "🎬 <b>Видео из фото</b> - анимированные изображения\n"
                    "📅 <b>По дате</b> - хронологический просмотр"
                ),
                reply_markup=get_all_photos_menu(),
                parse_mode="HTML"
            )
            
            await callback.answer()
            logger.info(f"Показано меню всех фото для пользователя {callback.from_user.id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе меню всех фото: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def show_all_videos(self, callback: CallbackQuery, state: FSMContext):
        """Показывает меню всех видео"""
        try:
            await self.safe_edit_message(
                callback.message,
                text=(
                    "🎬 <b>Все видео</b>\n\n"
                    "Ваши видеоролики по платформам:\n\n"
                    "🎭 <b>Hedra AI</b> - говорящие аватары\n"
                    "🌟 <b>Kling</b> - кинематографические видео\n"
                    "🎪 <b>Weo3</b> - креативные ролики\n"
                    "📁 <b>Все видео</b> - полная коллекция"
                ),
                reply_markup=get_all_videos_menu(),
                parse_mode="HTML"
            )
            
            await callback.answer()
            logger.info(f"Показано меню всех видео для пользователя {callback.from_user.id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе меню всех видео: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
    
    async def show_favorites(self, callback: CallbackQuery, state: FSMContext):
        """Показывает меню избранного"""
        try:
            await self.safe_edit_message(
                callback.message,
                text=(
                    "⭐ <b>Избранное</b>\n\n"
                    "Ваши любимые работы:\n\n"
                    "👤 <b>Избранные образы</b> - лучшие аватары\n"
                    "🖼️ <b>Избранные фото</b> - отмеченные изображения\n"
                    "🎬 <b>Избранные видео</b> - любимые ролики\n"
                    "🗂️ <b>Коллекции</b> - тематические подборки"
                ),
                reply_markup=get_favorites_menu(),
                parse_mode="HTML"
            )
            
            await callback.answer()
            logger.info(f"Показано меню избранного для пользователя {callback.from_user.id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе меню избранного: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)


# Создаем экземпляр обработчика
projects_handler = ProjectsHandler()

# Создаем роутер для экспорта
router = projects_handler.router

# Экспортируем callback обработчики
show_projects_menu_callback = projects_handler.show_projects_menu
show_all_photos_callback = projects_handler.show_all_photos
show_all_videos_callback = projects_handler.show_all_videos
show_favorites_callback = projects_handler.show_favorites 