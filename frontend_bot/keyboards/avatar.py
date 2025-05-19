"""
Клавиатуры для работы с аватарами:
- avatar_confirm_keyboard
- avatar_gallery_keyboard
- avatar_type_keyboard
- photo_stage_keyboard
- continue_keyboard
- only_continue_keyboard
"""
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from frontend_bot.config import settings


def avatar_confirm_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Создать аватар", callback_data="avatar_confirm_yes"),
        InlineKeyboardButton("✏️ Изменить", callback_data="avatar_confirm_edit"),
    )
    markup.add(InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel"))
    return markup


# Клавиатура выбора типа аватара
avatar_type_keyboard = InlineKeyboardMarkup()
avatar_type_keyboard.add(
    InlineKeyboardButton("👨 Мужчина", callback_data="avatar_type_man"),
    InlineKeyboardButton("👩 Женщина", callback_data="avatar_type_woman"),
)

# Клавиатура этапа загрузки фото
photo_stage_keyboard = InlineKeyboardMarkup()
photo_stage_keyboard.add(
    InlineKeyboardButton("📷 Мои фото", callback_data="avatar_show_photos"),
    InlineKeyboardButton("ℹ️ Требования", callback_data="avatar_show_requirements"),
    InlineKeyboardButton("👀 Пример фото", callback_data="avatar_show_example"),
)
photo_stage_keyboard.add(
    InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel")
)

# Клавиатура после 16 фото
continue_keyboard = InlineKeyboardMarkup()
continue_keyboard.add(InlineKeyboardButton("Продолжить", callback_data="avatar_next"))
continue_keyboard.add(InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel"))

# Клавиатура только для продолжения
only_continue_keyboard = InlineKeyboardMarkup()
only_continue_keyboard.add(
    InlineKeyboardButton("Продолжить", callback_data="avatar_next")
)
only_continue_keyboard.add(
    InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel")
)
