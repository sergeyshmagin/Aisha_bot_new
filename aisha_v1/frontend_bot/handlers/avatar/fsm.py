"""
Модуль FSM для создания аватаров.
"""

import logging
import asyncio
from uuid import uuid4
from telebot.types import Message
from telebot.async_telebot import AsyncTeleBot
from frontend_bot.bot_instance import bot
from frontend_bot.services.avatar_manager import (
    init_avatar_fsm,
    get_current_avatar_id,
    set_current_avatar_id,
)
from frontend_bot.services.state_utils import set_state_pg as set_state, get_state_pg as get_state, clear_state_pg as clear_state
from frontend_bot.texts.avatar.texts import PHOTO_REQUIREMENTS_TEXT, PHOTO_TYPE_PROMPT
from frontend_bot.keyboards.avatar import avatar_type_keyboard
from frontend_bot.texts.common import PROMPT_TYPE_MENU
from frontend_bot.shared.utils import clear_old_wizard_messages, send_and_track
from frontend_bot.config import settings
from frontend_bot.handlers.avatar.state import user_session, user_gallery
from frontend_bot.services.avatar_workflow import create_draft_avatar, update_draft_avatar
from sqlalchemy import select
from database.models import UserAvatar
from frontend_bot.repositories.user_repository import UserRepository
from frontend_bot.services.avatar_validator import validate_avatar_exists, validate_avatar_photos
from frontend_bot.keyboards.avatar import avatar_type_keyboard
from frontend_bot.shared.utils import clear_old_wizard_messages
from frontend_bot.handlers.avatar.state import user_session
from database.config import AsyncSessionLocal
from frontend_bot.services.photo_buffer import get_buffered_photos_redis, clear_photo_buffer_redis
from frontend_bot.repositories.state_repository import StateRepository
from frontend_bot.handlers.avatar.navigation import start_avatar_wizard
from sqlalchemy.ext.asyncio import AsyncSession
from .utils import get_photo_hint_text, update_photo_hint, reset_avatar_fsm

logger = logging.getLogger(__name__)

def get_gallery_key(user_id: int, avatar_id: str) -> str:
    """Получает ключ для галереи."""
    return f"{user_id}:{avatar_id}"


def reset_avatar_fsm(user_id, session):
    user_session.pop(user_id, None)
    for key in list(user_gallery.keys()):
        if key.startswith(f"{user_id}:"):
            user_gallery.pop(key, None)
    asyncio.create_task(clear_state(user_id, session))
    set_current_avatar_id(user_id, None)
    from frontend_bot.handlers.avatar.photo_upload import clear_photo_buffer_redis
    asyncio.create_task(clear_photo_buffer_redis(user_id))


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


async def handle_avatar_name_input(message, session):
    """
    Обрабатывает ввод имени аватара.
    
    Args:
        message (Message): Объект сообщения
        session (AsyncSession): Сессия БД
    """
    user_id = message.from_user.id
    state = await get_state(user_id, session)
    
    if not state or state.get("state") != "avatar_enter_name":
        return
        
    avatar_id = state.get("avatar_id")
    if not avatar_id:
        await bot.send_message(message.chat.id, "Аватар не найден")
        return
        
    # Валидация аватара
    is_valid, msg = await validate_avatar_exists(user_id, avatar_id, session)
    if not is_valid:
        await bot.send_message(message.chat.id, f"Ошибка: {msg}")
        return
        
    name = message.text.strip()
    if not name:
        await bot.send_message(message.chat.id, "Имя не может быть пустым")
        return
        
    # Обновляем имя аватара
    await update_draft_avatar(user_id, session, {
        "avatar_data": {"title": name}
    })
    
    # Переходим к подтверждению
    await set_state(user_id, {
        "state": "avatar_confirm",
        "avatar_id": avatar_id
    }, session)
    
    # Показываем подтверждение
    from frontend_bot.handlers.avatar.confirm import show_avatar_confirm
    await show_avatar_confirm(message.chat.id, user_id, avatar_id, session)
