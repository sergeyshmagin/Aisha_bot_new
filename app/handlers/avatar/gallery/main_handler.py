"""
Основной обработчик галереи аватаров
Рефакторинг app/handlers/avatar/gallery.py (663 строки → модули)
Объединяет AvatarCardsHandler, PhotoGalleryHandler, AvatarActionsHandler
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import logging

from app.core.di import get_user_service, get_avatar_service
from .avatar_cards import AvatarCardsHandler
from .photo_gallery import PhotoGalleryHandler
from .avatar_actions import AvatarActionsHandler
from .keyboards import GalleryKeyboards
from .models import gallery_cache

logger = logging.getLogger(__name__)

class GalleryHandler:
    """
    Основной обработчик галереи аватаров.
    Объединяет модули: AvatarCardsHandler, PhotoGalleryHandler, AvatarActionsHandler
    """
    
    def __init__(self):
        """Инициализация обработчика галереи"""
        self.router = Router()
        
        # Инициализируем модули
        self.cards_handler = AvatarCardsHandler()
        self.photo_handler = PhotoGalleryHandler()
        self.actions_handler = AvatarActionsHandler()
        self.keyboards = GalleryKeyboards()
        
        logger.info("Инициализирован GalleryHandler с модулями")

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
        
        # Фотогалерея
        self.router.callback_query.register(
            self.handle_view_avatar_photos,
            F.data.startswith("avatar_view_photos:")
        )
        
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

    async def handle_delete_avatar(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует удаление аватара"""
        await self.actions_handler.handle_delete_avatar(callback)

    async def handle_delete_avatar_confirm(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует подтверждение удаления аватара"""
        await self.actions_handler.handle_delete_avatar_confirm(callback)

    async def handle_delete_avatar_cancel(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует отмену удаления аватара"""
        await self.actions_handler.handle_delete_avatar_cancel(callback)

    async def handle_view_avatar_photos(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует просмотр фотографий аватара"""
        await self.photo_handler.handle_view_avatar_photos(callback)

    async def handle_photo_navigation(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует навигацию по фотографиям"""
        await self.photo_handler.handle_photo_navigation(callback)

    async def handle_view_avatar_card(self, callback: CallbackQuery, state: FSMContext):
        """Делегирует возврат к карточке аватара"""
        await self.photo_handler.handle_view_avatar_card(callback, state)

    async def handle_noop(self, callback: CallbackQuery):
        """Обработка пустых callback'ов (для неактивных кнопок)"""
        await callback.answer()

    async def handle_avatar_generate(self, callback: CallbackQuery, state: FSMContext):
        """Обработчик генерации изображений с аватаром"""
        try:
            # Извлекаем ID аватара из callback_data
            avatar_id = callback.data.split(":")[-1]
            
            # Проверяем что аватар существует и принадлежит пользователю
            user_telegram_id = callback.from_user.id
            
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar_by_id(avatar_id)
                if not avatar or avatar.user_id != user.id:
                    await callback.answer("❌ Аватар не найден", show_alert=True)
                    return
                
                # Проверяем что аватар готов к использованию
                if avatar.status.value != "completed":
                    await callback.answer("❌ Аватар ещё не готов к использованию", show_alert=True)
                    return
            
            # Переходим в меню генерации изображений
            from app.handlers.image_generation.main import ImageGenerationHandler
            
            # Сохраняем выбранный аватар в состояние
            await state.update_data(selected_avatar_id=avatar_id)
            
            # Показываем меню генерации изображений
            text = f"""🎨 **Генерация изображений**

🎭 **Выбранный аватар:** {avatar.name}
✨ **Статус:** Готов к использованию

📝 Введите описание изображения которое хотите создать с вашим аватаром.

💡 **Примеры:**
• "портрет в стиле ренессанса"
• "космонавт в открытом космосе"
• "супергерой в городе"
• "художник за мольбертом"

👆 Просто напишите ваше описание!"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔙 Назад к аватарам",
                    callback_data="avatar_gallery"
                )]
            ])
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            # Устанавливаем состояние ожидания промпта
            from app.handlers.image_generation.states import ImageGenerationStates
            await state.set_state(ImageGenerationStates.waiting_for_prompt)
            
            logger.info(f"Пользователь {user_telegram_id} начал генерацию с аватаром {avatar_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при переходе к генерации изображений: {e}")
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
        
        # Проверяем тип сообщения и выбираем правильный метод
        if callback.message.photo:
            # Если сообщение содержит фото, удаляем его и отправляем текстовое
            try:
                await callback.message.delete()
            except Exception:
                pass  # Игнорируем ошибки удаления
            
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            # Если сообщение текстовое, просто редактируем
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown") 