# Модуль галереи для аватаров
# Перенести сюда show_wizard_gallery, get_full_gallery_keyboard,
# handle_gallery_prev, handle_gallery_next, handle_gallery_delete,
# handle_gallery_add, handle_gallery_continue, handle_show_photos
# Импортировать необходимые зависимости и утилиты из avatar_manager,
# state_utils, utils, config и т.д.

import logging
print('AVATAR GALLERY HANDLERS LOADED')
logger = logging.getLogger(__name__)
logger.warning('AVATAR GALLERY HANDLERS LOADED (logger)')
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)
from frontend_bot.config import settings
from frontend_bot.shared.progress import get_progressbar
from frontend_bot.handlers.avatar.state import (
    user_session,
    user_gallery,
    user_last_gallery_msg,
    user_media_group_counter,
)
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
from typing import Optional, List, Dict
from telebot.async_telebot import AsyncTeleBot
from frontend_bot.services.avatar_fsm_service import cleanup_state
from frontend_bot.services.minio_client import generate_presigned_url, download_file
from frontend_bot.handlers.avatar.navigation import show_type_menu, start_avatar_wizard

def get_gallery_key(user_id: int, avatar_id: str) -> str:
    """Получает ключ для галереи."""
    return f"{user_id}:{avatar_id}"

# Клавиатура галереи


def get_full_gallery_keyboard(idx, total, avatar_id, photos, show_cancel=False, is_main=False):
    markup = InlineKeyboardMarkup(row_width=3)
    # Основная навигация
    markup.row(
        InlineKeyboardButton("⬅️ Назад", callback_data=f"avatar_gallery_prev:{avatar_id}"),
        InlineKeyboardButton("❌ Удалить", callback_data=f"avatar_gallery_delete:{avatar_id}"),
        InlineKeyboardButton("Вперёд ▶️", callback_data=f"avatar_gallery_next:{avatar_id}"),
    )
    # Продолжить, если достаточно фото
    if total >= settings.AVATAR_MIN_PHOTOS:
        markup.row(
            InlineKeyboardButton(
                "✅ Продолжить", callback_data=f"avatar_gallery_continue:{avatar_id}"
            )
        )
    # Отмена
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
    # Возвращаем список словарей с id и photo_key
    return [{"id": str(p.id), "photo_key": p.photo_key} for p in photos]


async def show_wizard_gallery(
    bot: AsyncTeleBot,
    chat_id: int,
    user_id: int,
    avatar_id: Optional[str] = None,
    photos: Optional[List[Dict]] = None,
    idx: int = 0,
    message_id: Optional[int] = None,
    session: Optional[AsyncSession] = None
) -> None:
    """
    Показывает галерею фото аватара в визарде (старая логика + новая клавиатура).
    """
    if photos is None:
        photos = await get_avatar_photos_from_db(user_id, avatar_id, session)
    if not photos:
        # Не отправляем сообщение об ошибке, просто return
        return
    # Корректируем индекс
    idx = max(0, min(idx, len(photos) - 1))
    photo = photos[idx]
    # Скачиваем фото из MinIO
    photo_bytes = await download_file("avatars", photo["photo_key"])
    # Старая подпись с прогрессбаром и рекомендациями
    caption = get_gallery_caption(idx, len(photos))
    keyboard = get_full_gallery_keyboard(idx, len(photos), avatar_id, photos)
    await bot.send_photo(
        chat_id,
        photo_bytes,
        caption=caption,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# Остальные функции и обработчики галереи:
# show_wizard_gallery, handle_gallery_prev, handle_gallery_next,
# handle_gallery_delete, handle_gallery_add, handle_gallery_continue,
# handle_show_photos переносить по аналогии...


@bot.callback_query_handler(func=lambda call: call.data.startswith("avatar_gallery_prev"))
@validate_user_avatar
async def handle_gallery_prev(call) -> None:
    telegram_id = getattr(call.from_user, "id", None)
    parts = call.data.split(":")
    avatar_id = parts[1] if len(parts) > 1 else None
    if not avatar_id:
        state = await get_state(telegram_id)
        if isinstance(state, dict):
            avatar_id = state.get('avatar_id')
    print(f"CALLBACK: {call.data}, telegram_id={telegram_id}, avatar_id={avatar_id}")
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        print(f"USER: {user}")
        if not user or not avatar_id:
            await bot.send_message(call.message.chat.id, "Ошибка: не найден пользователь или аватар.")
            await bot.answer_callback_query(call.id)
            return
        uuid_user_id = user.id
        photos = await get_avatar_photos_from_db(uuid_user_id, avatar_id, session)
        print(f"PHOTOS: {photos}")
        if not photos:
            await bot.send_message(call.message.chat.id, "Нет фото для отображения.")
            await bot.answer_callback_query(call.id)
            return
        gallery_key = get_gallery_key(uuid_user_id, avatar_id)
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
        user_gallery[gallery_key]["index"] = idx  # сохраняем новый индекс
        await show_wizard_gallery(
            call.message.chat.id,
            uuid_user_id,
            avatar_id,
            idx=idx,
            message_id=call.message.message_id,
            session=session,
        )
        await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("avatar_gallery_next"))
