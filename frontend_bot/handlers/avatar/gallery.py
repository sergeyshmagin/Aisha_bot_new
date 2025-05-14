# Модуль галереи для аватаров
# Перенести сюда show_wizard_gallery, get_full_gallery_keyboard,
# handle_gallery_prev, handle_gallery_next, handle_gallery_delete,
# handle_gallery_add, handle_gallery_continue, handle_show_photos
# Импортировать необходимые зависимости и утилиты из avatar_manager,
# state_manager, utils, config и т.д.

import logging
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)
from frontend_bot.config import AVATAR_MIN_PHOTOS
from frontend_bot.shared.progress import get_progressbar
from frontend_bot.handlers.avatar.state import user_session, user_gallery
from frontend_bot.bot import bot
import aiofiles
from io import BytesIO
import time
from frontend_bot.texts.common import (
    ERROR_NO_PHOTOS,
    ERROR_USER_AVATAR,
    ERROR_INDEX,
    get_gallery_caption,
    PROMPT_AVATAR_CANCELLED,
)
from frontend_bot.services.avatar_manager import (
    load_avatar_fsm,
    remove_photo_from_avatar,
    get_avatars_index,
    update_avatar_in_index,
    remove_avatar_from_index,
    update_avatar_fsm,
)
from frontend_bot.services.state_manager import (
    get_current_avatar_id,
    set_state,
    fsm_states,
)
from frontend_bot.utils.validators import validate_user_avatar
from frontend_bot.keyboards.common import get_gallery_keyboard
from frontend_bot.handlers.avatar.fsm import show_type_menu, start_avatar_wizard
from frontend_bot.shared.utils import clear_old_wizard_messages
from frontend_bot.keyboards.reply import (
    ai_photographer_keyboard,
    my_avatars_keyboard,
)
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Клавиатура галереи


