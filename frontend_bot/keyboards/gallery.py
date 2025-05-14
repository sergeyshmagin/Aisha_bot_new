"""Inline-клавиатуры для галереи образов и выбора стиля."""

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from frontend_bot.services.gallery_data import GALLERY_STYLES


def gallery_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🎭 Стили", callback_data="gallery_styles"),
        InlineKeyboardButton("⬅️", callback_data="gallery_prev"),
        InlineKeyboardButton("➡️", callback_data="gallery_next"),
    )
    keyboard.row(
        InlineKeyboardButton("📝 Промпт", callback_data="gallery_prompt"),
        InlineKeyboardButton("✨ Создать фото", callback_data="gallery_create"),
    )
    keyboard.row(
        InlineKeyboardButton("↩️ Вернуться в меню", callback_data="gallery_back")
    )
    return keyboard


def styles_inline_keyboard(selected_style=None):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for style in GALLERY_STYLES:
        text = (
            f"✅ {style['emoji']} {style['name']}"
            if style["name"] == selected_style
            else f"{style['emoji']} {style['name']}"
        )
        keyboard.insert(
            InlineKeyboardButton(text, callback_data=f"style_{style['name']}")
        )
    keyboard.add(InlineKeyboardButton("↩️ Скрыть стили", callback_data="style_hide"))
    return keyboard
