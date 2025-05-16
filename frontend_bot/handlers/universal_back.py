import logging
from frontend_bot.bot_instance import bot
from frontend_bot.services.state_utils import get_state, set_state
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
from frontend_bot.keyboards.reply import (
    photo_menu_keyboard,
    ai_photographer_keyboard,
    my_avatars_keyboard,
    photo_enhance_keyboard,
    transcribe_keyboard,
)
from frontend_bot.services.avatar_manager import get_avatars_index
from frontend_bot.services.avatar_workflow import cleanup_state

logger = logging.getLogger(__name__)


@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
async def handle_back(message):
    """Обработчик возврата в предыдущее меню."""
    logger.info(f"handle_back: message.text={message.text!r}, user_id={message.from_user.id}")
    try:
        user_id = message.from_user.id
        current_state = await get_state(user_id)
        
        if current_state == "photo_enhance":
            await handle_photo_enhance_back(message)
        elif current_state == "transcribe":
            await handle_transcribe_back(message)
        else:
            await set_state(user_id, "main_menu")
            await bot.send_message(
                message.chat.id,
                "Выберите действие:",
                reply_markup=main_menu_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Error in handle_back: {e}")
        await bot.send_message(
            message.chat.id,
            "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
            reply_markup=main_menu_keyboard()
        )
        await set_state(user_id, "main_menu")

@bot.message_handler(func=lambda message: message.text == "Отмена")
async def handle_cancel(message):
    """Обработчик отмены текущего действия."""
    logger.info(f"handle_cancel: message.text={message.text!r}, user_id={message.from_user.id}")
    try:
        user_id = message.from_user.id
        current_state = await get_state(user_id)
        
        # Обработка отмены для аватара
        if current_state.startswith("avatar_"):
            await cleanup_state(user_id)
            await bot.send_message(
                message.chat.id,
                "Создание аватара отменено.",
                reply_markup=main_menu_keyboard()
            )
            return
            
        # Обработка отмены для других состояний
        if current_state == "photo_enhance":
            await handle_photo_enhance_back(message)
        elif current_state == "transcribe":
            await handle_transcribe_back(message)
        else:
            await set_state(user_id, "main_menu")
            await bot.send_message(
                message.chat.id,
                "Действие отменено.",
                reply_markup=main_menu_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Error in handle_cancel: {e}")
        await bot.send_message(
            message.chat.id,
            "Произошла ошибка при отмене действия. Пожалуйста, попробуйте еще раз.",
            reply_markup=main_menu_keyboard()
        )
        await set_state(user_id, "main_menu")

async def handle_photo_enhance_back(message):
    """Обработчик возврата в меню улучшения фото."""
    try:
        user_id = message.from_user.id
        await set_state(user_id, "main_menu")
        await bot.send_message(
            message.chat.id,
            "Выберите действие:",
            reply_markup=photo_enhance_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in handle_photo_enhance_back: {e}")
        await bot.send_message(
            message.chat.id,
            "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
            reply_markup=main_menu_keyboard()
        )
        await set_state(user_id, "main_menu")

async def handle_transcribe_back(message):
    """Обработчик возврата в меню транскрибации."""
    try:
        user_id = message.from_user.id
        await set_state(user_id, "main_menu")
        await bot.send_message(
            message.chat.id,
            "Выберите действие:",
            reply_markup=transcribe_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in handle_transcribe_back: {e}")
        await bot.send_message(
            message.chat.id,
            "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
            reply_markup=main_menu_keyboard()
        )
        await set_state(user_id, "main_menu")
