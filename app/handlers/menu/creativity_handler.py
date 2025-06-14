"""
Обработчик раздела "Творчество"

Управляет созданием контента:
- Фото (аватары и Imagen4)
- Видео (различные платформы)

Переиспользует существующие обработчики для максимальной совместимости.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.keyboards.menu.creativity import get_creativity_menu, get_photo_menu, get_video_menu_v2
from app.core.logger import get_logger
from app.shared.handlers.base_handler import BaseHandler
from app.core.di import get_user_service

logger = get_logger(__name__)


class CreativityHandler(BaseHandler):
    """
    Обработчик раздела творчества
    
    Функции:
    - Показ меню творчества
    - Навигация по разделам фото и видео
    - Интеграция с существующими обработчиками
    """
    
    def __init__(self):
        super().__init__()
        self.router = Router()
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрация обработчиков"""
        # Новые callback обработчики
        self.router.callback_query.register(self.show_creativity_menu, F.data == "creativity_menu")
        self.router.callback_query.register(self.show_photo_menu, F.data == "photo_menu")
        self.router.callback_query.register(self.show_video_menu, F.data == "video_menu")
        
        # LEGACY: Поддержка старых callback_data
        self.router.callback_query.register(self.show_creativity_menu, F.data == "ai_creativity_menu")
        self.router.callback_query.register(self.show_photo_menu, F.data == "images_menu")
        
        # Обработчики для фото меню
        self.router.callback_query.register(self.show_avatar_generation_menu, F.data == "avatar_generation_menu")
        self.router.callback_query.register(self.start_imagen4_generation, F.data == "imagen4_generation")
        self.router.callback_query.register(self.show_video_generation_stub, F.data == "video_generation_stub")
        
        # Обработчики для видео меню
        self.router.callback_query.register(self.start_hedra_video, F.data == "hedra_video")
        self.router.callback_query.register(self.start_kling_video, F.data == "kling_video")
        self.router.callback_query.register(self.start_weo3_video, F.data == "weo3_video")
        self.router.callback_query.register(self.show_my_videos, F.data == "my_videos")
    
    async def get_user_avatar_photos_count(self, user_id: int) -> int:
        """Получает количество фото с аватаром пользователя"""
        try:
            async with get_user_service() as user_service:
                # Здесь будет логика подсчета фото с аватарами из галереи
                # Пока возвращаем 0, логику можно будет добавить позже
                return 0
        except Exception as e:
            logger.exception(f"Ошибка получения количества фото с аватаром пользователя {user_id}: {e}")
            return 0
    
    async def get_user_imagen_photos_count(self, user_id: int) -> int:
        """Получает количество фото по описанию пользователя"""
        try:
            async with get_user_service() as user_service:
                # Здесь будет логика подсчета фото Imagen4 из галереи
                # Пока возвращаем 0, логику можно будет добавить позже
                return 0
        except Exception as e:
            logger.exception(f"Ошибка получения количества фото Imagen пользователя {user_id}: {e}")
            return 0
    
    async def get_user_avatars_count(self, user_id: int) -> int:
        """Получает количество аватаров пользователя"""
        try:
            from app.core.di import get_avatar_service
            async with get_avatar_service() as avatar_service:
                # Получаем аватары пользователя (как в меню аватаров)
                avatars = await avatar_service.get_user_avatars_with_photos(user_id)
                return len(avatars)
        except Exception as e:
            logger.exception(f"Ошибка получения количества аватаров пользователя {user_id}: {e}")
            return 0
    
    async def get_user_videos_count(self, user_id: int) -> int:
        """Получает количество видео пользователя"""
        try:
            async with get_user_service() as user_service:
                # Здесь будет логика подсчета видео
                # Пока возвращаем 0, логику можно будет добавить позже
                return 0
        except Exception as e:
            logger.exception(f"Ошибка получения количества видео пользователя {user_id}: {e}")
            return 0
    
    async def show_creativity_menu(self, call: CallbackQuery, state: FSMContext):
        """
        🎨 Показывает меню творчества
        
        Основные направления:
        - Фото (создание изображений)
        - Видео (создание видеороликов)
        """
        await state.clear()
        
        menu_text = """🎨 **Творчество**

Создавайте уникальный контент с помощью ИИ:

📷 **Фото** - создание изображений
   • Фото с вашим лицом
   • Изображения по описанию
   • Видео из фото (скоро)

🎬 **Видео** - создание видеороликов
   • Hedra AI - говорящие портреты
   • Kling - креативные ролики
   • Weo3 - анимация изображений

Выберите направление:"""
        
        try:
            await self.safe_edit_message(
                call,
                menu_text,
                reply_markup=get_creativity_menu(),
                parse_mode="Markdown"
            )
            logger.debug("✅ Показано меню творчества")
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню творчества: {e}")
            await call.answer("❌ Ошибка загрузки меню", show_alert=True)
        
        await call.answer()
    
    async def show_photo_menu(self, call: CallbackQuery, state: FSMContext):
        """
        📷 Показывает меню фото
        
        Переиспользует существующую логику images_menu
        с обновленной навигацией
        """
        await state.clear()
        
        # Получаем пользователя
        user = await self.get_user_from_callback(call)
        if not user:
            return
        
        # Получаем количества разных типов фото и аватаров
        avatar_photos_count = await self.get_user_avatar_photos_count(user.id)
        imagen_photos_count = await self.get_user_imagen_photos_count(user.id)
        avatars_count = await self.get_user_avatars_count(user.id)
        
        menu_text = """📷 **Фото**

🎭 **Доступные технологии:**

📷 **Фото с аватаром** - используйте обученную на ваших фото модель
📝 **По описанию** - создание любых картинок через Imagen 4
🎭 **Мои аватары** - управление созданными образами
🖼️ **Мои фото** - все созданные изображения

Создавайте профессиональные снимки и художественные изображения!

Что выберете?"""
        
        try:
            await self.safe_edit_message(
                call,
                menu_text,
                reply_markup=get_photo_menu(
                    avatar_photos_count=avatar_photos_count,
                    imagen_photos_count=imagen_photos_count,
                    avatars_count=avatars_count
                ),
                parse_mode="Markdown"
            )
            logger.debug("✅ Показано меню фото")
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню фото: {e}")
            await call.answer("❌ Ошибка загрузки меню", show_alert=True)
        
        await call.answer()
    
    async def show_video_menu(self, call: CallbackQuery, state: FSMContext):
        """
        🎬 Показывает меню видео
        
        Переиспользует существующую логику video_menu
        с обновленной навигацией
        """
        await state.clear()
        
        # Получаем пользователя
        user = await self.get_user_from_callback(call)
        if not user:
            return
        
        # Получаем количество видео пользователя
        videos_count = await self.get_user_videos_count(user.id)
        
        menu_text = """🎬 **Видео**

🎭 **Доступные платформы:**

🎭 **Hedra AI** - создание говорящих портретов
🌟 **Kling** - генерация креативных роликов  
🎪 **Weo3** - анимация ваших изображений

Оживите ваши идеи с помощью ИИ!

Выберите платформу:"""
        
        try:
            await self.safe_edit_message(
                call,
                menu_text,
                reply_markup=get_video_menu_v2(videos_count=videos_count),
                parse_mode="Markdown"
            )
            logger.debug("✅ Показано меню видео")
            
        except Exception as e:
            logger.exception(f"Ошибка показа меню видео: {e}")
            await call.answer("❌ Ошибка загрузки меню", show_alert=True)
        
        await call.answer()
    
    async def show_avatar_generation_menu(self, call: CallbackQuery, state: FSMContext):
        """📷 Показывает меню генерации с аватаром"""
        from app.keyboards.main import get_avatar_generation_menu
        
        await state.clear()
        
        menu_text = """📷 **Фото со мной**

🎭 **Создавайте фото с вашим лицом:**

✍️ **Свой промпт** - опишите желаемую сцену
📷 **Генерация по фото** - загрузите референс для копирования стиля
🎨 **Выбрать стиль** - используйте готовые художественные стили

💡 **Для работы нужен обученный аватар**

Выберите способ создания:"""

        try:
            await self.safe_edit_message(
                call,
                menu_text,
                reply_markup=get_avatar_generation_menu(),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception(f"Ошибка меню аватара: {e}")
            await call.answer("❌ Ошибка загрузки меню", show_alert=True)
        
        await call.answer()
    
    async def start_imagen4_generation(self, call: CallbackQuery, state: FSMContext):
        """🎨 Imagen 4 Pro - генерация через Google Imagen4"""
        try:
            # Импортируем обработчик Imagen4
            from app.handlers.imagen4.imagen4_handler import imagen4_handler
            await imagen4_handler.show_prompt_input(call, state)
        except ImportError:
            await call.answer("🎨 Imagen 4 временно недоступен", show_alert=True)
        except Exception as e:
            logger.exception(f"Ошибка запуска Imagen4: {e}")
            await call.answer("❌ Ошибка запуска генерации", show_alert=True)
    
    async def show_video_generation_stub(self, call: CallbackQuery, state: FSMContext):
        """🎬 Заглушка для генерации видео"""
        await state.clear()
        
        stub_text = """🎬 **Видео генерация**

🚧 **В разработке**

Скоро здесь будут доступны:
• 🎭 Hedra AI - анимация лиц
• 🌟 Kling - создание видео по тексту
• 🎪 Weo3 - профессиональные ролики

📅 **Ожидаемый запуск:** В ближайших обновлениях

💡 **Пока что вы можете:**
• Создавать изображения с вашим образом
• Генерировать картинки по описанию"""

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data="photo_menu"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
            ]
        ])

        try:
            await self.safe_edit_message(
                call,
                stub_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.exception(f"Ошибка заглушки видео: {e}")
            await call.answer("❌ Ошибка загрузки", show_alert=True)
        
        await call.answer()
    
    async def start_hedra_video(self, call: CallbackQuery, state: FSMContext):
        """🎭 Hedra AI - говорящие портреты"""
        await call.answer("🎭 Hedra AI скоро будет доступен!", show_alert=True)
    
    async def start_kling_video(self, call: CallbackQuery, state: FSMContext):
        """🌟 Kling - кинематографическое видео"""
        await call.answer("🌟 Kling скоро будет доступен!", show_alert=True)
    
    async def start_weo3_video(self, call: CallbackQuery, state: FSMContext):
        """🎪 Weo3 - анимация изображений"""
        await call.answer("🎪 Weo3 скоро будет доступен!", show_alert=True)
    
    async def show_my_videos(self, call: CallbackQuery, state: FSMContext):
        """📁 Мои видео - управление созданными роликами"""
        await call.answer("📁 Раздел 'Мои видео' в разработке!", show_alert=True)


# Создаем экземпляр обработчика
creativity_handler = CreativityHandler()

# Экспортируем роутер для использования в router.py
router = creativity_handler.router 