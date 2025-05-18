# Модуль галереи для аватаров
# Перенести сюда show_wizard_gallery, get_full_gallery_keyboard,
# handle_gallery_prev, handle_gallery_next, handle_gallery_delete,
# handle_gallery_add, handle_gallery_continue, handle_show_photos
# Импортировать необходимые зависимости и утилиты из avatar_manager,
# state_utils, utils, config и т.д.

import logging
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)
from frontend_bot.config import settings
from frontend_bot.shared.progress import get_progressbar
from frontend_bot.handlers.avatar.state import user_session, user_gallery
from frontend_bot.bot_instance import bot
import time
from frontend_bot.texts.common import (
    ERROR_NO_PHOTOS,
    ERROR_USER_AVATAR,
    ERROR_INDEX,
    get_gallery_caption,
    PROMPT_AVATAR_CANCELLED,
)
from frontend_bot.services.avatar_manager import (
    remove_photo_from_avatar,
    get_avatars_index,
    get_current_avatar_id,
    set_current_avatar_id,
    get_avatar_photo,
)
from frontend_bot.services.state_utils import set_state, get_state, clear_state
from frontend_bot.utils.validators import validate_user_avatar
from frontend_bot.keyboards.common import get_gallery_keyboard
from frontend_bot.handlers.avatar.fsm import show_type_menu, start_avatar_wizard
from frontend_bot.shared.utils import clear_old_wizard_messages
from frontend_bot.keyboards.reply import (
    ai_photographer_keyboard,
    my_avatars_keyboard,
)
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from frontend_bot.services.avatar_workflow import delete_draft_avatar, set_main_avatar, get_avatar, delete_avatar, list_avatars
from database.config import AsyncSessionLocal
from frontend_bot.repositories.user_repository import UserRepository
from database.models import UserAvatarPhoto
from sqlalchemy import select
from io import BytesIO

logger = logging.getLogger(__name__)

def get_gallery_key(user_id: int, avatar_id: str) -> str:
    """Получает ключ для галереи."""
    return f"{user_id}:{avatar_id}"

# Клавиатура галереи


