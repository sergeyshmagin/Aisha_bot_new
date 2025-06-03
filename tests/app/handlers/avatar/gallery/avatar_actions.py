"""
Обработчик действий с аватарами
Выделен из app/handlers/avatar/gallery.py для соблюдения правила ≤500 строк
"""
from uuid import UUID
import logging

from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest

from app.core.di import get_user_service, get_avatar_service
from .keyboards import GalleryKeyboards
from .models import gallery_cache
from app.core.logger import get_logger

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
        """Показывает подтверждение удаления аватара"""
        try:
            user_telegram_id = callback.from_user.id
            avatar_id = UUID(callback.data.split(":")[1])
            
            # Получаем информацию об аватаре для подтверждения
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
            
            # Формируем текст подтверждения
            avatar_name = avatar.name or "Безымянный аватар"
            status_text = self._get_status_text(avatar.status.value)
            
            text = f"""🗑️ **Подтверждение удаления**

❓ Вы действительно хотите удалить аватар?

🎭 **Название:** {avatar_name}
📊 **Статус:** {status_text}

⚠️ **Внимание!** Это действие нельзя отменить.
Все данные аватара будут удалены навсегда:
• Обученная модель
• Загруженные фотографии  
• История генераций

🤔 Подумайте ещё раз перед удалением."""
            
            keyboard = self.keyboards.get_delete_confirmation_keyboard(str(avatar_id))
            
            try:
                # Уровень 1: Попытка с Markdown
                await callback.message.edit_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            except TelegramBadRequest as markdown_error:
                if "parse entities" in str(markdown_error):
                    # Уровень 2: Проблема с Markdown - отправляем без форматирования
                    logger.warning(f"Проблема с Markdown в подтверждении удаления аватара: {markdown_error}")
                    text_plain = text.replace('**', '')
                    
                    try:
                        await callback.message.edit_text(
                            text=text_plain,
                            reply_markup=keyboard,
                            parse_mode=None
                        )
                    except Exception as fallback_error:
                        logger.exception(f"Критическая ошибка при fallback удаления аватара: {fallback_error}")
                        await callback.answer("❌ Ошибка отображения", show_alert=True)
                        return
                else:
                    # Другая ошибка Telegram
                    logger.exception(f"Другая ошибка Telegram при подтверждении удаления: {markdown_error}")
                    await callback.answer("❌ Ошибка отображения", show_alert=True)
                    return
            
            logger.info(f"Пользователь {user_telegram_id} запросил удаление аватара {avatar_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе подтверждения удаления: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def handle_delete_avatar_confirm(self, callback: CallbackQuery):
        """Подтверждает и выполняет удаление аватара"""
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
            
            # Получаем название аватара перед удалением
            avatar_name = "аватар"
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar_by_id(avatar_id)
                if avatar and avatar.user_id == user.id:
                    avatar_name = avatar.name or "Безымянный аватар"
                
                # Удаляем аватар
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
                    
                    await callback.answer(f"🗑️ Аватар «{avatar_name}» удален")
                    logger.info(f"Пользователь {user_telegram_id} удалил аватар {avatar_id} ({avatar_name})")
                else:
                    await callback.answer("❌ Не удалось удалить аватар", show_alert=True)
            
        except Exception as e:
            logger.exception(f"Ошибка при удалении аватара: {e}")
            await callback.answer("❌ Произошла ошибка при удалении", show_alert=True)

    async def handle_delete_avatar_cancel(self, callback: CallbackQuery):
        """Отменяет удаление аватара и возвращает к карточке"""
        try:
            user_telegram_id = callback.from_user.id
            avatar_id = UUID(callback.data.split(":")[1])
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Получаем текущие аватары из кэша
            cache_data = await gallery_cache.get_avatars(user_telegram_id)
            if not cache_data:
                # Если кэша нет, перезагружаем аватары
                async with get_avatar_service() as avatar_service:
                    avatars = await avatar_service.get_user_avatars_with_photos(user.id)
                    if avatars:
                        # Находим индекс отменяемого аватара
                        current_idx = 0
                        for i, avatar in enumerate(avatars):
                            if avatar.id == avatar_id:
                                current_idx = i
                                break
                        
                        await gallery_cache.set_avatars(user_telegram_id, avatars, current_idx)
                        cache_data = {"avatars": avatars, "current_idx": current_idx}
                    else:
                        await self._show_empty_gallery(callback)
                        return
            
            # Возвращаемся к карточке аватара
            from .avatar_cards import AvatarCardsHandler
            cards_handler = AvatarCardsHandler()
            await cards_handler.send_avatar_card(
                callback, 
                user.id, 
                cache_data["avatars"], 
                cache_data["current_idx"]
            )
            
            await callback.answer("✅ Удаление отменено")
            logger.info(f"Пользователь {user_telegram_id} отменил удаление аватара {avatar_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при отмене удаления: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    def _get_status_text(self, status: str) -> str:
        """Возвращает читаемый текст статуса аватара"""
        status_map = {
            "draft": "📝 Черновик",
            "photos_uploading": "📤 Загрузка фото",
            "training": "🎓 Обучение",
            "completed": "✅ Готов",
            "failed": "❌ Ошибка",
            "cancelled": "🚫 Отменен"
        }
        return status_map.get(status, f"❓ {status}")

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
                        logger.warning(f"Проблема с Markdown в пустой галерее аватаров (новое сообщение): {markdown_error}")
                        text_plain = text.replace('**', '')
                        await callback.message.answer(text_plain, reply_markup=keyboard, parse_mode=None)
                    else:
                        logger.exception(f"Другая ошибка при отправке пустой галереи: {markdown_error}")
                        raise
            else:
                # Если сообщение текстовое, просто редактируем
                # Уровень 1: Попытка с Markdown
                try:
                    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
                except TelegramBadRequest as markdown_error:
                    if "parse entities" in str(markdown_error):
                        # Уровень 2: Проблема с Markdown - отправляем без форматирования
                        logger.warning(f"Проблема с Markdown в пустой галерее аватаров (редактирование): {markdown_error}")
                        text_plain = text.replace('**', '')
                        await callback.message.edit_text(text_plain, reply_markup=keyboard, parse_mode=None)
                    else:
                        logger.exception(f"Другая ошибка при редактировании пустой галереи: {markdown_error}")
                        raise
        except Exception as general_error:
            logger.exception(f"Критическая ошибка в пустой галерее аватаров: {general_error}")
            await callback.answer("❌ Ошибка отображения галереи", show_alert=True) 