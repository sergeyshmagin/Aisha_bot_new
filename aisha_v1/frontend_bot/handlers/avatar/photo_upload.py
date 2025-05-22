"""
Загрузка фото для аватаров.
"""

import asyncio
import logging
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.async_telebot import AsyncTeleBot
from frontend_bot.bot_instance import bot
from frontend_bot.services.avatar_manager import (
    validate_photo,
    save_avatar_minio,
)
from frontend_bot.services.state_utils import set_state, get_state, clear_state
from frontend_bot.shared.utils import delete_last_error_message, send_photo_validation_error, get_or_update_user
from frontend_bot.handlers.avatar.gallery import show_wizard_gallery, get_avatar_photos_from_db
from frontend_bot.config import settings
from frontend_bot.handlers.avatar.state import (
    user_session,
    user_gallery,
    user_single_photo_buffer,
    user_media_group_buffer,
    user_media_group_timers,
    user_single_photo_timer,
    user_locks,
    user_media_group_msg_ids,
    get_gallery_key,
    get_media_group_key,
    safe_dict,
    user_last_gallery_msg,
    user_media_group_counter,
)
from frontend_bot.services.avatar_manager import get_current_avatar_id
from sqlalchemy.ext.asyncio import AsyncSession
from database.config import AsyncSessionLocal
from frontend_bot.repositories.user_repository import UserRepository
import hashlib
from frontend_bot.services.avatar_workflow import check_photo_duplicate, PhotoValidationError
from frontend_bot.services.avatar_validator import validate_avatar_exists, validate_avatar_photos
from frontend_bot.repositories.avatar_repository import UserAvatarRepository
from frontend_bot.shared.redis_client import redis_client
import base64
import json
from typing import Optional, List
from frontend_bot.handlers.avatar.navigation import show_type_menu
from frontend_bot.services.photo_buffer import get_buffered_photos_redis, buffer_photo_redis, clear_photo_buffer_redis

logger = logging.getLogger(__name__)

REDIS_PHOTO_TTL = 300  # 5 минут

def get_photo_buffer_key(user_id):
    return f"photo_buffer:{user_id}"

async def buffer_photo_redis(user_id, photo_bytes, meta):
    key = get_photo_buffer_key(user_id)
    data = {
        "photo": base64.b64encode(photo_bytes).decode(),
        "meta": meta,
    }
    await redis_client.lpush(key, json.dumps(data).encode())
    await redis_client.expire(key, REDIS_PHOTO_TTL)

async def get_buffered_photos_redis(user_id):
    key = get_photo_buffer_key(user_id)
    photos = []
    while True:
        data = await redis_client.rpop(key)
        if not data:
            break
        obj = json.loads(data)
        obj["photo"] = base64.b64decode(obj["photo"])
        photos.append(obj)
    return photos

async def clear_photo_buffer_redis(user_id):
    key = get_photo_buffer_key(user_id)
    await redis_client.delete(key)

def with_session(handler):
    async def wrapper(message, *args, **kwargs):
        async with AsyncSessionLocal() as session:
            return await handler(message, session, *args, **kwargs)
    return wrapper

photo_buffer = {}  # user_id -> list of (file_info, downloaded_file, message, media_group_id)