def get_full_gallery_keyboard(idx, total):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("◀️ Назад", callback_data="avatar_gallery_prev"),
        InlineKeyboardButton("❌ Удалить", callback_data="avatar_gallery_delete"),
    )
    markup.row(InlineKeyboardButton("Вперёд ▶️", callback_data="avatar_gallery_next"))
    if total >= settings.AVATAR_MIN_PHOTOS:
        markup.row(
            InlineKeyboardButton(
                "✅ Продолжить", callback_data="avatar_gallery_continue"
            )
        )
    markup.row(InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel"))
    return markup


async def get_avatar_photos_from_db(user_id, avatar_id, db: AsyncSession):
    """Возвращает список фото для аватара из PostgreSQL."""
    query = select(UserAvatarPhoto).where(
        UserAvatarPhoto.user_id == user_id,
        UserAvatarPhoto.avatar_id == avatar_id
    ).order_by(UserAvatarPhoto.created_at)
    result = await db.execute(query)
    photos = result.scalars().all()
    logger.info(f"[gallery] get_avatar_photos_from_db: {len(photos)} фото найдено для avatar_id={avatar_id}")
    return [p.photo_key for p in photos]


async def show_wizard_gallery(
    chat_id: int,
    user_id: int,
    avatar_id: str,
    photos: list = None,
    idx: int = 0,
    message_id: int = None,
    db: AsyncSession = None,
) -> None:
    """
    Показывает галерею фото аватара.
    """
    if db is None:
        logger.error("[show_wizard_gallery] db (AsyncSession) обязателен!")
        return
    # Получаем фото из БД
    photos = await get_avatar_photos_from_db(user_id, avatar_id, db)
    if not photos:
        await bot.send_message(chat_id, ERROR_NO_PHOTOS)
        return
    idx = max(0, min(idx, len(photos) - 1))
    photo_key = photos[idx]
    total = len(photos)
    caption = get_gallery_caption(idx, total)
    keyboard = get_gallery_keyboard(idx, total)
    
    try:
        # Получаем фото из MinIO
        photo_bytes = await get_avatar_photo(photo_key)
        img_stream = BytesIO(photo_bytes)
        
        if message_id:
            await bot.edit_message_media(
                media=InputMediaPhoto(
                    img_stream, caption=caption, parse_mode="HTML"
                ),
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=keyboard,
            )
        else:
            msg = await bot.send_photo(
                chat_id,
                img_stream,
                caption=caption,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        logger.info(f"[show_wizard_gallery] показано фото {idx+1}/{total} для avatar_id={avatar_id}")
    except Exception as e:
        logger.error(f"[show_wizard_gallery] Ошибка при получении фото из MinIO: {e}")
        await bot.send_message(chat_id, ERROR_NO_PHOTOS)


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
    async with AsyncSessionLocal() as session:
        photos = await get_avatar_photos_from_db(user_id, avatar_id, session)
    if not photos:
        await bot.send_message(call.message.chat.id, "Нет фото для отображения.")
        await bot.answer_callback_query(call.id)
        return
    gallery_key = get_gallery_key(user_id, avatar_id)
    idx = user_gallery.get(gallery_key, {}).get("index", 0)
    if not (0 <= idx < len(photos)):
        await bot.send_message(call.message.chat.id, ERROR_INDEX)
        await bot.answer_callback_query(call.id)
        return
    now = time.monotonic()
    last = user_gallery[gallery_key]["last_switch"]
    if now - last < 0.7:
        await bot.answer_callback_query(call.id, "Слишком быстро!")
        return
    user_gallery[gallery_key]["last_switch"] = now
    if idx <= 0:
        idx = len(photos) - 1
    else:
        idx -= 1
    async with AsyncSessionLocal() as session:
        await show_wizard_gallery(
            call.message.chat.id,
            user_id,
            avatar_id,
            idx=idx,
            message_id=call.message.message_id,
            db=session,
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
    async with AsyncSessionLocal() as session:
        photos = await get_avatar_photos_from_db(user_id, avatar_id, session)
    if not photos:
        await bot.send_message(call.message.chat.id, "Нет фото для отображения.")
        await bot.answer_callback_query(call.id)
        return
    gallery_key = get_gallery_key(user_id, avatar_id)
    idx = user_gallery.get(gallery_key, {}).get("index", 0)
    if not (0 <= idx < len(photos)):
        await bot.send_message(call.message.chat.id, ERROR_INDEX)
        await bot.answer_callback_query(call.id)
        return
    now = time.monotonic()
    last = user_gallery[gallery_key]["last_switch"]
    if now - last < 0.7:
        await bot.answer_callback_query(call.id, "Слишком быстро!")
        return
    user_gallery[gallery_key]["last_switch"] = now
    if idx >= len(photos) - 1:
        idx = 0
    else:
        idx += 1
    async with AsyncSessionLocal() as session:
        await show_wizard_gallery(
            call.message.chat.id,
            user_id,
            avatar_id,
            idx=idx,
            message_id=call.message.message_id,
            db=session,
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
    async with AsyncSessionLocal() as session:
        photos = await get_avatar_photos_from_db(user_id, avatar_id, session)
        gallery_key = get_gallery_key(user_id, avatar_id)
        idx = user_gallery.get(gallery_key, {}).get("index", 0)
        logger.info(f"[handle_gallery_delete] idx={idx}, photos={photos}")
        if not photos or not (0 <= idx < len(photos)):
            await bot.send_message(call.message.chat.id, ERROR_INDEX)
            await bot.answer_callback_query(call.id)
            return
        # Удаляем фото из БД и MinIO
        await remove_photo_from_avatar(session, user_id, avatar_id, photos[idx])
        logger.info(f"[handle_gallery_delete] photo removed at idx={idx}")
        # Получаем обновлённый список фото
        photos = await get_avatar_photos_from_db(user_id, avatar_id, session)
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
        user_gallery[gallery_key]["index"] = new_idx
        logger.info(f"[handle_gallery_delete] show_wizard_gallery new_idx={new_idx}")
        await show_wizard_gallery(
            call.message.chat.id,
            user_id,
            avatar_id,
            idx=new_idx,
            message_id=call.message.message_id,
            db=session,
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
    async with AsyncSessionLocal() as session:
        photos = await get_avatar_photos_from_db(user_id, avatar_id, session)
        if not photos:
            await bot.send_message(call.message.chat.id, "У вас пока нет загруженных фото.")
        else:
            await show_wizard_gallery(call.message.chat.id, user_id, avatar_id, idx=0, db=session)
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
    reset_avatar_fsm(user_id, session)
    await bot.send_message(
        call.message.chat.id, PROMPT_AVATAR_CANCELLED, parse_mode="HTML"
    )
    await bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda m: m.text == "🧑‍🎨 ИИ фотограф")
async def ai_photographer_menu(message):
    await set_state(message.from_user.id, "ai_photographer", session)
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
    async with AsyncSessionLocal() as session:
        await start_avatar_wizard(message, session)


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
    date_str = dt.strftime("%d.%m.%Y") if dt else "-"
    status_str = "⏳ Обучается" if status == "pending" else status
    main_str = "⭐ Основной" if is_main else ""
    # Корректно отображаем пол на русском
    gender = avatar.get("gender")
    if gender in ("male", "man"):
        gender_str = "Мужчина"
    elif gender in ("female", "woman"):
        gender_str = "Женщина"
    elif gender:
        gender_str = str(gender)
    else:
        gender_str = "-"
    text = (
        f"<b>{title}</b>\n"
        f"🗓 {date_str}\n"
        f"🚻 Пол: {gender_str}\n"
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
async def view_avatars_handler(message, db: AsyncSession = None):
    """
    Миграция: листинг аватаров через MinIO/PostgreSQL (list_user_avatars_minio).
    Если db не передан — fallback на legacy get_avatars_index.
    """
    user_id = message.from_user.id
    if db is not None:
        avatars = await list_avatars(
            user_id=user_id,
            session=db
        )
        # Приводим к формату legacy для send_avatar_card
        avatars = [
            {
                "avatar_id": a["avatar_id"],
                "title": a.get("name", "Без имени"),
                "created_at": a.get("created_at", "-"),
                "status": a["metadata"].get("status", "-") if a.get("metadata") else "-",
                "is_main": a["metadata"].get("is_main", False) if a.get("metadata") else False,
                "preview_path": a["metadata"].get("preview_path") if a.get("metadata") else None,
                "gender": a["metadata"].get("gender") if a.get("metadata") else None,
            }
            for a in avatars
        ]
    else:
        async with AsyncSessionLocal() as session:
            avatars = await get_avatars_index(user_id, session)
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
        async with AsyncSessionLocal() as session:
            avatars = await get_avatars_index(user_id, session)
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
        async with AsyncSessionLocal() as session:
            avatars = await get_avatars_index(user_id, session)
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
async def handle_avatar_card_main(call, db: AsyncSession = None):
    """Обработчик кнопки "Сделать основным" в карточке аватара."""
    user_id = call.from_user.id
    try:
        avatar_id = call.data.split("_")[-1]
        session = db
        if session is None:
            from frontend_bot.database import get_async_session
            async with get_async_session() as session:
                await set_main_avatar(user_id, avatar_id, session)
        else:
            await set_main_avatar(user_id, avatar_id, session)
        async with AsyncSessionLocal() as session:
            avatars = await get_avatars_index(user_id, session)
        if not avatars:
            await bot.answer_callback_query(
                call.id,
                "Нет доступных аватаров"
            )
            return
        current_idx = 0
        for i, a in enumerate(avatars):
            if a["avatar_id"] == avatar_id:
                current_idx = i
                break
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
    avatar_id = call.data.split("_")[-1]
    from frontend_bot.services.avatar_manager import set_current_avatar_id
    set_current_avatar_id(user_id, avatar_id)
    from frontend_bot.handlers.avatar.state import user_session
    user_session.setdefault(user_id, {})
    user_session[user_id]["edit_mode"] = "edit"
    await set_state(user_id, "avatar_enter_name", session)
    await bot.send_message(
        call.message.chat.id,
        "Введите новое имя для аватара:"
    )
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("avatar_card_delete_")
)
async def handle_avatar_card_delete(call, db: AsyncSession = None):
    """
    Миграция: удаление аватара через MinIO/PostgreSQL (delete_avatar_minio).
    Если db не передан — fallback на legacy delete_draft_avatar.
    """
    user_id = call.from_user.id
    try:
        avatar_id = call.data.split("_")[-1]
        async with AsyncSessionLocal() as session:
            avatars = await get_avatars_index(user_id, session)
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
        # Удаляем аватар полностью (и файлы, и запись)
        if db is not None:
            await delete_avatar(
                user_id=user_id,
                avatar_id=avatar_id,
                session=db
            )
        else:
            from frontend_bot.database import get_async_session
            async with get_async_session() as session:
                await delete_draft_avatar(user_id, session)
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
