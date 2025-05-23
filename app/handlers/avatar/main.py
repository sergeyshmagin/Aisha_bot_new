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

logger = get_logger(__name__)
router = Router()

class AvatarMainHandler:
    """Основной обработчик меню аватаров"""
    
    def __init__(self):
        self.texts = AvatarTexts()
    
    async def show_avatar_menu(self, callback: CallbackQuery, state: FSMContext):
        """Показывает главное меню аватаров"""
        try:
            # Получаем сервисы через DI
            async with get_user_service() as user_service:
                user = await user_service.get_user_by_telegram_id(callback.from_user.id)
                
                if not user:
                    await callback.answer("❌ Пользователь не найден", show_alert=True)
                    return
            
            async with get_avatar_service() as avatar_service:
                # Получаем аватары пользователя
                user_avatars = await avatar_service.get_user_avatars(user.id)
                avatars_count = len(user_avatars)
            
            # Устанавливаем состояние
            await state.set_state(AvatarStates.menu)
            
            # Формируем текст и клавиатуру
            keyboard = get_avatar_main_menu(avatars_count)
            text = self.texts.get_main_menu_text(avatars_count)
            
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

@router.callback_query(F.data == "avatar_create")
async def start_avatar_creation(callback: CallbackQuery, state: FSMContext):
    """Начинает создание нового аватара"""
    try:
        # Переходим к выбору типа обучения (новая логика)
        from .training_type_selection import show_training_type_selection
        await show_training_type_selection(callback, state)
        
        logger.info(f"Пользователь {callback.from_user.id} начал создание аватара")
        
    except Exception as e:
        logger.exception(f"Ошибка при начале создания аватара: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.callback_query(F.data == "avatar_gallery")
async def show_avatar_gallery(callback: CallbackQuery, state: FSMContext):
    """Показывает галерею аватаров"""
    try:
        # TODO: Реализовать галерею аватаров
        await callback.message.edit_text(
            "🎭 **Галерея аватаров**\n\n🚧 В разработке...\n\nВозвращайтесь позже!",
            parse_mode="Markdown"
        )
        
        logger.info(f"Пользователь {callback.from_user.id} открыл галерею аватаров")
        
    except Exception as e:
        logger.exception(f"Ошибка при показе галереи аватаров: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуйте позже.", show_alert=True)

# Экспортируем обработчик для использования в других модулях
__all__ = ["avatar_main_handler", "router"] 