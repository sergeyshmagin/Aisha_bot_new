"""
Обработчик действий с аватарами
Выделен из app/handlers/avatar/gallery.py для соблюдения правила ≤500 строк
"""
from uuid import UUID
import logging

from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.core.di import get_user_service, get_avatar_service
from .keyboards import GalleryKeyboards
from .models import gallery_cache

logger = logging.getLogger(__name__)

class AvatarActionsHandler:
    """Обработчик действий с аватарами"""
    
    def __init__(self):
        self.keyboards = GalleryKeyboards()
    
    async def handle_set_main_avatar(self, callback: CallbackQuery):
        """Устанавливает аватар как основной"""
        try:
            user_telegram_id = callback.from_user.id
            avatar_id = UUID(callback.data.split(":")[1])
            
            # Получаем пользователя
            user_id = None
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
                
                user_id = user.id
            
            # Устанавливаем основной аватар
            async with get_avatar_service() as avatar_service:
                success = await avatar_service.set_main_avatar(user.id, avatar_id)
                
                if success:
                    # Обновляем кэш
                    cache_data = await gallery_cache.get_avatars(user_telegram_id)
                    if cache_data:
                        # Перезагружаем аватары с обновленными данными
                        avatars = await avatar_service.get_user_avatars_with_photos(user.id)
                        
                        # Находим индекс установленного аватара
                        current_idx = 0
                        for i, avatar in enumerate(avatars):
                            if avatar.id == avatar_id:
                                current_idx = i
                                break
                        
                        # Обновляем кэш с новыми данными
                        await gallery_cache.set_avatars(user_telegram_id, avatars, current_idx)
                        
                        # Обновляем карточку
                        from .avatar_cards import AvatarCardsHandler
                        cards_handler = AvatarCardsHandler()
                        await cards_handler.send_avatar_card(callback, user.id, avatars, current_idx)
                    
                    await callback.answer("⭐ Аватар установлен как основной!")
                else:
                    await callback.answer("❌ Не удалось установить аватар как основной", show_alert=True)
            
        except Exception as e:
            logger.exception(f"Ошибка при установке основного аватара: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def handle_delete_avatar(self, callback: CallbackQuery):
        """Удаляет аватар"""
        try:
            user_telegram_id = callback.from_user.id
            avatar_id = UUID(callback.data.split(":")[1])
            
            # Получаем пользователя
            user_id = None
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
                
                user_id = user.id
            
            # Удаляем аватар
            async with get_avatar_service() as avatar_service:
                success = await avatar_service.delete_avatar_completely(avatar_id)
                
                if success:
                    # Обновляем галерею
                    avatars = await avatar_service.get_user_avatars_with_photos(user.id)
                    
                    if avatars:
                        # Если остались аватары, показываем первый
                        await gallery_cache.set_avatars(user_telegram_id, avatars, 0)
                        
                        from .avatar_cards import AvatarCardsHandler
                        cards_handler = AvatarCardsHandler()
                        await cards_handler.send_avatar_card(callback, user.id, avatars, 0)
                    else:
                        # Если аватаров не осталось, показываем заглушку
                        await self._show_empty_gallery(callback)
                    
                    await callback.answer("🗑️ Аватар удален")
                else:
                    await callback.answer("❌ Не удалось удалить аватар", show_alert=True)
            
        except Exception as e:
            logger.exception(f"Ошибка при удалении аватара: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def _show_empty_gallery(self, callback: CallbackQuery):
        """Показывает заглушку пустой галереи"""
        text = """🎭 **Мои аватары**

🔍 У вас больше нет аватаров

🆕 Создайте новый аватар чтобы:
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