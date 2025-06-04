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
            # Получаем пользователя
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(callback.from_user.id)
                
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
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
                # Если сообщение содержит фото, удаляем его и отправляем текстовое
                try:
                    await callback.message.delete()
                except Exception:
                    pass  # Игнорируем ошибки удаления
                
                await callback.message.answer(text, reply_markup=keyboard)
            else:
                # Если сообщение текстовое, просто редактируем
                await callback.message.edit_text(text, reply_markup=keyboard)
            
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

@router.callback_query(F.data == "avatar_help")
async def show_avatar_help(callback: CallbackQuery):
    """Показывает справку по системе аватаров"""
    help_text = (
        "🧑‍🎨 Справка по аватарам:\n\n"
        "🆕 Создание: выбор типа → фото → обучение\n"
        "📁 Галерея: просмотр и управление\n"
        "💡 Совет: 10-20 качественных фото разных ракурсов"
    )
    await callback.answer(help_text, show_alert=True)

# Обработчик create_avatar перенесен в app/handlers/avatar/create.py
# чтобы избежать дублирования и конфликтов роутеров

# Галерея аватаров обрабатывается в отдельном модуле gallery.py
# Это сделано для лучшей организации кода и возможности повторного использования

# Экспортируем обработчик для использования в других модулях
__all__ = ["avatar_main_handler", "router"] 