@bot.message_handler(content_types=["photo"])
@with_session
async def handle_avatar_photo_upload(message, session) -> None:
    """
    Обрабатывает загрузку фото пользователем.
    
    Args:
        message (Message): Объект сообщения
        session (AsyncSession): Сессия БД
    """
    user = await get_or_update_user(message, session)
    uuid_user_id = user.id
    state = await get_state(uuid_user_id, session)
    avatar_id = user_session.get(uuid_user_id, {}).get("avatar_id")
    if not avatar_id:
        logger.error(
            f"[handle_avatar_photo_upload] Не найден avatar_id "
            f"для user_id={uuid_user_id}"
        )
        await bot.send_message(message.chat.id, "Ошибка: не найден аватар.")
        return
    # --- NEW: Проверка существования аватара в БД ---
    avatar_repo = UserAvatarRepository(session)
    avatar = await avatar_repo.get_by_id(avatar_id)
    if not avatar:
        logger.warning(f"[photo_upload] avatar_id {avatar_id} не найден, фото буферизовано в Redis")
        file_info = await bot.get_file(message.photo[-1].file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        media_group_id = getattr(message, "media_group_id", None)
        meta = {
            "file_id": file_info.file_id,
            "message_id": message.message_id,
            "media_group_id": media_group_id,
            "chat_id": message.chat.id,
        }
        await buffer_photo_redis(uuid_user_id, downloaded_file, meta)
        return
    # --- END NEW ---
    logger.info(
        f"[FSM] handle_avatar_photo_upload: state={state}, " f"avatar_id={avatar_id}"
    )
    if not state or state.get("state") != "avatar_photo_upload" or not avatar_id:
        logger.info("[FSM] handle_avatar_photo_upload: state not valid or no avatar_id")
        return
    
    # Валидация аватара
    is_valid, msg = await validate_avatar_exists(uuid_user_id, avatar_id, session)
    if not is_valid:
        await bot.send_message(message.chat.id, f"Ошибка: {msg}")
        return
    
    # Получаем информацию о файле
    file_info = await bot.get_file(message.photo[-1].file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    
    # Проверяем, является ли фото частью группы
    media_group_id = getattr(message, "media_group_id", None)
    
    if media_group_id:
        # Добавляем фото в буфер группы
        if uuid_user_id not in user_media_group_buffer:
            user_media_group_buffer[uuid_user_id] = {}
        if media_group_id not in user_media_group_buffer[uuid_user_id]:
            user_media_group_buffer[uuid_user_id][media_group_id] = []
        user_media_group_buffer[uuid_user_id][media_group_id].append(
            (file_info.file_id, downloaded_file, message.message_id)
        )
        # Запускаем обработку группы
        asyncio.create_task(
            flush_media_group(
                uuid_user_id,
                message.chat.id,
                avatar_id,
                media_group_id,
                session
            )
        )
    else:
        # Добавляем фото в буфер одиночных фото
        if uuid_user_id not in user_single_photo_buffer:
            user_single_photo_buffer[uuid_user_id] = []
        user_single_photo_buffer[uuid_user_id].append(
            (file_info.file_id, downloaded_file, message.message_id)
        )
        # Отправляем сообщение о процессе обработки
        processing_msg = await bot.send_message(
            message.chat.id,
            "Обрабатываю фотографию... Это может занять несколько секунд ⏳"
        )

        # Запускаем обработку одиночного фото
        asyncio.create_task(
            flush_single_photo_buffer(
                uuid_user_id,
                message.chat.id,
                avatar_id,
                session
            )
        )
        
        # Только для одиночных фото вызываем галерею сразу
        await schedule_show_gallery(uuid_user_id, message.chat.id, avatar_id, session)
        
        # Удаляем сообщение об обработке
        try:
            await bot.delete_message(message.chat.id, processing_msg.message_id)
        except Exception as e:
            logger.warning(f"[Не удалось удалить сообщение об обработке: {e}]")

user_single_photo_processing = safe_dict()  # user_id -> bool
user_gallery_show_timer = safe_dict()  # user_id -> asyncio.Task
user_last_gallery_msg = safe_dict()  # user_id -> message_id
user_last_gallery_info_msg = safe_dict()  # user_id -> message_id последнего info-сообщения

# Настройки и их влияние на работу:
# 1. GALLERY_DEBOUNCE_TIMEOUT (6 сек) - время ожидания перед показом галереи:
#    - < 3 сек: пользователь может не успеть загрузить все фото
#    - > 10 сек: слишком долгое ожидание
#    - 6 сек: оптимально для загрузки 5-10 фото
# 2. user_media_group_counter - счетчик пакетов фото:
#    - Увеличивается при каждой загрузке
#    - Сбрасывается при перезапуске бота
#    - Помогает пользователю отслеживать прогресс
# 3. user_last_gallery_info_msg - ID последнего сообщения:
#    - Предотвращает дублирование сообщений
#    - Автоматически очищается после показа галереи
#    - Защищает от утечек памяти

async def schedule_show_gallery(user_id, chat_id, avatar_id, session):
    if user_id in user_gallery_show_timer and not user_gallery_show_timer[user_id].done():
        user_gallery_show_timer[user_id].cancel()
    async def show():
        # Удаляем предыдущее сообщение галереи, если есть
        msg_id = user_last_gallery_msg.get(user_id)
        if msg_id:
            try:
                await bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
            user_last_gallery_msg[user_id] = None
        await asyncio.sleep(settings.GALLERY_DEBOUNCE_TIMEOUT)
        photos = await get_avatar_photos_from_db(user_id, avatar_id, session)
        # Отправляем новую галерею и сохраняем её message_id
        sent = await show_wizard_gallery(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            avatar_id=avatar_id,
            photos=photos,
            idx=len(photos)-1 if photos else 0,
            session=session
        )
        if sent and hasattr(sent, 'message_id'):
            user_last_gallery_msg[user_id] = sent.message_id
    user_gallery_show_timer[user_id] = asyncio.create_task(show())

async def flush_single_photo_buffer(user_id, chat_id, avatar_id, session):
    """
    Обрабатывает буфер одиночных фото.
    
    Args:
        user_id (int): ID пользователя
        chat_id (int): ID чата
        avatar_id (str): ID аватара
        session (AsyncSession): Сессия БД
    """
    try:
        if user_id not in user_locks:
            user_locks[user_id] = asyncio.Lock()
        async with user_locks[user_id]:
            await asyncio.sleep(1.5)
            photos = user_single_photo_buffer.pop(user_id, [])
            for file_id, photo_bytes, msg_id in photos:
                await process_photo(user_id, chat_id, avatar_id, file_id, photo_bytes, msg_id, session)
    except Exception as e:
        logger.exception("Ошибка при обработке фото: %s", e)
        await bot.send_message(
            chat_id,
            "Произошла ошибка при обработке фото. Попробуйте позже."
        )
    await schedule_show_gallery(user_id, chat_id, avatar_id, session)

user_media_group_processing = safe_dict()  # user_id -> set(media_group_id)

async def flush_media_group(user_id, chat_id, avatar_id, media_group_id, session):
    """
    Обрабатывает буфер группы фото.
    
    Args:
        user_id (int): ID пользователя
        chat_id (int): ID чата
        avatar_id (str): ID аватара
        media_group_id (str): ID группы медиа
        session (AsyncSession): Сессия БД
    """
    try:
        if user_id not in user_locks:
            user_locks[user_id] = asyncio.Lock()
        async with user_locks[user_id]:
            await asyncio.sleep(1.5)
            photos = user_media_group_buffer[user_id].pop(media_group_id, [])
            for file_id, photo_bytes, msg_id in photos:
                await process_photo(user_id, chat_id, avatar_id, file_id, photo_bytes, msg_id, session)
    except Exception as e:
        logger.exception("Ошибка при обработке группы фото: %s", e)
        await bot.send_message(
            chat_id,
            "Произошла ошибка при обработке группы фото. Попробуйте позже."
        )
    finally:
        if user_id in user_media_group_processing:
            user_media_group_processing[user_id].discard(media_group_id)
    await schedule_show_gallery(user_id, chat_id, avatar_id, session)

@bot.callback_query_handler(func=lambda call: call.data == "delete_error")
async def handle_delete_error(call):
    try:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "photo_duplicate_ack")
async def handle_duplicate_ack(call):
    try:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    await bot.answer_callback_query(call.id)

# --- Кнопка 'Отменить' в галерее ---
def get_full_gallery_keyboard(idx, total, avatar_id, photos):
    markup = InlineKeyboardMarkup()
    # ... существующий код ...
    markup.row(
        InlineKeyboardButton("◀️ Назад", callback_data=f"avatar_gallery_prev:{avatar_id}"),
        InlineKeyboardButton("❌ Удалить", callback_data=f"avatar_gallery_delete:{photos[idx]['id']}"),
        InlineKeyboardButton("Вперёд ▶️", callback_data=f"avatar_gallery_next:{avatar_id}"),
    )
    markup.row(
        InlineKeyboardButton("❌ Отменить", callback_data=f"avatar_gallery_cancel:{avatar_id}")
    )
    if total >= settings.AVATAR_MIN_PHOTOS:
        markup.row(
            InlineKeyboardButton(
                "✅ Продолжить", callback_data=f"avatar_gallery_continue:{avatar_id}"
            )
        )
    return markup

# --- NEW: функция для обработки буфера после создания аватара ---
async def process_photo_buffer(user_id, avatar_id, session):
    if user_id in photo_buffer:
        logger.info(f"[photo_buffer] Обрабатываю {len(photo_buffer[user_id])} фото из буфера для user_id={user_id}")
        for file_info, downloaded_file, message, media_group_id in photo_buffer[user_id]:
            # Можно вызвать flush_single_photo_buffer или аналогичный код
            # Здесь пример для одиночных фото:
            await flush_single_photo_buffer(user_id, message.chat.id, avatar_id, session)
        del photo_buffer[user_id]

# --- Вызов process_photo_buffer после создания аватара ---
# В месте, где создаётся аватар (например, после create_draft_avatar):
# await process_photo_buffer(uuid_user_id, avatar_id, session)

# --- Очистка буфера при отмене визарда или завершении сессии ---
def clear_photo_buffer(user_id):
    if user_id in photo_buffer:
        del photo_buffer[user_id]

# --- ВНИМАНИЕ ---
# Эта функция НЕ занимается загрузкой фото! Она просто вызывает галерею после буферизации фото.
# Для бизнес-логики загрузки фото используйте сервисную функцию из avatar_workflow.py
async def handle_photo_upload_show_menu(
    bot: AsyncTeleBot,
    chat_id: int,
    user_id: int,
    avatar_id: Optional[str] = None,
    session: Optional[AsyncSession] = None
) -> None:
    """
    Показывает галерею после загрузки фото (НЕ сохраняет фото!).
    Используется только как шаг визарда.
    """
    # Получаем фото из буфера
    photos = await get_buffered_photos_redis(user_id)
    
    if not photos:
        await bot.send_message(
            chat_id,
            "❌ Не удалось получить фото из буфера."
        )
        return
        
    # Показываем галерею

async def process_photo(user_id, chat_id, avatar_id, file_id, photo_bytes, msg_id, session):
    # Общая логика обработки фото: валидация, сохранение, удаление сообщения и т.д.
    # Пример:
    existing_photos = await get_avatar_photos_from_db(user_id, avatar_id, session)
    is_valid, result = await validate_photo(photo_bytes, existing_photos)
    if not is_valid:
        await delete_last_error_message(bot, user_session, user_id, chat_id)
        try:
            await bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        await send_photo_validation_error(bot, chat_id, photo_bytes, result)
        user_session[user_id]["last_error_msg"] = None
        return False
    photo_hash = hashlib.md5(photo_bytes).hexdigest()
    await save_avatar_minio(session, user_id, avatar_id, photo_bytes, {"photo_hash": photo_hash})
    try:
        await bot.delete_message(chat_id, msg_id)
    except Exception:
        pass
    return True

async def restore_photo_buffers_on_start():
    pass
