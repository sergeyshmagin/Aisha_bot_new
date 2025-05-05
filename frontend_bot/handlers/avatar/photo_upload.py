# Обработчики загрузки фото для аватара
# Перенести сюда handle_avatar_photo_upload, flush_single_photo_buffer, flush_media_group
# Импортировать необходимые зависимости и утилиты из avatar_manager, state_manager, utils, config и т.д.

# ... переносить по аналогии ... 

import logging
import asyncio
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from frontend_bot.bot import bot
from frontend_bot.services.avatar_manager import (
    load_avatar_fsm, add_photo_to_avatar, save_avatar_fsm, validate_photo
)
from frontend_bot.services.state_manager import (
    get_state, get_current_avatar_id, set_state
)
from frontend_bot.handlers.avatar.utils import get_progressbar, delete_last_error_message
from frontend_bot.config import AVATAR_MAX_PHOTOS, AVATAR_MIN_PHOTOS
from frontend_bot.handlers.avatar.state import (
    user_session, user_gallery, user_single_photo_buffer, user_media_group_buffer, user_media_group_timers, user_single_photo_timer, user_locks
)

logger = logging.getLogger(__name__)

@bot.message_handler(content_types=['photo'])
async def handle_avatar_photo_upload(message: Message):
    user_id = message.from_user.id
    logger.info(f"[FSM] handle_avatar_photo_upload: user_id={user_id}, message_id={message.message_id}")
    state = get_state(user_id)
    avatar_id = get_current_avatar_id(user_id)
    logger.info(f"[FSM] handle_avatar_photo_upload: state={state}, avatar_id={avatar_id}")
    if state != "avatar_photo_upload" or not avatar_id:
        logger.info(f"[FSM] handle_avatar_photo_upload: state not valid or no avatar_id")
        return
    file_info = await bot.get_file(message.photo[-1].file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    media_group_id = getattr(message, 'media_group_id', None)
    logger.info(f"[FSM] handle_avatar_photo_upload: media_group_id={media_group_id}")
    # --- Если это media_group ---
    if media_group_id:
        if user_id not in user_media_group_buffer:
            user_media_group_buffer[user_id] = {}
        if media_group_id not in user_media_group_buffer[user_id]:
            user_media_group_buffer[user_id][media_group_id] = []
        user_media_group_buffer[user_id][media_group_id].append((message.photo[-1].file_id, downloaded_file, message.message_id))
        # Сбросить старый таймер, если был
        if user_id in user_media_group_timers and media_group_id in user_media_group_timers[user_id]:
            user_media_group_timers[user_id][media_group_id].cancel()
        # Запустить новый таймер
        task = asyncio.create_task(flush_media_group(user_id, media_group_id, message.chat.id, avatar_id))
        if user_id not in user_media_group_timers:
            user_media_group_timers[user_id] = {}
        user_media_group_timers[user_id][media_group_id] = task
        return
    # --- Если это одиночное фото (или forward пачкой) ---
    if user_id not in user_single_photo_buffer:
        user_single_photo_buffer[user_id] = []
    user_single_photo_buffer[user_id].append((message.photo[-1].file_id, downloaded_file, message.message_id))
    # Запустить таймер только если его нет или он завершён
    if user_id not in user_single_photo_timer or user_single_photo_timer[user_id].done():
        task = asyncio.create_task(flush_single_photo_buffer(user_id, message.chat.id, avatar_id))
        user_single_photo_timer[user_id] = task
    return

async def flush_single_photo_buffer(user_id, chat_id, avatar_id):
    logger.info(f"[FSM] flush_single_photo_buffer called for user_id={user_id}, avatar_id={avatar_id}")
    try:
        if user_id not in user_locks:
            user_locks[user_id] = asyncio.Lock()
        async with user_locks[user_id]:
            await asyncio.sleep(1.5)
            photos = user_single_photo_buffer.pop(user_id, [])
            logger.info(f"[FSM] flush_single_photo_buffer: {len(photos)} photos to process")
            for file_id, photo_bytes, msg_id in photos:
                logger.info(f"[FSM] flush_single_photo_buffer: Processing photo {file_id}")
                data = load_avatar_fsm(user_id, avatar_id)
                logger.info(f"[FSM] flush_single_photo_buffer: loaded data.json: {data}")
                existing_photos = data.get("photos", [])
                existing_paths = [p["path"] if isinstance(p, dict) else p for p in existing_photos]
                is_valid, result = validate_photo(photo_bytes, existing_paths)
                logger.info(f"[FSM] flush_single_photo_buffer: validate_photo: {is_valid}, {result}")
                if not is_valid:
                    await delete_last_error_message(user_id, chat_id)
                    # Всегда удаляем исходное фото
                    try:
                        await bot.delete_message(chat_id, msg_id)
                    except Exception:
                        pass
                    from io import BytesIO
                    text = None
                    if "Такое фото уже загружено" in result:
                        text = (
                            "⚠️ Фото не принято: Такое фото уже загружено.\n"
                            "📸 Совет: используйте чёткие фото без фильтров."
                        )
                    else:
                        text = f"⚠️ Фото не принято: {result}\n📸 Совет: используйте чёткие фото без фильтров."
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton("Понятно", callback_data="delete_error"))
                    await bot.send_photo(
                        chat_id,
                        BytesIO(photo_bytes),
                        caption=text,
                        reply_markup=markup
                    )
                    user_session[user_id]['last_error_msg'] = None
                    continue
                await delete_last_error_message(user_id, chat_id)
                logger.info(f"[FSM] flush_single_photo_buffer: calling add_photo_to_avatar")
                photo_path = add_photo_to_avatar(user_id, avatar_id, photo_bytes, file_id=file_id)
                logger.info(f"[FSM] flush_single_photo_buffer: Photo added at {photo_path}")
                data = load_avatar_fsm(user_id, avatar_id)
                logger.info(f"[FSM] flush_single_photo_buffer: data after add_photo: {data}")
                # update_photo_hint больше не вызываем здесь, так как галерея покажет прогресс
                data["photos"][-1] = {"path": photo_path, "file_id": file_id}
                save_avatar_fsm(user_id, avatar_id, data)
                logger.info(f"[FSM] flush_single_photo_buffer: data after save_avatar_fsm: {data}")
                # Удаляем исходное сообщение с фото
                try:
                    await bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass
            # После всей пачки — только обновить прогресс, не показывать галерею
            data = load_avatar_fsm(user_id, avatar_id)
            photos = data.get("photos", [])
            msg_id = user_session[user_id]['wizard_message_ids'][-1] if user_session[user_id]['wizard_message_ids'] else None
            # notify_progress и show_wizard_gallery должны быть импортированы из gallery.py
            # await notify_progress(chat_id, user_id, avatar_id, len(photos), msg_id)
            # Если достигнут лимит — показать галерею и перевести в review
            if len(photos) >= AVATAR_MAX_PHOTOS:
                set_state(user_id, "avatar_gallery_review")
                # await show_wizard_gallery(chat_id, user_id, avatar_id, photos, len(photos)-1 if photos else 0)
    except Exception as e:
        logger.error(f"Ошибка: {e}")

