# Обработчики загрузки фото для аватара
# Перенести сюда handle_avatar_photo_upload, flush_single_photo_buffer,
# flush_media_group
# Импортировать необходимые зависимости и утилиты из avatar_manager,
# state_utils, utils, config и т.д.

# ... переносить по аналогии ...

import asyncio
import logging
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from frontend_bot.bot_instance import bot
from frontend_bot.services.avatar_manager import (
    validate_photo,
    save_avatar_minio,
)
from frontend_bot.services.state_utils import set_state, get_state, clear_state
from frontend_bot.shared.utils import delete_last_error_message, send_photo_validation_error
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
)
from frontend_bot.services.avatar_manager import get_current_avatar_id
from sqlalchemy.ext.asyncio import AsyncSession
from database.config import AsyncSessionLocal
from frontend_bot.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

def with_session(handler):
    async def wrapper(message, *args, **kwargs):
        async with AsyncSessionLocal() as session:
            return await handler(message, session, *args, **kwargs)
    return wrapper

@bot.message_handler(content_types=["photo"])
@with_session
async def handle_avatar_photo_upload(message, session) -> None:
    """
    Обрабатывает загрузку фото пользователем. Валидация user_id, avatar_id.
    """
    telegram_id = getattr(message.from_user, "id", None)
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        logger.error("[handle_avatar_photo_upload] Не удалось найти пользователя по Telegram ID")
        await bot.send_message(
            message.chat.id, "Ошибка: не удалось определить пользователя."
        )
        return
    uuid_user_id = user.id
    state = await get_state(uuid_user_id, session)
    avatar_id = get_current_avatar_id(uuid_user_id)
    if not avatar_id:
        logger.error(
            f"[handle_avatar_photo_upload] Не найден avatar_id "
            f"для user_id={uuid_user_id}"
        )
        await bot.send_message(message.chat.id, "Ошибка: не найден аватар.")
        return
    logger.info(
        f"[FSM] handle_avatar_photo_upload: state={state}, " f"avatar_id={avatar_id}"
    )
    if not state or state.get("state") != "avatar_photo_upload" or not avatar_id:
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
        if uuid_user_id not in user_media_group_buffer:
            user_media_group_buffer[uuid_user_id] = {}
        if media_group_id not in user_media_group_buffer[uuid_user_id]:
            user_media_group_buffer[uuid_user_id][media_group_id] = []
        user_media_group_buffer[uuid_user_id][media_group_id].append(
            (message.photo[-1].file_id, downloaded_file, message.message_id)
        )
        # --- Добавляем message_id в общий список для этой группы ---
        if uuid_user_id not in user_media_group_msg_ids:
            user_media_group_msg_ids[uuid_user_id] = {}
        if media_group_id not in user_media_group_msg_ids[uuid_user_id]:
            user_media_group_msg_ids[uuid_user_id][media_group_id] = []
        user_media_group_msg_ids[uuid_user_id][media_group_id].append(message.message_id)
        # Сбросить старый таймер, если был
        if (
            uuid_user_id in user_media_group_timers
            and media_group_id in user_media_group_timers[uuid_user_id]
        ):
            user_media_group_timers[uuid_user_id][media_group_id].cancel()
        # Запустить новый таймер
        task = asyncio.create_task(
            flush_media_group(uuid_user_id, media_group_id, message.chat.id, avatar_id, session, db=session)
        )
        if uuid_user_id not in user_media_group_timers:
            user_media_group_timers[uuid_user_id] = {}
        user_media_group_timers[uuid_user_id][media_group_id] = task
        return
    # --- Если это одиночное фото (или forward пачкой) ---
    if uuid_user_id not in user_single_photo_buffer:
        user_single_photo_buffer[uuid_user_id] = []
    user_single_photo_buffer[uuid_user_id].append(
        (message.photo[-1].file_id, downloaded_file, message.message_id)
    )
    # Запустить таймер только если его нет или он завершён
    if (
        uuid_user_id not in user_single_photo_timer
        or user_single_photo_timer[uuid_user_id].done()
    ):
        task = asyncio.create_task(
            flush_single_photo_buffer(uuid_user_id, message.chat.id, avatar_id, session, db=session)
        )
        user_single_photo_timer[uuid_user_id] = task
    return


