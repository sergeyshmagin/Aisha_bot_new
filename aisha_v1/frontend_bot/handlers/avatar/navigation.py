"""
Функции навигации для аватаров.
"""

from typing import Optional
from telebot.async_telebot import AsyncTeleBot
from frontend_bot.keyboards.avatar import avatar_type_keyboard, avatar_confirm_keyboard
from frontend_bot.services.avatar_validator import validate_avatar_exists
from frontend_bot.shared.redis_client import redis_client
from frontend_bot.services.photo_buffer import get_buffered_photos_redis, clear_photo_buffer_redis
from frontend_bot.texts.avatar.texts import PHOTO_REQUIREMENTS_TEXT
from frontend_bot.services.avatar_workflow import create_draft_avatar
from frontend_bot.handlers.avatar.state import user_session
from frontend_bot.services.state_utils import set_state
from sqlalchemy.ext.asyncio import AsyncSession

async def show_type_menu(
    bot: AsyncTeleBot,
    chat_id: int,
    user_id: int,
    avatar_id: Optional[str] = None,
    session: Optional[AsyncSession] = None
) -> None:
    """
    Показывает меню выбора типа аватара.
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        user_id: ID пользователя
        avatar_id: ID аватара (опционально)
        session: Сессия БД (опционально)
    """
    if avatar_id:
        # Проверяем существование аватара
        if not await validate_avatar_exists(user_id, avatar_id, session):
            await bot.send_message(
                chat_id,
                "❌ Аватар не найден или у вас нет прав для его редактирования."
            )
            return
            
    await bot.send_message(
        chat_id,
        "Выберите тип аватара:",
        reply_markup=avatar_type_keyboard
    )

async def start_avatar_wizard(
    bot: AsyncTeleBot,
    chat_id: int,
    user_id: int,
    session: AsyncSession = None
) -> None:
    """
    Запускает визард создания аватара (единая FSM-логика).
    """
    import logging
    from uuid import uuid4
    from frontend_bot.services.avatar_manager import set_current_avatar_id
    from frontend_bot.handlers.avatar.photo_upload import get_buffered_photos_redis, flush_single_photo_buffer
    from frontend_bot.handlers.avatar.state import user_gallery
    logger = logging.getLogger(__name__)

    # Очищаем буфер фото при старте
    await clear_photo_buffer_redis(user_id)

    # Создаём черновик аватара
    if session is None:
        from database.config import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            avatar = await create_draft_avatar(user_id, session, {"photo_key": "", "preview_key": "", "avatar_data": {"step": 0}})
            avatar_id = str(avatar.id)
            await set_state(user_id, {"state": "avatar_photo_upload", "avatar_id": avatar_id}, session)
    else:
        avatar = await create_draft_avatar(user_id, session, {"photo_key": "", "preview_key": "", "avatar_data": {"step": 0}})
        avatar_id = str(avatar.id)
        await set_state(user_id, {"state": "avatar_photo_upload", "avatar_id": avatar_id}, session)

    # Полная инициализация структуры user_session
    user_session[user_id] = {
        "avatar_id": avatar_id,
        "wizard_message_ids": [],
        "last_wizard_state": None,
        "uploaded_photo_msgs": [],
        "last_error_msg": None,
        "last_info_msg_id": None,
        "edit_mode": "create",
    }
    # Инициализация структуры user_gallery
    gallery_key = f"{user_id}:{avatar_id}"
    user_gallery[gallery_key] = {"index": 0, "last_switch": 0}

    # Сбросить счетчик media group при старте нового аватара
    try:
        from frontend_bot.handlers.avatar.state import user_media_group_counter
        user_media_group_counter[user_id] = 0
    except Exception:
        pass

    # Обработка буфера фото (если есть)
    buffered_photos = await get_buffered_photos_redis(user_id)
    for obj in buffered_photos:
        await flush_single_photo_buffer(user_id, chat_id, avatar_id, session)

    # Установить avatar_id как текущий для пользователя
    set_current_avatar_id(user_id, avatar_id)

    # Отправить требования к фото
    await bot.send_message(
        chat_id,
        PHOTO_REQUIREMENTS_TEXT,
        parse_mode="HTML"
    ) 