async def flush_media_group(user_id, media_group_id, chat_id, avatar_id):
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    async with user_locks[user_id]:
        logger.debug(f"[LOCK] user_id={user_id} lock acquired (media group)")
        await asyncio.sleep(1.5)
        photos = user_media_group_buffer[user_id].pop(media_group_id, [])
        for file_id, photo_bytes, msg_id in photos:
            data = load_avatar_fsm(user_id, avatar_id)
            existing_photos = data.get("photos", [])
            existing_paths = [p["path"] if isinstance(p, dict) else p for p in existing_photos]
            is_valid, result = validate_photo(photo_bytes, existing_paths)
            if not is_valid:
                await delete_last_error_message(user_id, chat_id)
                # Всегда удаляем исходное фото
                try:
                    await bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass
                from io import BytesIO
                text = None
                if "Такое фото уже загружено" in result:
                    text = (
                        "⚠️ Фото не принято: Такое фото уже загружено.\n"
                        "📸 Совет: используйте чёткие фото без фильтров."
                    )
                else:
                    text = f"⚠️ Фото не принято: {result}\n📸 Совет: используйте чёткие фото без фильтров."
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("Понятно", callback_data="delete_error"))
                await bot.send_photo(
                    chat_id,
                    BytesIO(photo_bytes),
                    caption=text,
                    reply_markup=markup
                )
                user_session[user_id]['last_error_msg'] = None
                continue
            await delete_last_error_message(user_id, chat_id)
            photo_path = add_photo_to_avatar(user_id, avatar_id, photo_bytes, file_id=file_id)
            data = load_avatar_fsm(user_id, avatar_id)
            data["photos"][-1] = {"path": photo_path, "file_id": file_id}
            save_avatar_fsm(user_id, avatar_id, data)
            # update_photo_hint больше не вызываем здесь, так как галерея покажет прогресс
            # Удаляем исходное сообщение с фото
            try:
                await bot.delete_message(chat_id, msg_id)
            except Exception:
                pass
        # После всей пачки — только обновить прогресс, не показывать галерею
        data = load_avatar_fsm(user_id, avatar_id)
        photos = data.get("photos", [])
        msg_id = user_session[user_id]['wizard_message_ids'][-1] if user_session[user_id]['wizard_message_ids'] else None
        # notify_progress и show_wizard_gallery должны быть импортированы из gallery.py
        # await notify_progress(chat_id, user_id, avatar_id, len(photos), msg_id)
        # Если достигнут лимит — показать галерею и перевести в review
        if len(photos) >= AVATAR_MAX_PHOTOS:
            set_state(user_id, "avatar_gallery_review")
            # await show_wizard_gallery(chat_id, user_id, avatar_id, photos, len(photos)-1 if photos else 0)
    logger.debug(f"[LOCK] user_id={user_id} lock released (media group)") 