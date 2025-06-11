"""
Основной обработчик галереи аватаров
Рефакторинг app/handlers/avatar/gallery.py (663 строки → модули)
Объединяет AvatarCardsHandler, PhotoGalleryHandler, AvatarActionsHandler
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import logging

from app.core.di import get_user_service, get_avatar_service
from app.core.logger import get_logger
from app.handlers.state import AvatarStates
from .avatar_cards import AvatarCardsHandler
from .photo_gallery import PhotoGalleryHandler
from .avatar_actions import AvatarActionsHandler
from .keyboards import GalleryKeyboards
from .models import gallery_cache

logger = logging.getLogger(__name__)

class AvatarGalleryHandler:
    """
    Основной обработчик галереи аватаров.
    Объединяет модули: AvatarCardsHandler, PhotoGalleryHandler, AvatarActionsHandler
    
    Переименован из GalleryHandler для избежания конфликтов с галереей изображений
    """
    
    def __init__(self):
        """Инициализация обработчика галереи аватаров"""
        self.router = Router()
        
        # Инициализируем модули
        self.cards_handler = AvatarCardsHandler()
        self.photo_handler = PhotoGalleryHandler()
        self.actions_handler = AvatarActionsHandler()
        self.keyboards = GalleryKeyboards()
        
        logger.info("Инициализирован AvatarGalleryHandler с модулями")

    def _register_handlers_sync(self):
        """Синхронная регистрация обработчиков галереи"""
        logger.info("Регистрация обработчиков галереи аватаров")
        
        # Основная галерея
        self.router.callback_query.register(
            self.show_avatar_gallery,
            F.data == "avatar_gallery"
        )
        
        # Навигация по карточкам аватаров
        self.router.callback_query.register(
            self.handle_avatar_card_prev,
            F.data.startswith("avatar_card_prev:")
        )
        
        self.router.callback_query.register(
            self.handle_avatar_card_next,
            F.data.startswith("avatar_card_next:")
        )
        
        # Действия с аватарами
        self.router.callback_query.register(
            self.handle_set_main_avatar,
            F.data.startswith("avatar_set_main:")
        )
        
        # Переименование аватара
        self.router.callback_query.register(
            self.handle_rename_avatar,
            F.data.startswith("avatar_rename:")
        )
        
        self.router.callback_query.register(
            self.handle_rename_avatar_cancel,
            F.data.startswith("avatar_rename_cancel:")
        )
        
        # Обработчик ввода текста для переименования
        self.router.message.register(
            self.handle_rename_text_input,
            AvatarStates.renaming_avatar
        )
        
        self.router.callback_query.register(
            self.handle_delete_avatar,
            F.data.startswith("avatar_delete:")
        )
        
        # Подтверждение удаления аватара
        self.router.callback_query.register(
            self.handle_delete_avatar_confirm,
            F.data.startswith("avatar_delete_confirm:")
        )
        
        self.router.callback_query.register(
            self.handle_delete_avatar_cancel,
            F.data.startswith("avatar_delete_cancel:")
        )
        
        # Фотогалерея (навигация по фотографиям)
        self.router.callback_query.register(
            self.handle_photo_navigation,
            F.data.startswith("avatar_photo_prev:")
        )
        
        self.router.callback_query.register(
            self.handle_photo_navigation,
            F.data.startswith("avatar_photo_next:")
        )
        
        self.router.callback_query.register(
            self.handle_view_avatar_card,
            F.data.startswith("avatar_view_card:")
        )
        
        # Пустые callback'ы
        self.router.callback_query.register(
            self.handle_noop,
            F.data == "noop"
        )
        
        # Генерация изображений с аватаром
        self.router.callback_query.register(
            self.handle_avatar_generate,
            F.data.startswith("avatar_generate:")
        )
        
        # Продолжение создания аватара
        self.router.callback_query.register(
            self.handle_continue_avatar_creation,
            F.data.startswith("avatar_continue_creation:")
        )

    async def register_handlers(self):
        """Асинхронная регистрация обработчиков галереи (для совместимости)"""
        self._register_handlers_sync()

    # Основные методы
    async def show_avatar_gallery(self, callback: CallbackQuery, state: FSMContext):
        """Показывает галерею аватаров пользователя"""
        try:
            user_telegram_id = callback.from_user.id
            
            # Получаем пользователя
            user_id = None
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                if not user:
                    await callback.message.edit_text("❌ Пользователь не найден")
                    return
                
                user_id = user.id
            
            # Получаем аватары пользователя
            async with get_avatar_service() as avatar_service:
                avatars = await avatar_service.get_user_avatars_with_photos(user_id)
            
            if not avatars:
                # Если аватаров нет
                await self._show_empty_gallery_message(callback)
                return
            
            # Сохраняем список аватаров в кэш
            await gallery_cache.set_avatars(user_telegram_id, avatars, 0)
            
            # Показываем первый аватар
            await self.cards_handler.send_avatar_card(callback, user.id, avatars, 0)
            
            logger.info(f"Пользователь {user_telegram_id} открыл галерею аватаров ({len(avatars)} шт.)")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе галереи аватаров: {e}")
            await callback.answer("❌ Произошла ошибка при загрузке галереи", show_alert=True)

    # Делегирование к модулям
    async def handle_avatar_card_prev(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует переход к предыдущему аватару"""
        await self.cards_handler.handle_avatar_card_navigation(callback, "prev")

    async def handle_avatar_card_next(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует переход к следующему аватару"""
        await self.cards_handler.handle_avatar_card_navigation(callback, "next")

    async def handle_set_main_avatar(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует установку основного аватара"""
        await self.actions_handler.handle_set_main_avatar(callback)

    async def handle_rename_avatar(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует начало переименования аватара"""
        await self.actions_handler.handle_rename_avatar(callback, state)

    async def handle_rename_avatar_cancel(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует отмену переименования аватара"""
        await self.actions_handler.handle_rename_avatar_cancel(callback, state)

    async def handle_rename_text_input(self, message: Message, state: FSMContext):
        """Делегирует обработку ввода нового имени аватара"""
        await self.actions_handler.process_avatar_rename(message, state)

    async def handle_delete_avatar(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует удаление аватара"""
        await self.actions_handler.handle_delete_avatar(callback)

    async def handle_delete_avatar_confirm(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует подтверждение удаления аватара"""
        await self.actions_handler.handle_delete_avatar_confirm(callback)

    async def handle_delete_avatar_cancel(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует отмену удаления аватара"""
        await self.actions_handler.handle_delete_avatar_cancel(callback)

    async def handle_view_avatar_card(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует возврат к карточке аватара"""
        await self.photo_handler.handle_view_avatar_card(callback, state)

    async def handle_photo_navigation(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует навигацию по фотографиям"""
        await self.photo_handler.handle_photo_navigation(callback)

    async def handle_noop(self, callback: CallbackQuery):
        """Обработка пустых callback'ов (для неактивных кнопок)"""
        await callback.answer()

    async def handle_avatar_generate(self, callback: CallbackQuery, state: FSMContext):
        """Обработчик генерации изображений с аватаром"""
        try:
            # Извлекаем ID аватара из callback_data
            avatar_id_str = callback.data.split(":")[-1]
            user_telegram_id = callback.from_user.id
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Проверяем существование аватара и его принадлежность
            async with get_avatar_service() as avatar_service:
                from uuid import UUID
                avatar_id = UUID(avatar_id_str)
                avatar = await avatar_service.get_avatar(avatar_id)
                if not avatar or str(avatar.user_id) != str(user.id):
                    logger.warning(f"Аватар {avatar_id_str} не найден или не принадлежит пользователю {user.id}")
                    await callback.answer("❌ Аватар не найден", show_alert=True)
                    return
                
                # Проверяем что аватар готов к использованию
                if avatar.status != "completed":
                    await callback.answer("❌ Аватар ещё не готов к использованию", show_alert=True)
                    return
                
                # Устанавливаем этот аватар как основной если он не основной
                if not avatar.is_main:
                    await avatar_service.set_main_avatar(user.id, avatar_id)
                    logger.info(f"Установлен основной аватар {avatar_id_str} для генерации пользователя {user_telegram_id}")
            
            # Переходим к основному menu генерации
            from app.handlers.generation.main_handler import GenerationMainHandler
            generation_handler = GenerationMainHandler()
            
            # Показываем основное меню генерации
            await generation_handler.show_generation_menu(callback)
            
            logger.info(f"Пользователь {user_telegram_id} перенаправлен к основной генерации с аватаром {avatar_id_str}")
            
        except Exception as e:
            logger.exception(f"Ошибка при переходе к генерации изображений: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def handle_continue_avatar_creation(self, callback: CallbackQuery, state: FSMContext):
        """Обработчик продолжения создания аватара (переход к загрузке фото)"""
        try:
            # Извлекаем ID аватара из callback_data
            avatar_id_str = callback.data.split(":")[-1]
            user_telegram_id = callback.from_user.id
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Проверяем существование аватара
            async with get_avatar_service() as avatar_service:
                from uuid import UUID
                avatar_id = UUID(avatar_id_str)
                avatar = await avatar_service.get_avatar(avatar_id)
                if not avatar or str(avatar.user_id) != str(user.id):
                    await callback.answer("❌ Аватар не найден", show_alert=True)
                    return
                
                # Проверяем что аватар в статусе черновика или загрузки фото
                if avatar.status not in ["draft", "photos_uploading"]:
                    await callback.answer("❌ Этот аватар уже завершен", show_alert=True)
                    return
            
            # Устанавливаем данные аватара в состояние FSM для продолжения
            await state.update_data({
                "avatar_id": avatar_id_str,
                "avatar_name": avatar.name,
                "gender": avatar.gender.value if avatar.gender else "unknown",
                "training_type": avatar.training_type.value if avatar.training_type else "portrait"
            })
            
            # Переходим к загрузке фото - используем PhotoUploadHandler
            from app.handlers.avatar.photo_upload.main_handler import PhotoUploadHandler
            photo_upload_handler = PhotoUploadHandler()
            
            # Вызываем метод начала загрузки фото
            await photo_upload_handler.start_photo_upload(callback, state)
            
            logger.info(f"Пользователь {user_telegram_id} продолжил создание аватара {avatar_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при продолжении создания аватара: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    # Вспомогательные методы
    async def _show_empty_gallery_message(self, callback: CallbackQuery):
        """Показывает сообщение о пустой галерее"""
        text = """🎭 **Мои аватары**

🔍 У вас пока нет созданных аватаров

🆕 Создайте свой первый аватар чтобы:
• 🎨 Генерировать уникальные изображения
• 🎭 Создавать персональные портреты
• ✨ Экспериментировать со стилями

👆 Нажмите "Создать аватар" чтобы начать!"""
        
        keyboard = self.keyboards.get_empty_gallery_keyboard()
        
        try:
            # Проверяем тип сообщения и выбираем правильный метод
            if callback.message.photo:
                # Если сообщение содержит фото, удаляем его и отправляем текстовое
                try:
                    await callback.message.delete()
                except Exception:
                    pass  # Игнорируем ошибки удаления
                
                # Уровень 1: Попытка с Markdown
                try:
                    await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
                except TelegramBadRequest as markdown_error:
                    if "parse entities" in str(markdown_error):
                        # Уровень 2: Проблема с Markdown - отправляем без форматирования
                        logger.warning(f"Проблема с Markdown в пустой галерее аватаров главный handler (новое сообщение): {markdown_error}")
                        text_plain = text.replace('**', '')
                        await callback.message.answer(text_plain, reply_markup=keyboard, parse_mode=None)
                    else:
                        logger.exception(f"Другая ошибка при отправке пустой галереи главный handler: {markdown_error}")
                        raise
            else:
                # Если сообщение текстовое, просто редактируем
                # Уровень 1: Попытка с Markdown
                try:
                    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
                except TelegramBadRequest as markdown_error:
                    if "parse entities" in str(markdown_error):
                        # Уровень 2: Проблема с Markdown - отправляем без форматирования
                        logger.warning(f"Проблема с Markdown в пустой галерее аватаров главный handler (редактирование): {markdown_error}")
                        text_plain = text.replace('**', '')
                        await callback.message.edit_text(text_plain, reply_markup=keyboard, parse_mode=None)
                    else:
                        logger.exception(f"Другая ошибка при редактировании пустой галереи главный handler: {markdown_error}")
                        raise
        except Exception as general_error:
            logger.exception(f"Критическая ошибка в пустой галерее аватаров главный handler: {general_error}")
            await callback.answer("❌ Ошибка отображения галереи", show_alert=True) 