@validate_user_avatar
async def handle_gallery_next(call) -> None:
    telegram_id = getattr(call.from_user, "id", None)
    parts = call.data.split(":")
    avatar_id = parts[1] if len(parts) > 1 else None
    if not avatar_id:
        state = await get_state(telegram_id)
        if isinstance(state, dict):
            avatar_id = state.get('avatar_id')
    print(f"CALLBACK: {call.data}, telegram_id={telegram_id}, avatar_id={avatar_id}")
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        print(f"USER: {user}")
        if not user or not avatar_id:
            await bot.send_message(call.message.chat.id, "Ошибка: не найден пользователь или аватар.")
            await bot.answer_callback_query(call.id)
            return
        uuid_user_id = user.id
        photos = await get_avatar_photos_from_db(uuid_user_id, avatar_id, session)
        print(f"PHOTOS: {photos}")
        if not photos:
            await bot.send_message(call.message.chat.id, "Нет фото для отображения.")
            await bot.answer_callback_query(call.id)
            return
        gallery_key = get_gallery_key(uuid_user_id, avatar_id)
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
        user_gallery[gallery_key]["index"] = idx
        await show_wizard_gallery(
            call.message.chat.id,
            uuid_user_id,
            avatar_id,
            idx=idx,
            message_id=call.message.message_id,
            session=session,
        )
        await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("avatar_gallery_delete"))
@validate_user_avatar
async def handle_gallery_delete(call) -> None:
    telegram_id = getattr(call.from_user, "id", None)
    parts = call.data.split(":")
    photo_id = parts[1] if len(parts) > 1 else None
    avatar_id = None
    if not photo_id:
        state = await get_state(telegram_id)
        if isinstance(state, dict):
            avatar_id = state.get('avatar_id')
    logger.warning(f"[DEBUG] handle_gallery_delete: callback_data={call.data}, telegram_id={telegram_id}, photo_id={photo_id}")
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        logger.warning(f"[DEBUG] handle_gallery_delete: user={user}")
        if not user or (not photo_id and not avatar_id):
            await bot.send_message(call.message.chat.id, "Ошибка: не найден пользователь или фото.")
            await bot.answer_callback_query(call.id)
            return
        uuid_user_id = user.id
        # Получаем avatar_id по photo_id
        query = select(UserAvatarPhoto).where(UserAvatarPhoto.id == photo_id)
        result = await session.execute(query)
        photo_obj = result.scalar_one_or_none()
        logger.warning(f"[DEBUG] handle_gallery_delete: photo_obj={photo_obj}")
        if not photo_obj:
            await bot.send_message(call.message.chat.id, "Ошибка: фото не найдено.")
            await bot.answer_callback_query(call.id)
            return
        avatar_id = str(photo_obj.avatar_id)
        logger.warning(f"[DEBUG] handle_gallery_delete: удаляем фото, uuid_user_id={uuid_user_id}, avatar_id={avatar_id}, photo_id={photo_id}")
        # Удаляем фото из БД и MinIO
        success = await remove_photo_from_avatar(session, uuid_user_id, avatar_id, str(photo_obj.id))
        logger.warning(f"[DEBUG] handle_gallery_delete: результат удаления success={success}")
        # Получаем обновлённый список фото
        photos = await get_avatar_photos_from_db(uuid_user_id, avatar_id, session)
        logger.warning(f"[DEBUG] handle_gallery_delete: осталось фото {len(photos)}")
        gallery_key = get_gallery_key(uuid_user_id, avatar_id)
        idx = user_gallery.get(gallery_key, {}).get("index", 0)
        if not photos:
            try:
                await bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            await bot.send_message(call.message.chat.id, "Нет фото для отображения. Пожалуйста, загрузите хотя бы одно фото.")
            await bot.answer_callback_query(call.id)
            return
        idx = min(idx, len(photos) - 1)
        keyboard = get_full_gallery_keyboard(idx, len(photos), avatar_id, photos)
        # Показываем следующее фото
        await show_wizard_gallery(call.message.chat.id, uuid_user_id, avatar_id, photos, idx, session)
        await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("avatar_gallery_continue"))
