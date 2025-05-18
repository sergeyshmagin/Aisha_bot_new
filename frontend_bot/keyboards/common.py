from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from frontend_bot.config import settings

# Клавиатура отмены
cancel_keyboard = InlineKeyboardMarkup()
cancel_keyboard.add(InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel"))

# Клавиатура подтверждения
confirm_keyboard = InlineKeyboardMarkup()
confirm_keyboard.add(
    InlineKeyboardButton("✅ Создать аватар", callback_data="avatar_confirm_yes"),
    InlineKeyboardButton("✏️ Изменить", callback_data="avatar_confirm_edit"),
)
confirm_keyboard.add(InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel"))

# Клавиатура выбора типа
avatar_type_keyboard = InlineKeyboardMarkup()
avatar_type_keyboard.add(
    InlineKeyboardButton("👨 Мужчина", callback_data="avatar_type_man"),
    InlineKeyboardButton("👩 Женщина", callback_data="avatar_type_woman"),
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

# Универсальная клавиатура галереи


def get_gallery_keyboard(idx: int, total: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("⬅️ Назад", callback_data="avatar_gallery_prev"),
        InlineKeyboardButton("❌ Удалить", callback_data="avatar_gallery_delete"),
        InlineKeyboardButton("Вперёд ▶️", callback_data="avatar_gallery_next"),
    )
    if total >= settings.AVATAR_MIN_PHOTOS:
        markup.row(
            InlineKeyboardButton(
                "✅ Продолжить", callback_data="avatar_gallery_continue"
            )
        )
    markup.row(InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel"))
    return markup
