import logging
from frontend_bot.handlers.general import bot
from frontend_bot.services.state_manager import get_state, set_state
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
from frontend_bot.keyboards.reply import (
    photo_menu_keyboard,
    ai_photographer_keyboard,
    my_avatars_keyboard,
)
from frontend_bot.services.avatar_manager import get_avatars_index

logger = logging.getLogger(__name__)


@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
async def universal_back_handler(message):
    logger.info(f"[HANDLER] universal_back_handler, message.text={message.text!r}")
    user_id = message.from_user.id
    state = await get_state(user_id)
    logger.info(f"[UNIVERSAL_BACK] user_id={user_id}, state={state}")
    if state in [
        "avatar_photo_upload",
        "avatar_title",
        "avatar_confirm",
        "avatar_gallery_review",
    ]:
        avatars = await get_avatars_index(user_id)
        if avatars:
            await set_state(user_id, "my_avatars")
            await bot.send_message(
                message.chat.id,
                "Меню аватаров:",
                reply_markup=my_avatars_keyboard(),
            )
        else:
            await set_state(user_id, "ai_photographer")
            await bot.send_message(
                message.chat.id,
                "🧑‍🎨 ИИ фотограф\n\nСоздавайте аватары и образы с помощью ИИ.",
                reply_markup=ai_photographer_keyboard(),
            )
    elif state == "my_avatars":
        await set_state(user_id, "ai_photographer")
        await bot.send_message(
            message.chat.id,
            "🧑‍🎨 ИИ фотограф\n\nСоздавайте аватары и образы с помощью ИИ.",
            reply_markup=ai_photographer_keyboard(),
        )
    elif state == "ai_photographer":
        await set_state(user_id, "photo_menu")
        await bot.send_message(
            message.chat.id,
            "🖼 Работа с фото\n\nУлучшайте фото или создавайте ИИ-аватары.",
            reply_markup=photo_menu_keyboard(),
        )
    elif state == "photo_menu":
        await set_state(user_id, "main_menu")
        await bot.send_message(
            message.chat.id,
            "Главное меню. Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await set_state(user_id, "main_menu")
        await bot.send_message(
            message.chat.id,
            "Главное меню. Выберите действие:",
            reply_markup=main_menu_keyboard(),
        )