def get_full_gallery_keyboard(idx, total):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("◀️ Назад", callback_data="avatar_gallery_prev"),
        InlineKeyboardButton("❌ Удалить", callback_data="avatar_gallery_delete"),
    )
    markup.row(InlineKeyboardButton("Вперёд ▶️", callback_data="avatar_gallery_next"))
    if total >= AVATAR_MIN_PHOTOS:
        markup.row(
            InlineKeyboardButton(
                "✅ Продолжить", callback_data="avatar_gallery_continue"
            )
        )
    markup.row(InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel"))
    return markup


async def show_wizard_gallery(
    chat_id: int,
    user_id: int,
    avatar_id: str,
    photos: list,
    idx: int,
    message_id: int = None,
) -> None:
    """
    Показывает галерею фото для аватара в визарде.
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
    if not isinstance(user_id, int) or not avatar_id:
        logger.error(
            f"[show_wizard_gallery] Некорректные user_id или avatar_id: "
            f"{user_id}, {avatar_id}"
        )
        return
    if not isinstance(photos, list):
        logger.error(
            f"[show_wizard_gallery] photos не list: {type(photos)}"
        )
        return
    if not photos:
        await bot.send_message(chat_id, ERROR_NO_PHOTOS)
        return
    idx = max(0, min(idx, len(photos) - 1))
    user_gallery.setdefault((user_id, avatar_id), {"index": 0, "last_switch": 0})
    user_gallery[(user_id, avatar_id)]["index"] = idx
    photo = photos[idx]
    if isinstance(photo, dict):
        file_id = photo.get("file_id")
        photo_path = photo.get("path")
    else:
        file_id = None
        photo_path = photo
    total = len(photos)
    caption = get_gallery_caption(idx, total)
    keyboard = get_gallery_keyboard(idx, total)
    last = user_session[user_id]["last_wizard_state"]
    logger.info(f"[show_wizard_gallery] last_wizard_state={last}")
    if last and last[0] == caption and last[1].to_dict() == keyboard.to_dict():
        logger.info(
            "[show_wizard_gallery] return: no change (gallery)"
        )
        return
    if message_id:
        try:
            if file_id:
                await bot.edit_message_media(
                    media=InputMediaPhoto(
                        file_id, caption=caption, parse_mode="HTML"
                    ),
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=keyboard,
                )
            else:
                async with aiofiles.open(photo_path, "rb") as img:
                    img_bytes = await img.read()
                    img_stream = BytesIO(img_bytes)
                    await bot.edit_message_media(
                        media=InputMediaPhoto(
                            img_stream, caption=caption, parse_mode="HTML"
                        ),
                        chat_id=chat_id,
                        message_id=message_id,
                        reply_markup=keyboard,
                    )
            await clear_old_wizard_messages(
                bot, user_session, chat_id, user_id, keep_msg_id=message_id
            )
            user_session[user_id]["last_wizard_state"] = (caption, keyboard)
            logger.info(
                "[show_wizard_gallery] return: edit_message_media"
            )
        except Exception as e:
            logger.exception(f"[show_wizard_gallery] Exception: {e}")
            if file_id:
                msg = await bot.send_photo(
                    chat_id,
                    file_id,
                    caption=caption,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
            else:
                async with aiofiles.open(photo_path, "rb") as img:
                    img_bytes = await img.read()
                    img_stream = BytesIO(img_bytes)
                    msg = await bot.send_photo(
                        chat_id,
                        img_stream,
                        caption=caption,
                        reply_markup=keyboard,
                        parse_mode="HTML",
                    )
            await clear_old_wizard_messages(
                bot, user_session, chat_id, user_id, keep_msg_id=msg.message_id
            )
            user_session[user_id]["wizard_message_ids"] = [msg.message_id]
            user_session[user_id]["last_wizard_state"] = (caption, keyboard)
            logger.info(
                "[show_wizard_gallery] return: send_photo after exception"
            )
    else:
        if file_id:
            msg = await bot.send_photo(
                chat_id,
                file_id,
                caption=caption,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        else:
            async with aiofiles.open(photo_path, "rb") as img:
                img_bytes = await img.read()
                img_stream = BytesIO(img_bytes)
                msg = await bot.send_photo(
                    chat_id,
                    img_stream,
                    caption=caption,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
        await clear_old_wizard_messages(
            bot, user_session, chat_id, user_id, keep_msg_id=msg.message_id
        )
        user_session[user_id]["wizard_message_ids"] = [msg.message_id]
        user_session[user_id]["last_wizard_state"] = (caption, keyboard)
        logger.info(
            "[show_wizard_gallery] return: send_photo (new message)"
        )


# Остальные функции и обработчики галереи:
# show_wizard_gallery, handle_gallery_prev, handle_gallery_next,
# handle_gallery_delete, handle_gallery_add, handle_gallery_continue,
# handle_show_photos переносить по аналогии...


@bot.callback_query_handler(func=lambda call: call.data == "avatar_gallery_prev")
@validate_user_avatar
async def handle_gallery_prev(call) -> None:
    user_id = getattr(call.from_user, "id", None)
    avatar_id = get_current_avatar_id(user_id)
    if not isinstance(user_id, int) or not avatar_id:
        await bot.send_message(call.message.chat.id, ERROR_USER_AVATAR)
        await bot.answer_callback_query(call.id)
        return
    data = await load_avatar_fsm(user_id, avatar_id)
    photos = data.get("photos", [])
    if not photos:
        await bot.send_message(call.message.chat.id, "Нет фото для отображения.")
        await bot.answer_callback_query(call.id)
        return
    if user_id not in user_session:
        user_session[user_id] = {
            "wizard_message_ids": [],
            "last_wizard_state": None,
            "uploaded_photo_msgs": [],
            "last_error_msg": None,
            "last_info_msg_id": None,
        }
    idx = user_gallery.get((user_id, avatar_id), {}).get("index", 0)
    if not (0 <= idx < len(photos)):
        await bot.send_message(call.message.chat.id, ERROR_INDEX)
        await bot.answer_callback_query(call.id)
        return
    now = time.monotonic()
    last = user_gallery[(user_id, avatar_id)]["last_switch"]
    if now - last < 0.7:
        await bot.answer_callback_query(call.id, "Слишком быстро!")
        return
    user_gallery[(user_id, avatar_id)]["last_switch"] = now
    if idx <= 0:
        idx = len(photos) - 1
    else:
        idx -= 1
    await show_wizard_gallery(
        call.message.chat.id,
        user_id,
        avatar_id,
        photos,
        idx,
        message_id=call.message.message_id,
    )
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "avatar_gallery_next")
@validate_user_avatar
async def handle_gallery_next(call) -> None:
    user_id = getattr(call.from_user, "id", None)
    avatar_id = get_current_avatar_id(user_id)
    if not isinstance(user_id, int) or not avatar_id:
        await bot.send_message(call.message.chat.id, ERROR_USER_AVATAR)
        await bot.answer_callback_query(call.id)
        return
    data = await load_avatar_fsm(user_id, avatar_id)
    photos = data.get("photos", [])
    if not photos:
        await bot.send_message(call.message.chat.id, "Нет фото для отображения.")
        await bot.answer_callback_query(call.id)
        return
    if user_id not in user_session:
        user_session[user_id] = {
            "wizard_message_ids": [],
            "last_wizard_state": None,
            "uploaded_photo_msgs": [],
            "last_error_msg": None,
            "last_info_msg_id": None,
        }
    idx = user_gallery.get((user_id, avatar_id), {}).get("index", 0)
    if not (0 <= idx < len(photos)):
        await bot.send_message(call.message.chat.id, ERROR_INDEX)
        await bot.answer_callback_query(call.id)
        return
    now = time.monotonic()
    last = user_gallery[(user_id, avatar_id)]["last_switch"]
    if now - last < 0.7:
        await bot.answer_callback_query(call.id, "Слишком быстро!")
        return
    user_gallery[(user_id, avatar_id)]["last_switch"] = now
    if idx >= len(photos) - 1:
        idx = 0
    else:
        idx += 1
    await show_wizard_gallery(
        call.message.chat.id,
        user_id,
        avatar_id,
        photos,
        idx,
        message_id=call.message.message_id,
    )
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "avatar_gallery_delete")
@validate_user_avatar
async def handle_gallery_delete(call) -> None:
    user_id = getattr(call.from_user, "id", None)
    avatar_id = get_current_avatar_id(user_id)
    logger.info(f"[handle_gallery_delete] user_id={user_id}, avatar_id={avatar_id}")
    if not isinstance(user_id, int) or not avatar_id:
        await bot.send_message(call.message.chat.id, ERROR_USER_AVATAR)
        await bot.answer_callback_query(call.id)
        return
    data = await load_avatar_fsm(user_id, avatar_id)
    logger.info(f"[handle_gallery_delete] loaded data: {data}")
    photos = data.get("photos", [])
    if user_id not in user_session:
        user_session[user_id] = {
            "wizard_message_ids": [],
            "last_wizard_state": None,
            "uploaded_photo_msgs": [],
            "last_error_msg": None,
            "last_info_msg_id": None,
        }
    idx = user_gallery.get((user_id, avatar_id), {}).get("index", 0)
    logger.info(f"[handle_gallery_delete] idx={idx}, photos={photos}")
    if not photos or not (0 <= idx < len(photos)):
        await bot.send_message(call.message.chat.id, ERROR_INDEX)
        await bot.answer_callback_query(call.id)
        return
    await remove_photo_from_avatar(user_id, avatar_id, idx)
    logger.info(f"[handle_gallery_delete] photo removed at idx={idx}")
    data = await load_avatar_fsm(user_id, avatar_id)
    logger.info(f"[handle_gallery_delete] data after remove: {data}")
    photos = data.get("photos", [])
    if not photos:
        try:
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        await clear_old_wizard_messages(
            bot, user_session, call.message.chat.id, user_id
        )
        import asyncio

        await asyncio.sleep(0.5)
        return
    new_idx = min(idx, len(photos) - 1)
    user_gallery[(user_id, avatar_id)]["index"] = new_idx
    logger.info(f"[handle_gallery_delete] show_wizard_gallery new_idx={new_idx}")
    await show_wizard_gallery(
        call.message.chat.id,
        user_id,
        avatar_id,
        photos,
        new_idx,
        message_id=call.message.message_id,
    )
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "avatar_gallery_continue")
async def handle_gallery_continue(call):
    user_id = call.from_user.id
    await show_type_menu(call.message.chat.id, user_id)
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "avatar_show_photos")
async def handle_show_photos(call):
    user_id = call.from_user.id
    avatar_id = get_current_avatar_id(user_id)
    data = await load_avatar_fsm(user_id, avatar_id)
    photos = data.get("photos", [])
    if not photos:
        await bot.send_message(call.message.chat.id, "У вас пока нет загруженных фото.")
    else:
        await show_wizard_gallery(call.message.chat.id, user_id, avatar_id, photos, 0)
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "avatar_gallery_add")
async def handle_gallery_add(call):
    # Не отправляем отдельное сообщение, просто уведомляем пользователя
    await bot.answer_callback_query(call.id, "Ждём новое фото...")


@bot.callback_query_handler(func=lambda call: call.data == "avatar_cancel")
async def handle_avatar_cancel(call):
    user_id = getattr(call.from_user, "id", None)
    from frontend_bot.handlers.avatar.fsm import reset_avatar_fsm

    # Очищаем сообщения визарда
    if user_id in user_session:
        msg_ids = user_session[user_id].get("wizard_message_ids", [])
        for mid in msg_ids:
            try:
                await bot.delete_message(call.message.chat.id, mid)
            except Exception:
                pass
    reset_avatar_fsm(user_id)
    await bot.send_message(
        call.message.chat.id, PROMPT_AVATAR_CANCELLED, parse_mode="HTML"
    )
    await bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda m: m.text == "🧑‍🎨 ИИ фотограф")
async def ai_photographer_menu(message):
    await set_state(message.from_user.id, "ai_photographer")
    await bot.send_message(
        message.chat.id,
        "🧑‍🎨 ИИ фотограф\n\nСоздавайте аватары и образы с помощью ИИ.",
        reply_markup=ai_photographer_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "🖼 Мои аватары")
async def my_avatars_menu(message):
    await bot.send_message(
        message.chat.id,
        "Меню аватаров:",
        reply_markup=my_avatars_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "📷 Создать аватар")
async def create_avatar_handler(message):
    await start_avatar_wizard(message)


async def send_avatar_card(chat_id, user_id, avatars, idx=0):
    if not avatars:
        await bot.send_message(chat_id, "У вас нет аватаров.")
        return
    avatar = avatars[idx]
    avatar_id = avatar["avatar_id"]
    title = avatar.get("title", "Без имени")
    created_at = avatar.get("created_at", "-")
    status = avatar.get("status", "-")
    is_main = avatar.get("is_main", False)
    preview_path = avatar.get("preview_path")
    # Формируем текст карточки
    dt = datetime.fromisoformat(created_at) if created_at and created_at != "-" else None
    date_str = dt.strftime("%d.%m.%Y %H:%M") if dt else "-"
    status_str = "⏳ Обучается" if status == "pending" else status
    main_str = "⭐ Основной" if is_main else ""
    text = (
        f"<b>{title}</b>\n"
        f"🗓 {date_str}\n"
        f"⚡ Статус: {status_str}\n"
        f"{main_str}\n"
        f"({idx+1} из {len(avatars)})"
    )
    # Клавиатура
    kb = InlineKeyboardMarkup(row_width=3)
    kb.row(
        InlineKeyboardButton("⬅️", callback_data=f"avatar_card_prev_{idx}"),
        InlineKeyboardButton(f"{idx+1} из {len(avatars)}", callback_data="noop"),
        InlineKeyboardButton("➡️", callback_data=f"avatar_card_next_{idx}"),
    )
    kb.row(
        InlineKeyboardButton("⭐", callback_data=f"avatar_card_main_{avatar_id}"),
        InlineKeyboardButton("✏️", callback_data=f"avatar_card_edit_{avatar_id}"),
        InlineKeyboardButton("🗑", callback_data=f"avatar_card_delete_{avatar_id}"),
    )
    kb.row(InlineKeyboardButton("↩️ В меню", callback_data="avatar_card_menu"))
    # Отправляем превью (если есть) и карточку
    if preview_path and os.path.exists(preview_path):
        with open(preview_path, "rb") as img:
            await bot.send_photo(chat_id, img, caption=text, parse_mode="HTML", reply_markup=kb)
    else:
        await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)


@bot.message_handler(func=lambda m: m.text == "👁 Просмотреть аватары")
async def view_avatars_handler(message):
    user_id = message.from_user.id
    avatars = await get_avatars_index(user_id)
    if not avatars:
        await bot.send_message(
            message.chat.id,
            (
                "У вас пока нет аватаров. "
                "Нажмите '📷 Создать аватар', чтобы начать!"
            ),
            reply_markup=my_avatars_keyboard(),
        )
        return
    # Показываем карточку первого (или основного) аватара
    idx = 0
    for i, a in enumerate(avatars):
        if a.get("is_main"):
            idx = i
            break
    await send_avatar_card(message.chat.id, user_id, avatars, idx)


@bot.message_handler(func=lambda m: m.text == "🖼 Образы")
async def my_images_menu(message):
    # TODO: заменить на реальный сервис получения образов пользователя
    await bot.send_message(
        message.chat.id,
        "У вас пока нет образов. Функция в разработке.",
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("avatar_card_prev_")
)
async def handle_avatar_card_prev(call):
    """Обработчик кнопки "Предыдущий аватар" в карточке аватара."""
    user_id = call.from_user.id
    try:
        idx = int(call.data.split("_")[-1])
        avatars = await get_avatars_index(user_id)
        if not avatars:
            await bot.answer_callback_query(
                call.id,
                "Нет доступных аватаров"
            )
            return
        new_idx = len(avatars) - 1 if idx <= 0 else idx - 1
        await send_avatar_card(
            call.message.chat.id,
            user_id,
            avatars,
            new_idx
        )
        try:
            await bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )
        except Exception:
            pass
    except Exception as e:
        logger.exception(
            "Error in handle_avatar_card_prev: %s",
            e
        )
        await bot.answer_callback_query(call.id, "Произошла ошибка")
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("avatar_card_next_")
)
async def handle_avatar_card_next(call):
    """Обработчик кнопки "Следующий аватар" в карточке аватара."""
    user_id = call.from_user.id
    try:
        idx = int(call.data.split("_")[-1])
        avatars = await get_avatars_index(user_id)
        if not avatars:
            await bot.answer_callback_query(
                call.id,
                "Нет доступных аватаров"
            )
            return
        new_idx = 0 if idx >= len(avatars) - 1 else idx + 1
        await send_avatar_card(
            call.message.chat.id,
            user_id,
            avatars,
            new_idx
        )
        try:
            await bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )
        except Exception:
            pass
    except Exception as e:
        logger.exception(
            "Error in handle_avatar_card_next: %s",
            e
        )
        await bot.answer_callback_query(call.id, "Произошла ошибка")
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("avatar_card_main_")
)
async def handle_avatar_card_main(call):
    """Обработчик кнопки "Сделать основным" в карточке аватара."""
    user_id = call.from_user.id
    try:
        avatar_id = call.data.split("_")[-1]
        avatars = await get_avatars_index(user_id)
        if not avatars:
            await bot.answer_callback_query(
                call.id,
                "Нет доступных аватаров"
            )
            return
        
        # Находим текущий индекс
        current_idx = 0
        for i, a in enumerate(avatars):
            if a["avatar_id"] == avatar_id:
                current_idx = i
                break
        
        # Обновляем статус основного аватара
        await update_avatar_in_index(
            user_id,
            avatar_id,
            {"is_main": True}
        )
        
        # Обновляем карточку
        avatars = await get_avatars_index(user_id)
        await send_avatar_card(
            call.message.chat.id,
            user_id,
            avatars,
            current_idx
        )
        try:
            await bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )
        except Exception:
            pass
        await bot.answer_callback_query(
            call.id,
            "Установлен как основной аватар"
        )
    except Exception as e:
        logger.exception(
            "Error in handle_avatar_card_main: %s",
            e
        )
        await bot.answer_callback_query(call.id, "Произошла ошибка")


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("avatar_card_edit_")
)
async def handle_avatar_card_edit(call):
    """Обработчик кнопки "Редактировать" в карточке аватара."""
    user_id = call.from_user.id
    try:
        avatar_id = call.data.split("_")[-1]
        # Переводим пользователя в режим редактирования имени
        await set_state(user_id, "avatar_enter_name")
        await bot.send_message(
            call.message.chat.id,
            "Введите новое имя для аватара:"
        )
        await bot.answer_callback_query(call.id)
    except Exception as e:
        logger.exception(
            "Error in handle_avatar_card_edit: %s",
            e
        )
        await bot.answer_callback_query(call.id, "Произошла ошибка")


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("avatar_card_delete_")
)
async def handle_avatar_card_delete(call):
    """Обработчик кнопки "Удалить" в карточке аватара."""
    user_id = call.from_user.id
    try:
        avatar_id = call.data.split("_")[-1]
        avatars = await get_avatars_index(user_id)
        if not avatars:
            await bot.answer_callback_query(
                call.id,
                "Нет доступных аватаров"
            )
            return
        
        # Находим текущий индекс перед удалением
        current_idx = 0
        for i, a in enumerate(avatars):
            if a["avatar_id"] == avatar_id:
                current_idx = i
                break
        
        # Удаляем аватар
        await remove_avatar_from_index(user_id, avatar_id)
        
        # Обновляем список и показываем следующий аватар
        avatars = await get_avatars_index(user_id)
        if avatars:
            new_idx = min(current_idx, len(avatars) - 1)
            await send_avatar_card(
                call.message.chat.id,
                user_id,
                avatars,
                new_idx
            )
        else:
            msg = (
                "У вас больше нет аватаров. "
                "Нажмите '📷 Создать аватар', чтобы начать!"
            )
            await bot.send_message(
                call.message.chat.id,
                msg,
                reply_markup=my_avatars_keyboard(),
            )
        try:
            await bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )
        except Exception:
            pass
        await bot.answer_callback_query(call.id, "Аватар удален")
    except Exception as e:
        logger.exception(
            "Error in handle_avatar_card_delete: %s",
            e
        )
        await bot.answer_callback_query(call.id, "Произошла ошибка")


@bot.callback_query_handler(func=lambda call: call.data == "avatar_card_menu")
async def handle_avatar_card_menu(call):
    """Обработчик кнопки "В меню" в карточке аватара."""
    user_id = call.from_user.id
    try:
        await bot.send_message(
            call.message.chat.id,
            "Меню аватаров:",
            reply_markup=my_avatars_keyboard(),
        )
        try:
            await bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )
        except Exception:
            pass
        await bot.answer_callback_query(call.id)
    except Exception as e:
        logger.exception(
            "Error in handle_avatar_card_menu: %s",
            e
        )
        await bot.answer_callback_query(call.id, "Произошла ошибка")


@bot.message_handler(func=lambda m: m.text == "⬅️ Назад" and fsm_states.get(m.from_user.id) == "avatar_enter_name")
async def handle_avatar_name_back(message):
    """Обработчик кнопки "Назад" при вводе имени аватара."""
    user_id = message.from_user.id
    # Возвращаемся к просмотру аватаров
    avatars = await get_avatars_index(user_id)
    if not avatars:
        await bot.send_message(
            message.chat.id,
            "У вас нет аватаров.",
            reply_markup=my_avatars_keyboard()
        )
        return
    # Показываем карточку первого (или основного) аватара
    idx = 0
    for i, a in enumerate(avatars):
        if a.get("is_main"):
            idx = i
            break
    await send_avatar_card(message.chat.id, user_id, avatars, idx)


@bot.message_handler(func=lambda m: fsm_states.get(m.from_user.id) == "avatar_enter_name")
async def handle_avatar_name_input(message):
    """Обработчик ввода имени аватара (как для создания, так и для редактирования)."""
    user_id = message.from_user.id
    try:
        if message.text in ["⬅️ Назад", "Отмена"]:
            # Возвращаемся к просмотру аватаров
            avatars = await get_avatars_index(user_id)
            if not avatars:
                await bot.send_message(
                    message.chat.id,
                    "У вас нет аватаров.",
                    reply_markup=my_avatars_keyboard()
                )
                return
            # Показываем карточку первого (или основного) аватара
            idx = 0
            for i, a in enumerate(avatars):
                if a.get("is_main"):
                    idx = i
                    break
            await send_avatar_card(message.chat.id, user_id, avatars, idx)
            return

        name = message.text.strip()
        if not name:
            await bot.send_message(
                message.chat.id,
                "Имя не может быть пустым. Введите имя для аватара:"
            )
            return

        avatar_id = get_current_avatar_id(user_id)
        if not avatar_id:
            await bot.send_message(
                message.chat.id,
                "Ошибка: не найден аватар."
            )
            return

        # Обновляем имя аватара
        await update_avatar_fsm(user_id, avatar_id, title=name)
        await update_avatar_in_index(user_id, avatar_id, {"title": name})

        # Получаем обновленный список аватаров
        avatars = await get_avatars_index(user_id)
        if not avatars:
            await bot.send_message(
                message.chat.id,
                "Ошибка при обновлении аватара.",
                reply_markup=my_avatars_keyboard()
            )
            return

        # Находим индекс текущего аватара
        current_idx = 0
        for i, a in enumerate(avatars):
            if a["avatar_id"] == avatar_id:
                current_idx = i
                break

        # Показываем обновленную карточку
        await send_avatar_card(
            message.chat.id,
            user_id,
            avatars,
            current_idx
        )
        await bot.send_message(
            message.chat.id,
            "✅ Имя аватара успешно обновлено!"
        )

    except Exception as e:
        logger.exception(
            "Error in handle_avatar_name_input: %s",
            e
        )
        await bot.send_message(
            message.chat.id,
            "Произошла ошибка при обновлении имени аватара."
        )