async def flush_single_photo_buffer(user_id, chat_id, avatar_id, session, db: AsyncSession = None):
    """
    Миграция: сохраняет фото аватара через MinIO/PostgreSQL (save_avatar_minio).
    Если db не передан — fallback на legacy add_photo_to_avatar.
    """
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
                # --- Валидация (оставляем как есть) ---
                photos = await get_avatar_photos_from_db(user_id, avatar_id, db)
                logger.info(
                    f"[FSM] flush_single_photo_buffer: " f"loaded data.json: {photos}"
                )
                existing_paths = photos
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
                    await send_photo_validation_error(bot, chat_id, photo_bytes, result)
                    user_session[user_id]["last_error_msg"] = None
                    continue
                await delete_last_error_message(bot, user_session, user_id, chat_id)
                logger.info(
                    f"[FSM] flush_single_photo_buffer: " f"calling save_avatar_minio"
                )
                if db is not None:
                    await save_avatar_minio(
                        db=db,
                        user_id=user_id,
                        avatar_id=avatar_id,
                        original=photo_bytes,
                        metadata={"file_id": file_id}
                    )
                    logger.info(f"[FSM] flush_single_photo_buffer: saved to MinIO/PostgreSQL (user_id={user_id}, avatar_id={avatar_id})")
                    photos = await get_avatar_photos_from_db(user_id, avatar_id, db)
                    logger.info(f"[FSM] flush_single_photo_buffer: data after save_avatar_minio: {photos}")
                    logger.info(f"[FSM] flush_single_photo_buffer: data['photos'] after save_avatar_minio: {photos}")
                else:
                    logger.error("[FSM] save_avatar_minio: db is None — невозможна работа без БД/MinIO!")
                    continue
                try:
                    await bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass
            photos = await get_avatar_photos_from_db(user_id, avatar_id, db)
            logger.info(f"[FSM] flush_single_photo_buffer: data['photos'] after all: {photos}")
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
                db=db
            )
            # Если достигнут максимум — меняем состояние
            if len(photos) >= settings.AVATAR_MAX_PHOTOS:
                await set_state(user_id, "avatar_gallery_review", session)
            logger.info(
                f"[DEBUG] flush_single_photo_buffer END: user_id={user_id}, "
                f"avatar_id={avatar_id}"
            )
    except Exception as e:
        logger.exception(f"Ошибка в flush_single_photo_buffer: {e}")


async def flush_media_group(user_id, media_group_id, chat_id, avatar_id, session, db: AsyncSession = None):
    """
    Миграция: сохраняет фото аватара через MinIO/PostgreSQL (save_avatar_minio) для media group.
    Если db не передан — fallback на legacy add_photo_to_avatar.
    """
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
            await asyncio.sleep(1.5)  # Ждем, пока все фото из группы придут
            
            # Собираем все фото из буфера
            photos = user_media_group_buffer[user_id].pop(media_group_id, [])
            logger.info(f"[DEBUG] flush_media_group: {len(photos)} photos to process")
            
            # Список для хранения успешно загруженных фото
            uploaded_photos = []
            
            # Загружаем все фото в MinIO
            for file_id, photo_bytes, msg_id in photos:
                logger.info(f"[DEBUG] flush_media_group: Processing photo {file_id}")
                photos = await get_avatar_photos_from_db(user_id, avatar_id, db)
                existing_paths = photos
                is_valid, result = await validate_photo(photo_bytes, existing_paths)
                if not is_valid:
                    await delete_last_error_message(bot, user_session, user_id, chat_id)
                    try:
                        await bot.delete_message(chat_id, msg_id)
                    except Exception:
                        pass
                    await send_photo_validation_error(bot, chat_id, photo_bytes, result)
                    user_session[user_id]["last_error_msg"] = None
                    continue
                    
                await delete_last_error_message(bot, user_session, user_id, chat_id)
                if db is not None:
                    try:
                        await save_avatar_minio(
                            db=db,
                            user_id=user_id,
                            avatar_id=avatar_id,
                            original=photo_bytes,
                            metadata={"file_id": file_id}
                        )
                        uploaded_photos.append((file_id, msg_id))
                        logger.info(f"[FSM] flush_media_group: saved to MinIO/PostgreSQL (user_id={user_id}, avatar_id={avatar_id})")
                    except Exception as e:
                        logger.error(f"[FSM] flush_media_group: error saving photo {file_id}: {e}")
                        continue
                else:
                    logger.error("[FSM] save_avatar_minio: db is None — невозможна работа без БД/MinIO!")
                    continue
                    
            # Удаляем все сообщения с фото
            for _, msg_id in uploaded_photos:
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
                await flush_media_group(user_id, media_group_id, chat_id, avatar_id, session, db=db)
                
            # Ждем немного, чтобы все операции с БД завершились
            await asyncio.sleep(1.0)
            
            # Загружаем финальное состояние и показываем галерею
            photos = await get_avatar_photos_from_db(user_id, avatar_id, db)
            logger.info(f"[FSM] flush_media_group: data['photos'] after all: {photos}")
            msg_id = (
                user_session[user_id]["wizard_message_ids"][-1]
                if user_id in user_session
                and user_session[user_id]["wizard_message_ids"]
                else None
            )
            
            # Показываем галерею после загрузки всех фото
            await show_wizard_gallery(
                chat_id,
                user_id,
                avatar_id,
                photos,
                len(photos) - 1 if photos else 0,
                db=db
            )
            
            # Если достигнут максимум — меняем состояние
            if len(photos) >= settings.AVATAR_MAX_PHOTOS:
                await set_state(user_id, "avatar_gallery_review", session)
                
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