async def handle_gallery_continue(call):
    telegram_id = call.from_user.id
    parts = call.data.split(":")
    avatar_id = parts[1] if len(parts) > 1 else None
    if not avatar_id:
        state = await get_state(telegram_id)
        if isinstance(state, dict):
            avatar_id = state.get('avatar_id')
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user or not avatar_id:
            await bot.send_message(call.message.chat.id, "Ошибка: не найден пользователь или аватар.")
            await bot.answer_callback_query(call.id)
            return
        uuid_user_id = user.id
        photos = await get_avatar_photos_from_db(uuid_user_id, avatar_id, session)
        if len(photos) < settings.AVATAR_MIN_PHOTOS:
            await bot.send_message(call.message.chat.id, f"Недостаточно фото для генерации аватара. Нужно минимум {settings.AVATAR_MIN_PHOTOS}.")
            await bot.answer_callback_query(call.id)
            return
        # Переводим state на следующий этап
        await set_state(uuid_user_id, "avatar_type_select", session)
        # Переходим к выбору типа аватара, передаём avatar_id
        await show_type_menu(call.message.chat.id, uuid_user_id, avatar_id=avatar_id, session=session)
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
            await show_wizard_gallery(call.message.chat.id, user_id, avatar_id, idx=0, session=session)
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "avatar_gallery_add")
async def handle_gallery_add(call):
    # Не отправляем отдельное сообщение, просто уведомляем пользователя
    await bot.answer_callback_query(call.id, "Ждём новое фото...")


@bot.callback_query_handler(func=lambda call: call.data == "avatar_cancel")
async def handle_avatar_cancel(call):
    telegram_id = getattr(call.from_user, "id", None)
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            logger.error(f"[handle_avatar_cancel] Не найден пользователь с telegram_id={telegram_id}")
            await bot.send_message(call.message.chat.id, "Ошибка: не удалось определить пользователя.")
            await bot.answer_callback_query(call.id)
            return
        uuid_user_id = user.id
        avatar_id = user_session.get(uuid_user_id, {}).get("avatar_id")
        await cleanup_state(uuid_user_id, avatar_id, session)
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
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await bot.send_message(message.chat.id, "Ошибка: пользователь не найден.")
            return
        await start_avatar_wizard(bot, message.chat.id, user.id, session)


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
    Показывает галерею фото для просмотра аватаров.
    """
    user_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(user_id)
        if not user:
            await bot.send_message(message.chat.id, "Ошибка: пользователь не найден.")
            return
            
        uuid_user_id = user.id
        avatar_id = get_current_avatar_id(user_id)
        if not avatar_id:
            await bot.send_message(
                message.chat.id,
                "У вас пока нет аватаров. Нажмите '📷 Создать аватар', чтобы начать!",
                reply_markup=my_avatars_keyboard(),
            )
            return
            
        photos = await get_avatar_photos_from_db(uuid_user_id, avatar_id, session)
        if not photos:
            await bot.send_message(
                message.chat.id,
                "У вас пока нет загруженных фото.",
                reply_markup=my_avatars_keyboard(),
            )
            return
            
        await show_wizard_gallery(
            bot,
            message.chat.id,
            uuid_user_id,
            avatar_id=avatar_id,
            photos=photos,
            idx=0,
            session=session
        )


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
