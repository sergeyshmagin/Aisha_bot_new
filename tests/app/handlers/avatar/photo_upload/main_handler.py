"""
Основной обработчик загрузки фотографий
Рефакторинг app/handlers/avatar/photo_upload.py (924 строки → модули)
Объединяет UploadHandler, GalleryHandler, ProgressHandler
"""
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from uuid import UUID
import logging

from app.handlers.state import AvatarStates
from app.core.di import get_avatar_service
from .upload_handler import UploadHandler
from .gallery_handler import PhotoUploadGalleryHandler
from .progress_handler import ProgressHandler
from .models import PhotoUploadConfig

logger = logging.getLogger(__name__)

class PhotoUploadHandler:
    """
    Основной обработчик для загрузки фотографий аватаров.
    Объединяет модули: UploadHandler, GalleryHandler, ProgressHandler
    """
    
    def __init__(self):
        """Инициализация обработчика загрузки фотографий"""
        self.router = Router()
        self.config = PhotoUploadConfig()
        
        # Инициализируем модули
        self.upload_handler = UploadHandler()
        self.gallery_handler = PhotoUploadGalleryHandler()
        self.progress_handler = ProgressHandler()
        
        logger.info("Инициализирован PhotoUploadHandler с модулями")

    def _register_handlers_sync(self):
        """Синхронная регистрация обработчиков для загрузки фотографий"""
        logger.info("Регистрация обработчиков загрузки фотографий")
        
        # Обработчики callback'ов
        self.router.callback_query.register(
            self.start_photo_upload,
            F.data == "start_photo_upload"
        )
        
        self.router.callback_query.register(
            self.show_photo_gallery,
            F.data == "show_photo_gallery"
        )
        
        self.router.callback_query.register(
            self.handle_back_to_upload,
            F.data == "back_to_upload"
        )
        
        self.router.callback_query.register(
            self.handle_gallery_nav_prev,
            F.data == "gallery_nav_prev"
        )
        
        self.router.callback_query.register(
            self.handle_gallery_nav_next,
            F.data == "gallery_nav_next"
        )
        
        self.router.callback_query.register(
            self.handle_delete_photo_callback,
            F.data.startswith("delete_photo_")
        )
        
        self.router.callback_query.register(
            self.handle_cancel_avatar_draft,
            F.data.startswith("cancel_avatar_draft")
        )
        
        self.router.callback_query.register(
            self.handle_delete_error_photo,
            F.data == "delete_error_photo"
        )
        
        self.router.callback_query.register(
            self.handle_photo_counter,
            F.data == "photo_counter"
        )
        
        self.router.callback_query.register(
            self.show_training_confirmation,
            F.data == "confirm_training_current"
        )
        
        # Обработчик загрузки фотографий
        self.router.message.register(
            self.handle_photo_upload,
            F.photo,
            AvatarStates.uploading_photos
        )

    async def register_handlers(self):
        """Асинхронная регистрация обработчиков для загрузки фотографий (для совместимости)"""
        self._register_handlers_sync()

    # Делегирование к модулям
    async def start_photo_upload(self, callback: CallbackQuery, state: FSMContext):
        """Начинает процесс загрузки фотографий для аватара"""
        try:
            user_id = callback.from_user.id
            
            # Очищаем кэш предыдущих сообщений прогресса
            self.progress_handler.clear_progress_cache(user_id)
            
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_name = data.get("avatar_name", "Аватар")
            avatar_gender = data.get("gender", "unknown")
            training_type = data.get("training_type", "portrait")
            avatar_id = data.get("avatar_id")
            
            if not avatar_id:
                await callback.answer("❌ Ошибка: данные аватара не найдены", show_alert=True)
                return
            
            # Проверяем существующий драфт
            existing_photos_count = await self._check_existing_draft(user_id, UUID(avatar_id))
            
            # Устанавливаем состояние загрузки
            await state.set_state(AvatarStates.uploading_photos)
            
            if existing_photos_count > 0:
                # Показываем информацию о продолжении
                await self._show_draft_continuation(callback, state, avatar_name, existing_photos_count, UUID(avatar_id))
            else:
                # Показываем обычные инструкции
                intro_text = self.progress_handler._get_upload_intro_text(avatar_name, training_type, avatar_gender)
                await callback.message.edit_text(text=intro_text)
            
            logger.info(f"Пользователь {user_id} начал загрузку фото для аватара {avatar_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при начале загрузки фото: {e}")
            await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

    async def handle_photo_upload(self, message: Message, state: FSMContext, bot: Bot):
        """Делегирует обработку загрузки фото к UploadHandler"""
        try:
            # Обрабатываем загрузку через UploadHandler
            success, error_message, photos_count = await self.upload_handler.handle_photo_upload(message, state, bot)
            
            if success:
                # Получаем данные для обновления UI
                data = await state.get_data()
                avatar_id = UUID(data.get("avatar_id"))
                user_id = message.from_user.id
                
                # Получаем обновленные фотографии
                async with get_avatar_service() as avatar_service:
                    photos, _ = await avatar_service.get_avatar_photos(avatar_id)
                
                # Обновляем галерею если открыта
                await self.progress_handler.update_gallery_if_open(user_id, avatar_id, photos)
                
                # Показываем прогресс
                await self.progress_handler.show_upload_progress(message, photos_count, avatar_id)
            
        except Exception as e:
            logger.exception(f"Ошибка при обработке загрузки фото: {e}")
            await message.answer("❌ Произошла ошибка при загрузке фото")

    async def show_photo_gallery(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует показ галереи к GalleryHandler"""
        await self.gallery_handler.show_photo_gallery(callback, state)

    async def handle_gallery_nav_prev(self, callback: CallbackQuery):
        """Делегирует навигацию назад к GalleryHandler"""
        await self.gallery_handler.handle_gallery_navigation(callback, "prev")

    async def handle_gallery_nav_next(self, callback: CallbackQuery):
        """Делегирует навигацию вперед к GalleryHandler"""
        await self.gallery_handler.handle_gallery_navigation(callback, "next")

    async def handle_delete_photo_callback(self, callback: CallbackQuery):
        """Делегирует удаление фото к GalleryHandler"""
        try:
            # Извлекаем photo_index из callback_data
            photo_index = int(callback.data.split("_")[-1])
            
            # Получаем avatar_id из кэша галереи
            user_id = callback.from_user.id
            
            cache_data = await self.gallery_handler._get_gallery_cache(user_id)
            if cache_data is None:
                await callback.answer("❌ Галерея не найдена", show_alert=True)
                return
            
            avatar_id = UUID(cache_data["avatar_id"])
            await self.gallery_handler.handle_delete_photo(callback, avatar_id, photo_index)
            
        except Exception as e:
            logger.exception(f"Ошибка при удалении фото: {e}")
            await callback.answer("❌ Ошибка при удалении фото", show_alert=True)

    async def handle_back_to_upload(self, callback: CallbackQuery, state: FSMContext):
        """Возврат к загрузке фотографий"""
        try:
            # Очищаем кэш галереи
            user_id = callback.from_user.id
            self.gallery_handler.clear_gallery_cache(user_id)
            
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_id = UUID(data.get("avatar_id"))
            
            # Получаем текущее количество фото
            async with get_avatar_service() as avatar_service:
                photos, photos_count = await avatar_service.get_avatar_photos(avatar_id)
            
            # Показываем прогресс загрузки
            await self.progress_handler.show_upload_progress(callback.message, photos_count, avatar_id)
            
        except Exception as e:
            logger.exception(f"Ошибка при возврате к загрузке: {e}")
            await callback.answer("❌ Ошибка при возврате", show_alert=True)

    async def handle_cancel_avatar_draft(self, callback: CallbackQuery, state: FSMContext):
        """Обрабатывает отмену создания аватара с полной очисткой"""
        try:
            user_id = callback.from_user.id
            
            # Получаем данные из состояния
            data = await state.get_data()
            avatar_id_str = data.get("avatar_id")
            avatar_name = data.get("avatar_name", "аватар")
            
            if avatar_id_str:
                avatar_id = UUID(avatar_id_str)
                
                # Удаляем аватар из БД вместе с фотографиями
                async with get_avatar_service() as avatar_service:
                    await avatar_service.delete_avatar_completely(avatar_id)
                
                logger.info(f"Пользователь {user_id} отменил создание аватара {avatar_id}")
            
            # Очищаем состояние FSM
            await state.clear()
            
            # Очищаем кэши
            self.progress_handler.clear_progress_cache(user_id)
            self.gallery_handler.clear_gallery_cache(user_id)
            
            # Очищаем кэш загрузок
            from .upload_handler import user_upload_locks
            if user_id in user_upload_locks:
                del user_upload_locks[user_id]
            
            # Показываем подтверждение
            text = f"""🗑️ Создание аватара отменено

Драфт аватара "{avatar_name}" и все загруженные фотографии удалены.

Вы можете начать создание нового аватара в любое время."""
            
            # Возвращаем в главное меню
            from app.keyboards.main import get_main_menu
            keyboard = get_main_menu()
            
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.exception(f"Ошибка при отмене создания аватара: {e}")
            await callback.answer("❌ Произошла ошибка при отмене", show_alert=True)

    async def handle_delete_error_photo(self, callback: CallbackQuery):
        """Удаление сообщения с ошибкой фото"""
        try:
            await callback.message.delete()
            await callback.answer()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение с ошибкой: {e}")
            await callback.answer()

    async def handle_photo_counter(self, callback: CallbackQuery):
        """Обработка нажатия на счетчик фото (информационная кнопка)"""
        await callback.answer("📸 Это счетчик загруженных фотографий")

    async def show_training_confirmation(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует показ подтверждения обучения к ProgressHandler"""
        await self.progress_handler.show_training_confirmation(callback, state)

    # Вспомогательные методы
    async def _check_existing_draft(self, user_id: int, avatar_id: UUID) -> int:
        """Проверяет существующий драфт аватара и возвращает количество загруженных фото"""
        try:
            async with get_avatar_service() as avatar_service:
                photos, total = await avatar_service.get_avatar_photos(avatar_id)
                return total
        except Exception as e:
            logger.warning(f"Ошибка при проверке существующего драфта: {e}")
            return 0

    async def _show_draft_continuation(self, callback: CallbackQuery, state: FSMContext, avatar_name: str, existing_count: int, avatar_id: UUID):
        """Показывает информацию о продолжении загрузки существующего драфта"""
        # Временно используем значения по умолчанию
        gender_text = "👨 Мужской"
        type_text = "🎨 Портретный"
        
        text = f"""🔄 Продолжение создания аватара

🎭 Имя: {avatar_name}
📸 Уже загружено: {existing_count}/{self.config.MAX_PHOTOS} фото
👤 Пол: {gender_text}
🎨 Тип: {type_text}

✅ Отлично! Вы можете продолжить загрузку фотографий с того места, где остановились.

📤 Варианты действий:
• Загрузить еще фото для улучшения качества
• Посмотреть уже загруженные фото  
• Начать обучение (если загружено ≥{self.config.MIN_PHOTOS} фото)

💡 Совет: Для лучшего результата рекомендуется {self.config.MAX_PHOTOS} фото

📸 Продолжайте отправлять фотографии:"""
        
        from app.keyboards.photo_upload import get_photo_upload_keyboard
        keyboard = get_photo_upload_keyboard(existing_count, self.config.MIN_PHOTOS, self.config.MAX_PHOTOS)
        
        await callback.message.edit_text(text=text, reply_markup=keyboard) 