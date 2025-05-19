from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from frontend_bot.config import settings

# Клавиатура отмены
cancel_keyboard = InlineKeyboardMarkup()
cancel_keyboard.add(InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel"))

# Клавиатура подтверждения (если используется не только для аватаров)
confirm_keyboard = InlineKeyboardMarkup()
confirm_keyboard.add(
    InlineKeyboardButton("✅ Создать аватар", callback_data="avatar_confirm_yes"),
    InlineKeyboardButton("✏️ Изменить", callback_data="avatar_confirm_edit"),
)
confirm_keyboard.add(InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel"))

# Оставляю только универсальные клавиатуры. Все аватарные — теперь в avatar.py
