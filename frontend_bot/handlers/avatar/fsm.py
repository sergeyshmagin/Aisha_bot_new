# Glue-код FSM для аватаров

# ... импортировать обработчики явно по мере декомпозиции ...

import logging
import asyncio
from uuid import uuid4
from telebot.types import Message
from frontend_bot.bot import bot
from frontend_bot.services.avatar_manager import (
    init_avatar_fsm,
    load_avatar_fsm,
)
from frontend_bot.services.state_manager import (
    set_state,
    get_state,
    set_current_avatar_id,
    get_current_avatar_id,
    clear_state,
)
from frontend_bot.texts.avatar.texts import PHOTO_REQUIREMENTS_TEXT
from frontend_bot.keyboards.common import avatar_type_keyboard
from frontend_bot.texts.common import PROMPT_TYPE_MENU
from frontend_bot.shared.utils import clear_old_wizard_messages
from frontend_bot.config import AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS

# from frontend_bot.handlers.avatar.state import user_session, user_gallery  # TODO: заменить на реальный импорт

# Временно для совместимости:
user_session = {}
user_gallery = {}

logger = logging.getLogger(__name__)


async def send_and_track(user_id, chat_id, *args, **kwargs):
    msg = await bot.send_message(chat_id, *args, **kwargs)
    user_session[user_id]["wizard_message_ids"].append(msg.message_id)
    return msg


async def start_avatar_wizard(message: Message):
    """
    Запускает визард создания аватара для пользователя.
    """
    logger.info(f"[AVATAR FSM] Запуск визарда для user_id={message.from_user.id}")
    user_id = message.from_user.id
    avatar_id = str(uuid4())
    user_session[user_id] = {
        "wizard_message_ids": [],
        "last_wizard_state": None,
        "uploaded_photo_msgs": [],
        "last_error_msg": None,
        "last_info_msg_id": None,
    }
    user_gallery[(user_id, avatar_id)] = {"index": 0, "last_switch": 0}
    await init_avatar_fsm(user_id, avatar_id, class_name="")
    await set_state(user_id, "avatar_photo_upload")
    set_current_avatar_id(user_id, avatar_id)
    requirements = PHOTO_REQUIREMENTS_TEXT
    await send_and_track(user_id, message.chat.id, requirements, parse_mode="HTML")
    state = await get_state(user_id)
    logger.info(
        f"[DEBUG] После запуска визарда: user_id={user_id}, "
        f"state={state}, "
        f"avatar_id={get_current_avatar_id(user_id)}"
    )


def reset_avatar_fsm(user_id):
    user_session.pop(user_id, None)
    for key in list(user_gallery.keys()):
        if key[0] == user_id:
            user_gallery.pop(key, None)
    asyncio.create_task(clear_state(user_id))
    set_current_avatar_id(user_id, None)


async def show_type_menu(chat_id, user_id):
    await clear_old_wizard_messages(
        bot, user_session, chat_id, user_id, keep_msg_id=None
    )
    msg = await send_and_track(
        user_id,
        chat_id,
        PROMPT_TYPE_MENU,
        reply_markup=avatar_type_keyboard,
    )
    return msg


def get_photo_hint_text(current, min_photos, max_photos):
    requirements = (
        f"Требования: фото должны быть разными, без фильтров, хорошее освещение. "
        f"Минимум: {min_photos}, максимум: {max_photos}."
    )
    if current < min_photos:
        return (
            f"✅ Принято: {current} фото из {min_photos}.\n"
            f"До минимума осталось: {min_photos - current} фото.\n\n"
            f"{requirements}"
        )
    elif current < max_photos:
        return (
            f"✅ Принято: {current} фото из {max_photos}.\n"
            f"Можно добавить ещё {max_photos - current} фото для лучшего результата.\n\n"
            f"{requirements}"
        )
    else:
        return (
            f"✅ Принято максимальное количество фото: {max_photos}.\n"
            f"{requirements}"
        )


async def update_photo_hint(user_id, chat_id, avatar_id):
    data = await load_avatar_fsm(user_id, avatar_id)
    photos = data.get("photos", [])
    count = len(photos)
    msg_id = user_session[user_id].get("last_info_msg_id")
    if msg_id:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
    text = get_photo_hint_text(count, AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS)
    msg = await bot.send_message(chat_id, text)
    user_session[user_id]["last_info_msg_id"] = msg.message_id
