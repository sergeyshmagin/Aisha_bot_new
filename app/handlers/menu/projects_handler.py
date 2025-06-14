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
        
        # === ОБРАБОТЧИКИ ГАЛЕРЕИ ФОТО ===
        self.router.callback_query.register(
            self.handle_gallery_avatars,
            F.data == "gallery_avatars"
        )
        
        self.router.callback_query.register(
            self.handle_gallery_imagen,
            F.data == "gallery_imagen"
        )
        
        self.router.callback_query.register(
            self.handle_gallery_video,
            F.data == "gallery_video"
        )
        
        self.router.callback_query.register(
            self.handle_gallery_by_date,
            F.data == "gallery_by_date"
        )
        
        # === ОБРАБОТЧИКИ ИЗБРАННОГО ===
        self.router.callback_query.register(
            self.handle_favorites_avatars,
            F.data == "favorites_avatars"
        )
        
        self.router.callback_query.register(
            self.handle_favorites_images,
            F.data == "favorites_images"
        )
        
        self.router.callback_query.register(
            self.handle_favorites_videos,
            F.data == "favorites_videos"
        )
        
        self.router.callback_query.register(
            self.handle_favorites_collections,
            F.data == "favorites_collections"
        )
        
        # === ОБРАБОТЧИКИ ВИДЕО ===
        self.router.callback_query.register(
            self.handle_videos_by_date,
            F.data == "videos_by_date"
        )
        
        self.router.callback_query.register(
            self.handle_gallery_hedra_videos,
            F.data == "gallery_hedra_videos"
        )
        
        self.router.callback_query.register(
            self.handle_gallery_kling_videos,
            F.data == "gallery_kling_videos"
        )
        
        self.router.callback_query.register(
            self.handle_gallery_weo3_videos,
            F.data == "gallery_weo3_videos"
        )
        
        self.router.callback_query.register(
            self.handle_favorite_videos,
            F.data == "favorite_videos"
        )
        
        # === СТАТИСТИКА ===
        self.router.callback_query.register(
            self.handle_my_stats,
            F.data == "my_stats"
        )
        
        # === ПРОФИЛЬ ===
        self.router.callback_query.register(
            self.handle_my_gallery,
            F.data == "my_gallery"
        )
    
    async def show_projects_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает главное меню раздела 'Мои работы'"""
        try:
            await self.safe_edit_message(
                callback,
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
                callback,
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
                callback,
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
                callback,
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
    
    # === ОБРАБОТЧИКИ ГАЛЕРЕИ ФОТО ===
    
    async def handle_gallery_avatars(self, callback: CallbackQuery, state: FSMContext):
        """Галерея аватаров"""
        await state.clear()
        
        # Импортируем обработчик фильтров галереи
        from app.handlers.gallery.filter_handler import gallery_filter_handler
        
        # Устанавливаем фильтр по типу "avatar" и показываем галерею
        await gallery_filter_handler.show_gallery_with_type_filter(callback, state, "avatar")
    
    async def handle_gallery_imagen(self, callback: CallbackQuery, state: FSMContext):
        """Галерея Imagen"""
        await state.clear()
        
        # Импортируем обработчик фильтров галереи
        from app.handlers.gallery.filter_handler import gallery_filter_handler
        
        # Устанавливаем фильтр по типу "imagen4" и показываем галерею
        await gallery_filter_handler.show_gallery_with_type_filter(callback, state, "imagen4")
    
    async def handle_gallery_video(self, callback: CallbackQuery, state: FSMContext):
        """Галерея видео из фото"""
        await callback.answer("🎬 Видео из фото - в разработке!\n\nАнимированные изображения и видеоролики.", show_alert=True)
    
    async def handle_gallery_by_date(self, callback: CallbackQuery, state: FSMContext):
        """Галерея по дате"""
        await state.clear()
        
        # Импортируем обработчик фильтров галереи
        from app.handlers.gallery.filter_handler import gallery_filter_handler
        
        # Показываем меню фильтрации по дате
        await gallery_filter_handler.show_date_filter_menu(callback, state)
    
    # === ОБРАБОТЧИКИ ИЗБРАННОГО ===
    
    async def handle_favorites_avatars(self, callback: CallbackQuery, state: FSMContext):
        """Избранные аватары"""
        await callback.answer("👤 Избранные образы - в разработке!\n\nВаши любимые аватары и образы.", show_alert=True)
    
    async def handle_favorites_images(self, callback: CallbackQuery, state: FSMContext):
        """Избранные изображения"""
        await state.clear()
        
        # Пока показываем заглушку для избранного, функция будет добавлена позже
        await callback.answer("⭐ Избранные фото - в разработке!\n\nОтмеченные изображения в одном месте.", show_alert=True)
    
    async def handle_favorites_videos(self, callback: CallbackQuery, state: FSMContext):
        """Избранные видео"""
        await callback.answer("🎬 Избранные видео - в разработке!\n\nВаши любимые видеоролики.", show_alert=True)
    
    async def handle_favorites_collections(self, callback: CallbackQuery, state: FSMContext):
        """Избранные коллекции"""
        await callback.answer("🗂️ Коллекции - в разработке!\n\nТематические подборки ваших работ.", show_alert=True)
    
    # === ОБРАБОТЧИКИ ВИДЕО ===
    
    async def handle_videos_by_date(self, callback: CallbackQuery, state: FSMContext):
        """Видео по дате"""
        await callback.answer("📅 Видео по дате - в разработке!\n\nХронологический просмотр видеороликов.", show_alert=True)
    
    async def handle_gallery_hedra_videos(self, callback: CallbackQuery, state: FSMContext):
        """Видео Hedra AI"""
        await callback.answer("🎭 Hedra AI видео - в разработке!\n\nВсе говорящие аватары, созданные в Hedra.", show_alert=True)
    
    async def handle_gallery_kling_videos(self, callback: CallbackQuery, state: FSMContext):
        """Видео Kling"""
        await callback.answer("🌟 Kling видео - в разработке!\n\nКинематографические ролики платформы Kling.", show_alert=True)
    
    async def handle_gallery_weo3_videos(self, callback: CallbackQuery, state: FSMContext):
        """Видео Weo3"""
        await callback.answer("🎪 Weo3 видео - в разработке!\n\nКреативные ролики от Weo3.", show_alert=True)
    
    async def handle_favorite_videos(self, callback: CallbackQuery, state: FSMContext):
        """Избранные видео (дубликат)"""
        await callback.answer("⭐ Избранные видео - в разработке!\n\nВаши отмеченные видеоролики.", show_alert=True)
    
    # === СТАТИСТИКА ===
    
    async def handle_my_stats(self, callback: CallbackQuery, state: FSMContext):
        """Моя статистика"""
        await callback.answer("📊 Статистика творчества - в разработке!\n\nАналитика ваших работ и активности.", show_alert=True)
    
    # === ПРОФИЛЬ ===
    
    async def handle_my_gallery(self, callback: CallbackQuery, state: FSMContext):
        """Моя галерея - перенаправляем на настоящую галерею"""
        # Импортируем обработчик настоящей галереи
        from app.handlers.gallery.main_handler import handle_gallery_main
        await handle_gallery_main(callback, state)


# Создаем экземпляр обработчика
projects_handler = ProjectsHandler()

# Создаем роутер для экспорта
router = projects_handler.router

# Экспортируем callback обработчики
show_projects_menu_callback = projects_handler.show_projects_menu
show_all_photos_callback = projects_handler.show_all_photos
show_all_videos_callback = projects_handler.show_all_videos
show_favorites_callback = projects_handler.show_favorites 