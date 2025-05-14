# Обработчики загрузки фото для аватара
# Перенести сюда handle_avatar_photo_upload, flush_single_photo_buffer,
# flush_media_group
# Импортировать необходимые зависимости и утилиты из avatar_manager,
# state_manager, utils, config и т.д.

# ... переносить по аналогии ...

import asyncio
import logging
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from frontend_bot.bot import bot
from frontend_bot.services.avatar_manager import (
    load_avatar_fsm,
    add_photo_to_avatar,
    validate_photo,
    save_avatar_fsm,
)
from frontend_bot.services.state_manager import (
    get_state,
    get_current_avatar_id,
    set_state,
)
from frontend_bot.shared.utils import delete_last_error_message
from frontend_bot.handlers.avatar.gallery import show_wizard_gallery
from frontend_bot.config import AVATAR_MAX_PHOTOS
from frontend_bot.handlers.avatar.state import (
    user_session,
    user_gallery,
    user_single_photo_buffer,
    user_media_group_buffer,
    user_media_group_timers,
    user_single_photo_timer,
    user_locks,
    user_media_group_msg_ids,
)

logger = logging.getLogger(__name__)


@bot.message_handler(content_types=["photo"])
async def handle_avatar_photo_upload(message: Message) -> None:
    """
    Обрабатывает загрузку фото пользователем. Валидация user_id, avatar_id.
    """
    user_id = getattr(message.from_user, "id", None)
    if not isinstance(user_id, int):
        logger.error("[handle_avatar_photo_upload] Некорректный user_id")
        await bot.send_message(
            message.chat.id, "Ошибка: не удалось определить пользователя."
        )
        return
    state = await get_state(user_id)
    avatar_id = get_current_avatar_id(user_id)
    if not avatar_id:
        logger.error(
            f"[handle_avatar_photo_upload] Не найден avatar_id "
            f"для user_id={user_id}"
        )
        await bot.send_message(message.chat.id, "Ошибка: не найден аватар.")
        return
    logger.info(
        f"[FSM] handle_avatar_photo_upload: state={state}, " f"avatar_id={avatar_id}"
    )
    if state != "avatar_photo_upload" or not avatar_id:
        logger.info("[FSM] handle_avatar_photo_upload: state not valid or no avatar_id")
        return
    file_info = await bot.get_file(message.photo[-1].file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    media_group_id = getattr(message, "media_group_id", None)
    logger.info(
        f"[FSM] handle_avatar_photo_upload: " f"media_group_id={media_group_id}"
    )
    # --- Если это media_group ---
    if media_group_id:
        if user_id not in user_media_group_buffer:
            user_media_group_buffer[user_id] = {}
        if media_group_id not in user_media_group_buffer[user_id]:
            user_media_group_buffer[user_id][media_group_id] = []
        user_media_group_buffer[user_id][media_group_id].append(
            (message.photo[-1].file_id, downloaded_file, message.message_id)
        )
        # --- Добавляем message_id в общий список для этой группы ---
        if user_id not in user_media_group_msg_ids:
            user_media_group_msg_ids[user_id] = {}
        if media_group_id not in user_media_group_msg_ids[user_id]:
            user_media_group_msg_ids[user_id][media_group_id] = []
        user_media_group_msg_ids[user_id][media_group_id].append(message.message_id)
        # Сбросить старый таймер, если был
        if (
            user_id in user_media_group_timers
            and media_group_id in user_media_group_timers[user_id]
        ):
            user_media_group_timers[user_id][media_group_id].cancel()
        # Запустить новый таймер
        task = asyncio.create_task(
            flush_media_group(user_id, media_group_id, message.chat.id, avatar_id)
        )
        if user_id not in user_media_group_timers:
            user_media_group_timers[user_id] = {}
        user_media_group_timers[user_id][media_group_id] = task
        return
    # --- Если это одиночное фото (или forward пачкой) ---
    if user_id not in user_single_photo_buffer:
        user_single_photo_buffer[user_id] = []
    user_single_photo_buffer[user_id].append(
        (message.photo[-1].file_id, downloaded_file, message.message_id)
    )
    # Запустить таймер только если его нет или он завершён
    if (
        user_id not in user_single_photo_timer
        or user_single_photo_timer[user_id].done()
    ):
        task = asyncio.create_task(
            flush_single_photo_buffer(user_id, message.chat.id, avatar_id)
        )
        user_single_photo_timer[user_id] = task
    return


async def flush_single_photo_buffer(user_id, chat_id, avatar_id):
    user_session.setdefault(
        user_id,
        {
            "wizard_message_ids": [],
            "last_wizard_state": None,
            "uploaded_photo_msgs": [],
            "last_error_msg": None,
            "last_info_msg_id": None,
        },
    )
    logger.info(
        f"[DEBUG] flush_single_photo_buffer START: user_id={user_id}, avatar_id={avatar_id}"
    )
    try:
        if user_id not in user_locks:
            user_locks[user_id] = asyncio.Lock()
        async with user_locks[user_id]:
            await asyncio.sleep(1.5)
            photos = user_single_photo_buffer.pop(user_id, [])
            logger.info(
                f"[DEBUG] flush_single_photo_buffer: "
                f"{len(photos)} photos to process"
            )
            for file_id, photo_bytes, msg_id in photos:
                logger.info(
                    f"[DEBUG] flush_single_photo_buffer: " f"Processing photo {file_id}"
                )
                data = await load_avatar_fsm(user_id, avatar_id)
                logger.info(
                    f"[FSM] flush_single_photo_buffer: " f"loaded data.json: {data}"
                )
                existing_photos = data.get("photos", [])
                existing_paths = [
                    p["path"] if isinstance(p, dict) else p for p in existing_photos
                ]
                is_valid, result = await validate_photo(photo_bytes, existing_paths)
                logger.info(
                    f"[FSM] flush_single_photo_buffer: "
                    f"validate_photo: {is_valid}, {result}"
                )
                if not is_valid:
                    await delete_last_error_message(bot, user_session, user_id, chat_id)
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
                        text = (
                            f"⚠️ Фото не принято: {result}\n"
                            "📸 Совет: используйте чёткие фото без фильтров."
                        )
                    markup = InlineKeyboardMarkup()
                    markup.add(
                        InlineKeyboardButton("Понятно", callback_data="delete_error")
                    )
                    await bot.send_photo(
                        chat_id, BytesIO(photo_bytes), caption=text, reply_markup=markup
                    )
                    user_session[user_id]["last_error_msg"] = None
                    continue
                await delete_last_error_message(bot, user_session, user_id, chat_id)
                logger.info(
                    f"[FSM] flush_single_photo_buffer: " f"calling add_photo_to_avatar"
                )
                photo_path = await add_photo_to_avatar(
                    user_id, avatar_id, photo_bytes, file_id=file_id
                )
                logger.info(
                    f"[FSM] flush_single_photo_buffer: " f"Photo added at {photo_path}"
                )
                data = await load_avatar_fsm(user_id, avatar_id)
                logger.info(
                    f"[FSM] flush_single_photo_buffer: " f"data after add_photo: {data}"
                )
                data["photos"][-1] = {"path": photo_path, "file_id": file_id}
                await save_avatar_fsm(user_id, avatar_id, data)
                logger.info(
                    f"[FSM] flush_single_photo_buffer: "
                    f"data after save_avatar_fsm: {data}"
                )
                try:
                    await bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass
            data = await load_avatar_fsm(user_id, avatar_id)
            photos = data.get("photos", [])
            msg_id = (
                user_session[user_id]["wizard_message_ids"][-1]
                if user_id in user_session
                and user_session[user_id]["wizard_message_ids"]
                else None
            )
            # Показываем галерею после каждого добавления фото
            await show_wizard_gallery(
                chat_id,
                user_id,
                avatar_id,
                photos,
                len(photos) - 1 if photos else 0,
            )
            # Если достигнут максимум — меняем состояние
            if len(photos) >= AVATAR_MAX_PHOTOS:
                await set_state(user_id, "avatar_gallery_review")
            logger.info(
                f"[DEBUG] flush_single_photo_buffer END: user_id={user_id}, "
                f"avatar_id={avatar_id}"
            )
    except Exception as e:
        logger.exception(f"Ошибка в flush_single_photo_buffer: {e}")


async def flush_media_group(user_id, media_group_id, chat_id, avatar_id):
    user_session.setdefault(
        user_id,
        {
            "wizard_message_ids": [],
            "last_wizard_state": None,
            "uploaded_photo_msgs": [],
            "last_error_msg": None,
            "last_info_msg_id": None,
        },
    )
    logger.info(
        f"[DEBUG] flush_media_group START: user_id={user_id}, media_group_id={media_group_id}, avatar_id={avatar_id}"
    )
    try:
        if user_id not in user_locks:
            user_locks[user_id] = asyncio.Lock()
        async with user_locks[user_id]:
            logger.debug(f"[LOCK] user_id={user_id} lock acquired (media group)")
            await asyncio.sleep(1.5)
            photos = user_media_group_buffer[user_id].pop(media_group_id, [])
            logger.info(f"[DEBUG] flush_media_group: {len(photos)} photos to process")
            for file_id, photo_bytes, msg_id in photos:
                logger.info(f"[DEBUG] flush_media_group: Processing photo {file_id}")
                data = await load_avatar_fsm(user_id, avatar_id)
                existing_photos = data.get("photos", [])
                existing_paths = [
                    p["path"] if isinstance(p, dict) else p for p in existing_photos
                ]
                is_valid, result = await validate_photo(photo_bytes, existing_paths)
                if not is_valid:
                    await delete_last_error_message(bot, user_session, user_id, chat_id)
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
                        text = (
                            f"⚠️ Фото не принято: {result}\n"
                            "📸 Совет: используйте чёткие фото без фильтров."
                        )
                    markup = InlineKeyboardMarkup()
                    markup.add(
                        InlineKeyboardButton("Понятно", callback_data="delete_error")
                    )
                    await bot.send_photo(
                        chat_id, BytesIO(photo_bytes), caption=text, reply_markup=markup
                    )
                    user_session[user_id]["last_error_msg"] = None
                    continue
                await delete_last_error_message(bot, user_session, user_id, chat_id)
                photo_path = await add_photo_to_avatar(
                    user_id, avatar_id, photo_bytes, file_id=file_id
                )
                data = await load_avatar_fsm(user_id, avatar_id)
                data["photos"][-1] = {"path": photo_path, "file_id": file_id}
                await save_avatar_fsm(user_id, avatar_id, data)
                try:
                    await bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass
            # --- После обработки удаляем все сообщения этой группы ---
            msg_ids = user_media_group_msg_ids.get(user_id, {}).get(media_group_id, [])
            for mid in msg_ids:
                try:
                    await bot.delete_message(chat_id, mid)
                except Exception:
                    pass
            # Очищаем список message_id для этой группы
            if (
                user_id in user_media_group_msg_ids
                and media_group_id in user_media_group_msg_ids[user_id]
            ):
                user_media_group_msg_ids[user_id][media_group_id] = []
            # --- Проверяем, не появились ли новые фото с этим media_group_id ---
            if (
                user_id in user_media_group_buffer
                and media_group_id in user_media_group_buffer[user_id]
                and user_media_group_buffer[user_id][media_group_id]
            ):
                logger.info(
                    f"[DEBUG] flush_media_group: обнаружены новые фото, "
                    f"повторный запуск через 0.5 сек"
                )
                await asyncio.sleep(0.5)
                await flush_media_group(user_id, media_group_id, chat_id, avatar_id)
            data = await load_avatar_fsm(user_id, avatar_id)
            photos = data.get("photos", [])
            msg_id = (
                user_session[user_id]["wizard_message_ids"][-1]
                if user_id in user_session
                and user_session[user_id]["wizard_message_ids"]
                else None
            )
            # Показываем галерею после каждого добавления фото
            await show_wizard_gallery(
                chat_id,
                user_id,
                avatar_id,
                photos,
                len(photos) - 1 if photos else 0,
            )
            # Если достигнут максимум — меняем состояние
            if len(photos) >= AVATAR_MAX_PHOTOS:
                await set_state(user_id, "avatar_gallery_review")
            logger.info(
                f"[DEBUG] flush_media_group END: user_id={user_id}, "
                f"media_group_id={media_group_id}, avatar_id={avatar_id}"
            )
    except Exception as e:
        logger.exception(f"Ошибка в flush_media_group: {e}")
    logger.debug(f"[LOCK] user_id={user_id} lock released (media group)")


@bot.callback_query_handler(func=lambda call: call.data == "delete_error")
async def handle_delete_error(call):
    try:
        await bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    await bot.answer_callback_query(call.id)
