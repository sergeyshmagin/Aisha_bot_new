"""
Модуль FSM для создания аватаров.
"""

# ... импортировать обработчики явно по мере декомпозиции ...

import logging
import asyncio
from uuid import uuid4
from telebot.types import Message
from frontend_bot.bot_instance import bot
from frontend_bot.services.avatar_manager import (
    init_avatar_fsm,
    get_current_avatar_id,
    set_current_avatar_id,
)
from frontend_bot.services.state_utils import set_state_pg as set_state, get_state_pg as get_state, clear_state_pg as clear_state
from frontend_bot.texts.avatar.texts import PHOTO_REQUIREMENTS_TEXT
from frontend_bot.keyboards.common import avatar_type_keyboard
from frontend_bot.texts.common import PROMPT_TYPE_MENU
from frontend_bot.shared.utils import clear_old_wizard_messages, send_and_track
from frontend_bot.config import settings
from frontend_bot.handlers.avatar.state import user_session, user_gallery
from frontend_bot.services.avatar_workflow import create_draft_avatar, update_draft_avatar
from sqlalchemy import select
from database.models import UserAvatar
from frontend_bot.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

def get_gallery_key(user_id: int, avatar_id: str) -> str:
    """Получает ключ для галереи."""
    return f"{user_id}:{avatar_id}"


async def start_avatar_wizard(message: Message, session):
    """
    Запускает визард создания аватара для пользователя.
    """
    logger.info(f"[AVATAR FSM] Запуск визарда для user_id={message.from_user.id}")
    telegram_id = message.from_user.id
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        await bot.send_message(message.chat.id, "Пользователь не найден. Пожалуйста, /start.")
        return
    uuid_user_id = user.id
    avatar_id = str(uuid4())
    user_session[uuid_user_id] = {
        "wizard_message_ids": [],
        "last_wizard_state": None,
        "uploaded_photo_msgs": [],
        "last_error_msg": None,
        "last_info_msg_id": None,
        "edit_mode": "create",
    }
    gallery_key = get_gallery_key(uuid_user_id, avatar_id)
    user_gallery[gallery_key] = {"index": 0, "last_switch": 0}
    await create_draft_avatar(uuid_user_id, session, {"photo_key": "", "preview_key": "", "avatar_data": {"step": 0}})
    await set_state(uuid_user_id, "avatar_photo_upload", session)
    set_current_avatar_id(uuid_user_id, avatar_id)
    requirements = PHOTO_REQUIREMENTS_TEXT
    await send_and_track(bot, user_session, uuid_user_id, message.chat.id, requirements, parse_mode="HTML")
    state = await get_state(uuid_user_id, session)
    logger.info(
        f"[DEBUG] После запуска визарда: user_id={uuid_user_id}, "
        f"state={state}, "
        f"avatar_id={get_current_avatar_id(uuid_user_id)}"
    )


def reset_avatar_fsm(user_id, session):
    user_session.pop(user_id, None)
    for key in list(user_gallery.keys()):
        if key.startswith(f"{user_id}:"):
            user_gallery.pop(key, None)
    asyncio.create_task(clear_state(user_id, session))
    set_current_avatar_id(user_id, None)


async def show_type_menu(chat_id, user_id):
    await clear_old_wizard_messages(
        bot, user_session, chat_id, user_id, keep_msg_id=None
    )
    msg = await send_and_track(
        bot, user_session, user_id, chat_id,
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


async def update_photo_hint(user_id, chat_id, avatar_id, session):
    result = await session.execute(
        select(UserAvatar).where(UserAvatar.user_id == user_id, UserAvatar.id == avatar_id)
    )
    avatar = result.scalar_one_or_none()
    photos = avatar.avatar_data.get("photos", []) if avatar and avatar.avatar_data else []
    count = len(photos)
    msg_id = user_session[user_id].get("last_info_msg_id")
    if msg_id:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
    text = get_photo_hint_text(count, settings.AVATAR_MIN_PHOTOS, settings.AVATAR_MAX_PHOTOS)
    msg = await bot.send_message(chat_id, text)
    user_session[user_id]["last_info_msg_id"] = msg.message_id
