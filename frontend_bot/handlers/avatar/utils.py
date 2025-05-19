from frontend_bot.config import settings
from frontend_bot.services.avatar_manager import set_current_avatar_id
from frontend_bot.bot import bot
import asyncio
from frontend_bot.handlers.avatar.state import user_session, user_gallery
from frontend_bot.shared.progress import get_progressbar
from frontend_bot.services.state_utils import clear_state, set_state
import logging

logger = logging.getLogger(__name__)

# Прогресс-бар

# --- FSM/Session утилиты ---


def reset_avatar_fsm(user_id, session):
    from frontend_bot.handlers.avatar.fsm import reset_avatar_fsm as _reset_avatar_fsm
    _reset_avatar_fsm(user_id, session)


def get_gallery_key(user_id: int, avatar_id: str) -> str:
    """Получает ключ для галереи."""
    return f"{user_id}:{avatar_id}"


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
    msg_id = user_session[user_id].get("last_info_msg_id")
    if msg_id:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
    text = get_photo_hint_text(count, settings.AVATAR_MIN_PHOTOS, settings.AVATAR_MAX_PHOTOS)
    msg = await bot.send_message(chat_id, text)
    user_session[user_id]["last_info_msg_id"] = msg.message_id


async def delete_last_error_message(user_id, chat_id):
    old_err = user_session[user_id]["last_error_msg"]
    if old_err:
        try:
            await bot.delete_message(chat_id, old_err)
        except Exception:
            pass
        user_session[user_id]["last_error_msg"] = None


async def delete_last_info_message(user_id, chat_id):
    msg_id = user_session[user_id].get("last_info_msg_id")
    if msg_id:
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        user_session[user_id]["last_info_msg_id"] = None


# Остальные утилиты (reset, get_photo_hint_text, update_photo_hint, delete_last_error_message, delete_last_info_message)
# ... переносить по аналогии ...
