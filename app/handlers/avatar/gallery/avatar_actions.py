"""
Обработчик действий с аватарами
Выделен из app/handlers/avatar/gallery.py для соблюдения правила ≤500 строк
"""
from uuid import UUID
import logging

from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest

from app.core.di import get_user_service, get_avatar_service
from app.handlers.state import AvatarStates
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

    async def handle_rename_avatar(self, callback: CallbackQuery, state: FSMContext):
        """Начинает процесс переименования аватара"""
        try:
            user_telegram_id = callback.from_user.id
            avatar_id = UUID(callback.data.split(":")[1])
            
            # Получаем пользователя и аватар
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar(avatar_id)
                if not avatar or str(avatar.user_id) != str(user.id):
                    await callback.answer("❌ Аватар не найден", show_alert=True)
                    return
                
                current_name = avatar.name or "Безымянный аватар"
            
            # Сохраняем ID аватара в состояние
            await state.update_data(rename_avatar_id=str(avatar_id))
            await state.set_state(AvatarStates.renaming_avatar)
            
            # Формируем текст с инструкцией
            text = f"""✏️ **Переименование аватара**

🏷️ **Текущее имя:** {current_name}

📝 Введите новое имя для аватара:

💡 **Рекомендации:**
• Длина: 2-30 символов
• Используйте понятные имена
• Избегайте спецсимволов

✅ Просто напишите новое имя в чат"""
            
            keyboard = self.keyboards.get_rename_cancel_keyboard(str(avatar_id))
            
            # Отправляем инструкцию
            if callback.message.photo:
                # Если сообщение содержит фото, удаляем его и отправляем новое текстовое
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                
                await callback.message.answer(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                # Если сообщение текстовое, просто редактируем
                await callback.message.edit_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            
            logger.info(f"Пользователь {user_telegram_id} начал переименование аватара {avatar_id}")
            
        except Exception as e:
            logger.exception(f"Ошибка при начале переименования аватара: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def handle_rename_avatar_cancel(self, callback: CallbackQuery, state: FSMContext):
        """Отменяет переименование аватара"""
        try:
            user_telegram_id = callback.from_user.id
            avatar_id = UUID(callback.data.split(":")[1])
            
            # Очищаем состояние
            await state.clear()
            
            # Возвращаемся к карточке аватара
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            async with get_avatar_service() as avatar_service:
                avatars = await avatar_service.get_user_avatars_with_photos(user.id)
                
                # Находим индекс аватара
                current_idx = 0
                for i, avatar in enumerate(avatars):
                    if avatar.id == avatar_id:
                        current_idx = i
                        break
                
                # Показываем карточку аватара
                from .avatar_cards import AvatarCardsHandler
                cards_handler = AvatarCardsHandler()
                await cards_handler.send_avatar_card(callback, user.id, avatars, current_idx)
            
            await callback.answer("❌ Переименование отменено")
            
        except Exception as e:
            logger.exception(f"Ошибка при отмене переименования: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

    async def process_avatar_rename(self, message: Message, state: FSMContext):
        """Обрабатывает ввод нового имени аватара"""
        try:
            user_telegram_id = message.from_user.id
            new_name = message.text.strip()
            
            # Валидация имени
            if not new_name:
                await message.reply("❌ Имя не может быть пустым. Попробуйте ещё раз.")
                return
            
            if len(new_name) < 2:
                await message.reply("❌ Имя слишком короткое (минимум 2 символа). Попробуйте ещё раз.")
                return
            
            if len(new_name) > 30:
                await message.reply("❌ Имя слишком длинное (максимум 30 символов). Попробуйте ещё раз.")
                return
            
            # Получаем ID аватара из состояния
            data = await state.get_data()
            avatar_id_str = data.get("rename_avatar_id")
            if not avatar_id_str:
                await message.reply("❌ Ошибка: не найден ID аватара. Попробуйте начать заново.")
                await state.clear()
                return
            
            avatar_id = UUID(avatar_id_str)
            
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                if not user:
                    await message.reply("❌ Пользователь не найден")
                    return
            
            # Обновляем имя аватара
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar(avatar_id)
                if not avatar or str(avatar.user_id) != str(user.id):
                    await message.reply("❌ Аватар не найден")
                    await state.clear()
                    return
                
                old_name = avatar.name or "Безымянный аватар"
                
                # Обновляем имя
                updated_avatar = await avatar_service.set_avatar_name(avatar_id, new_name)
                
                if updated_avatar:
                    # Очищаем состояние
                    await state.clear()
                    
                    # Получаем обновленный список аватаров
                    avatars = await avatar_service.get_user_avatars_with_photos(user.id)
                    
                    # Находим индекс переименованного аватара
                    current_idx = 0
                    for i, avatar in enumerate(avatars):
                        if avatar.id == avatar_id:
                            current_idx = i
                            break
                    
                    # Обновляем кэш
                    await gallery_cache.set_avatars(user_telegram_id, avatars, current_idx)
                    
                    # Отправляем подтверждение
                    await message.reply(f"✅ Аватар переименован!\n\n📝 **{old_name}** → **{new_name}**")
                    
                    # Показываем обновленную карточку аватара
                    from .avatar_cards import AvatarCardsHandler
                    cards_handler = AvatarCardsHandler()
                    await cards_handler.send_avatar_card(
                        type('CallbackQuery', (), {
                            'message': message,
                            'from_user': message.from_user
                        })(), 
                        user.id, 
                        avatars, 
                        current_idx
                    )
                    
                    logger.info(f"Пользователь {user_telegram_id} переименовал аватар {avatar_id}: '{old_name}' → '{new_name}'")
                else:
                    await message.reply("❌ Не удалось переименовать аватар. Попробуйте ещё раз.")
            
        except ValueError as e:
            await message.reply("❌ Некорректные данные. Попробуйте ещё раз.")
            logger.error(f"Ошибка валидации при переименовании: {e}")
        except Exception as e:
            logger.exception(f"Ошибка при переименовании аватара: {e}")
            await message.reply("❌ Произошла ошибка. Попробуйте ещё раз.")

    async def handle_delete_avatar(self, callback: CallbackQuery):
        """Показывает подтверждение удаления аватара"""
        try:
            user_telegram_id = callback.from_user.id
            avatar_id = UUID(callback.data.split(":")[1])
            
            # Получаем пользователя и аватар
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            # Получаем информацию об аватаре
            avatar_name = "аватар"
            async with get_avatar_service() as avatar_service:
                avatar = await avatar_service.get_avatar(avatar_id)
                if not avatar or str(avatar.user_id) != str(user.id):
                    await callback.answer("❌ Аватар не найден", show_alert=True)
                    return
                
                avatar_name = avatar.name or "Безымянный аватар"
                photos, total_photos = await avatar_service.get_avatar_photos(avatar_id)
            
            # Формируем текст подтверждения
            text = f"""🗑️ **Удаление аватара**

Вы действительно хотите удалить аватар **«{avatar_name}»**?

⚠️ **Это действие необратимо!**

🗂️ Будет удалено:
• {total_photos} фотографий
• Все сгенерированные изображения  
• История генераций

🤔 Подумайте ещё раз перед удалением."""
            
            keyboard = self.keyboards.get_delete_confirmation_keyboard(str(avatar_id))
            
            # Проверяем тип сообщения и выбираем правильный метод отправки
            if callback.message.photo:
                # Если сообщение содержит фото, удаляем его и отправляем новое текстовое
                try:
                    await callback.message.delete()
                except Exception:
                    pass  # Игнорируем ошибки удаления
                
                # Отправляем новое сообщение
                try:
                    await callback.message.answer(
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                except TelegramBadRequest as markdown_error:
                    if "parse entities" in str(markdown_error):
                        # Проблема с Markdown - отправляем без форматирования
                        logger.warning(f"Проблема с Markdown в подтверждении удаления аватара (новое сообщение): {markdown_error}")
                        text_plain = text.replace('**', '')
                        await callback.message.answer(
                            text=text_plain,
                            reply_markup=keyboard,
                            parse_mode=None
                        )
                    else:
                        logger.exception(f"Ошибка при отправке подтверждения удаления: {markdown_error}")
                        await callback.answer("❌ Ошибка отображения", show_alert=True)
                        return
            else:
                # Если сообщение текстовое, просто редактируем
                try:
                    await callback.message.edit_text(
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                except TelegramBadRequest as markdown_error:
                    if "parse entities" in str(markdown_error):
                        # Проблема с Markdown - редактируем без форматирования
                        logger.warning(f"Проблема с Markdown в подтверждении удаления аватара (редактирование): {markdown_error}")
                        text_plain = text.replace('**', '')
                        await callback.message.edit_text(
                            text=text_plain,
                            reply_markup=keyboard,
                            parse_mode=None
                        )
                    else:
                        logger.exception(f"Ошибка при редактировании подтверждения удаления: {markdown_error}")
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
                avatar = await avatar_service.get_avatar(avatar_id)
                if avatar and str(avatar.user_id) == str(user.id):
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