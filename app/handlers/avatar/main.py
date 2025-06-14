"""
Основные обработчики меню аватаров
Замена legacy AvatarHandler
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.keyboards.avatar_clean import get_avatar_main_menu
from app.texts.avatar import AvatarTexts  
from app.handlers.state import AvatarStates
from app.core.di import get_user_service, get_avatar_service
from app.core.logger import get_logger
from app.core.database import get_session
from app.database.models import Avatar, AvatarStatus
from sqlalchemy import select

logger = get_logger(__name__)
router = Router()

class AvatarMainHandler:
    """Основной обработчик меню аватаров"""
    
    def __init__(self):
        self.texts = AvatarTexts()
    
    async def show_avatar_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает главное меню аватаров"""
        try:
            # Получаем пользователя с автоматической регистрацией
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(callback.from_user.id)
                
                if not user:
                    # Автоматически регистрируем пользователя
                    telegram_user_data = {
                        "id": callback.from_user.id,
                        "first_name": callback.from_user.first_name,
                        "last_name": callback.from_user.last_name,
                        "username": callback.from_user.username,
                        "language_code": callback.from_user.language_code,
                        "is_premium": getattr(callback.from_user, 'is_premium', False),
                        "is_bot": callback.from_user.is_bot,
                    }
                    
                    user = await user_service.register_user(telegram_user_data)
                    if not user:
                        logger.error(f"Не удалось зарегистрировать пользователя {callback.from_user.id}")
                        await callback.answer("❌ Произошла ошибка. Попробуйте команду /start", show_alert=True)
                        return
            
            # 🚀 ИСПРАВЛЕНИЕ: Используем ту же логику что и в галерее
            async with get_avatar_service() as avatar_service:
                # Получаем все аватары кроме черновиков (как в галерее)
                avatars = await avatar_service.get_user_avatars_with_photos(user.id)
                avatars_count = len(avatars)
            
            # Устанавливаем состояние
            await state.set_state(AvatarStates.menu)
            
            # Формируем текст и клавиатуру
            keyboard = get_avatar_main_menu(avatars_count)
            text = self.texts.get_main_menu_text(avatars_count)
            
            # Проверяем тип сообщения и выбираем правильный метод
            if callback.message.photo:
                # ✅ ИСПРАВЛЕНИЕ: Редактируем подпись фото вместо удаления
                try:
                    await callback.message.edit_caption(
                        caption=text,
                        reply_markup=keyboard
                    )
                    logger.debug("✅ Avatar menu: отредактирована подпись фото")
                except Exception as edit_error:
                    logger.debug(f"Не удалось отредактировать подпись, отправляю новое: {edit_error}")
                    await callback.message.answer(
                        text=text,
                        reply_markup=keyboard
                    )
                
            elif callback.message.text or callback.message.caption:
                # ✅ Обычное текстовое сообщение - редактируем текст
                try:
                    await callback.message.edit_text(
                        text=text,
                        reply_markup=keyboard
                    )
                    logger.debug("✅ Avatar menu: отредактирован текст")
                except Exception as edit_error:
                    logger.debug(f"Не удалось отредактировать текст, отправляю новое: {edit_error}")
                    await callback.message.answer(
                        text=text,
                        reply_markup=keyboard
                    )
                
            else:
                # ❌ Неизвестный тип - отправляем новое (крайний случай)
                await callback.message.answer(
                    text=text,
                    reply_markup=keyboard
                )
                logger.debug("⚠️ Avatar menu: отправлено новое сообщение")
            
            await callback.answer()
            
            logger.info(f"Показано меню аватаров пользователю {user.id}, аватаров: {avatars_count}")
            
        except Exception as e:
            logger.exception(f"Ошибка при показе меню аватаров: {e}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)

# Создаем экземпляр обработчика
avatar_main_handler = AvatarMainHandler()

@router.callback_query(F.data == "avatar_menu")
async def show_avatar_menu(callback: CallbackQuery, state: FSMContext):
    """Обработчик показа меню аватаров"""
    await avatar_main_handler.show_avatar_menu(callback, state)

# @router.callback_query(F.data == "avatar_help")
# async def show_avatar_help(callback: CallbackQuery):
#     """Показывает справку по системе аватаров"""
#     help_text = (
#         "🧑‍🎨 Справка по аватарам:\n\n"
#         "🆕 Создание: выбор типа → фото → обучение\n"
#         "📁 Галерея: просмотр и управление\n"
#         "💡 Совет: 10-20 качественных фото разных ракурсов"
#     )
#     await callback.answer(help_text, show_alert=True)

# Обработчик create_avatar перенесен в app/handlers/avatar/create.py
# чтобы избежать дублирования и конфликтов роутеров

# Галерея аватаров обрабатывается в отдельном модуле gallery.py
# Это сделано для лучшей организации кода и возможности повторного использования

# Экспортируем обработчик для использования в других модулях
__all__ = ["avatar_main_handler", "router"] 