"""Обработчики для галереи образов и выбора стиля."""

from telebot.types import InputMediaPhoto
from frontend_bot.services.gallery_data import GALLERY_IMAGES
from frontend_bot.keyboards.gallery import (
    gallery_inline_keyboard,
    styles_inline_keyboard,
)
from frontend_bot.handlers.general import bot
import aiofiles
import io
from frontend_bot.texts.common import ERROR_NO_PHOTOS, ERROR_INDEX
from frontend_bot.repositories.user_repository import UserRepository
from database.config import AsyncSessionLocal
from frontend_bot.services.state_utils import get_state, set_state


@bot.message_handler(func=lambda m: m.text == "🖼 Образы")
async def show_gallery(message):
    """Обработчик для показа галереи образов по нажатию на кнопку 'Образы'."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await bot.send_message(message.chat.id, ERROR_NO_PHOTOS)
            return
        uuid_user_id = user.id
        # Получаем состояние галереи из БД
        state = await get_state(uuid_user_id, session) or {}
        gallery_state = state.get("gallery", {"idx": 0, "style": None})
        idx = gallery_state["idx"]
        img = GALLERY_IMAGES[idx]
        async with aiofiles.open(img["image_path"], "rb") as photo_file:
            photo_bytes = await photo_file.read()
            await bot.send_photo(
                message.chat.id,
                io.BytesIO(photo_bytes),
                caption=(
                    f"<b>Стиль:</b> {img['style']}\n"
                    f"<b>Образ ({idx+1} из {len(GALLERY_IMAGES)}):</b> "
                    f"{img['name']}"
                ),
                parse_mode="HTML",
                reply_markup=gallery_inline_keyboard(),
            )
        # Сохраняем idx в состоянии
        gallery_state["idx"] = idx
        state["gallery"] = gallery_state
        await set_state(uuid_user_id, state, session)


@bot.callback_query_handler(func=lambda call: call.data.startswith("gallery_"))
async def gallery_callback(call):
    """Обработчик inline-кнопок галереи (переключение, стили, возврат)."""
    telegram_id = call.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await bot.send_message(call.message.chat.id, ERROR_NO_PHOTOS)
            return
        uuid_user_id = user.id
        state = await get_state(uuid_user_id, session) or {}
        gallery_state = state.get("gallery", {"idx": 0, "style": None})
        idx = gallery_state["idx"]
        style = gallery_state["style"]

        if call.data == "gallery_next":
            idx = (idx + 1) % len(GALLERY_IMAGES)
        elif call.data == "gallery_prev":
            idx = (idx - 1) % len(GALLERY_IMAGES)
        elif call.data == "gallery_styles":
            await bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=styles_inline_keyboard(selected_style=style),
            )
            return
        elif call.data == "gallery_back":
            await bot.edit_message_caption(
                call.message.chat.id,
                call.message.message_id,
                caption="Вы вернулись в меню.",
                reply_markup=None,
            )
            return
        # ... обработка других кнопок

        if not (0 <= idx < len(GALLERY_IMAGES)):
            await bot.send_message(call.message.chat.id, ERROR_INDEX)
            return
        img = GALLERY_IMAGES[idx]
        async with aiofiles.open(img["image_path"], "rb") as photo_file:
            photo_bytes = await photo_file.read()
            await bot.edit_message_media(
                media=InputMediaPhoto(
                    io.BytesIO(photo_bytes),
                    caption=(
                        f"<b>Стиль:</b> {img['style']}\n"
                        f"<b>Образ ({idx+1} из {len(GALLERY_IMAGES)}):</b> "
                        f"{img['name']}"
                    ),
                    parse_mode="HTML",
                ),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=gallery_inline_keyboard(),
            )
        # Сохраняем новое состояние
        gallery_state["idx"] = idx
        state["gallery"] = gallery_state
        await set_state(uuid_user_id, state, session)


@bot.callback_query_handler(func=lambda call: call.data.startswith("style_"))
async def style_callback(call):
    """Обработчик выбора стиля в галерее образов."""
    telegram_id = call.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=gallery_inline_keyboard(),
            )
        else:
            uuid_user_id = user.id
            state = await get_state(uuid_user_id, session) or {}
            gallery_state = state.get("gallery", {"idx": 0, "style": None})
            style = call.data.replace("style_", "")
            gallery_state["style"] = style
            state["gallery"] = gallery_state
            await set_state(uuid_user_id, state, session)
            await bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=styles_inline_keyboard(selected_style=style),
            )
            # Можно также фильтровать GALLERY_IMAGES по стилю
