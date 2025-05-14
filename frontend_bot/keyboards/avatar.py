from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def avatar_confirm_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Создать аватар", callback_data="avatar_confirm_yes"),
        InlineKeyboardButton("✏️ Изменить", callback_data="avatar_confirm_edit"),
    )
    markup.add(InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel"))
    return markup


def avatar_gallery_keyboard(
    current: int, total: int, avatar_id: str, is_main: bool
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=3)
    kb.row(
        InlineKeyboardButton("⬅️", callback_data="avatar_prev"),
        InlineKeyboardButton(f"{current} из {total}", callback_data="avatar_page"),
        InlineKeyboardButton("➡️", callback_data="avatar_next"),
    )
    kb.row(
        InlineKeyboardButton("⭐", callback_data=f"avatar_main_{avatar_id}"),
        InlineKeyboardButton("✏️", callback_data=f"avatar_rename_{avatar_id}"),
        InlineKeyboardButton("🗑", callback_data=f"avatar_delete_{avatar_id}"),
    )
    kb.add(InlineKeyboardButton("↩️ В меню", callback_data="avatar_back"))
    return kb
