"""Обработчики для галереи образов и выбора стиля."""

from telebot.types import InputMediaPhoto
from frontend_bot.services.gallery_data import GALLERY_IMAGES
from frontend_bot.services.gallery_state import user_gallery_state
from frontend_bot.keyboards.gallery import gallery_inline_keyboard, styles_inline_keyboard
from frontend_bot.handlers.general import bot

@bot.message_handler(func=lambda m: m.text == "🖼 Образы")
async def show_gallery(message):
    """Обработчик для показа галереи образов по нажатию на кнопку 'Образы'."""
    user_id = message.from_user.id
    user_gallery_state[user_id] = {"style": None, "idx": 0}
    img = GALLERY_IMAGES[0]
    with open(img["image_path"], "rb") as photo:
        await bot.send_photo(
            message.chat.id,
            photo,
            caption=f"<b>Стиль:</b> {img['style']}\n<b>Образ (1 из {len(GALLERY_IMAGES)}):</b> {img['name']}",
            parse_mode="HTML",
            reply_markup=gallery_inline_keyboard()
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("gallery_"))
async def gallery_callback(call):
    """Обработчик inline-кнопок галереи (переключение, стили, возврат)."""
    user_id = call.from_user.id
    state = user_gallery_state.get(user_id, {"style": None, "idx": 0})
    idx = state["idx"]
    style = state["style"]

    if call.data == "gallery_next":
        idx = (idx + 1) % len(GALLERY_IMAGES)
    elif call.data == "gallery_prev":
        idx = (idx - 1) % len(GALLERY_IMAGES)
    elif call.data == "gallery_styles":
        await bot.edit_message_reply_markup(
            call.message.chat.id, call.message.message_id,
            reply_markup=styles_inline_keyboard(selected_style=style)
        )
        return
    elif call.data == "gallery_back":
        await bot.edit_message_caption(
            call.message.chat.id, call.message.message_id,
            caption="Вы вернулись в меню.",
            reply_markup=None
        )
        return
    # ... обработка других кнопок

    user_gallery_state[user_id]["idx"] = idx
    img = GALLERY_IMAGES[idx]
    with open(img["image_path"], "rb") as photo:
        await bot.edit_message_media(
            media=InputMediaPhoto(photo, caption=f"<b>Стиль:</b> {img['style']}\n<b>Образ ({idx+1} из {len(GALLERY_IMAGES)}):</b> {img['name']}", parse_mode="HTML"),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=gallery_inline_keyboard()
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("style_"))
async def style_callback(call):
    """Обработчик выбора стиля в галерее образов."""
    user_id = call.from_user.id
    style_name = call.data.replace("style_", "")
    if style_name == "hide":
        await bot.edit_message_reply_markup(
            call.message.chat.id, call.message.message_id,
            reply_markup=gallery_inline_keyboard()
        )
    else:
        user_gallery_state[user_id]["style"] = style_name
        await bot.edit_message_reply_markup(
            call.message.chat.id, call.message.message_id,
            reply_markup=styles_inline_keyboard(selected_style=style_name)
        )
        # Можно также фильтровать GALLERY_IMAGES по стилю 