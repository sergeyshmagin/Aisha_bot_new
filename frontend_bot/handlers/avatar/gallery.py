# Модуль галереи для аватаров
# Перенести сюда show_wizard_gallery, get_full_gallery_keyboard, handle_gallery_prev, handle_gallery_next, handle_gallery_delete, handle_gallery_add, handle_gallery_continue, handle_show_photos
# Импортировать необходимые зависимости и утилиты из avatar_manager, state_manager, utils, config и т.д.

import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from frontend_bot.bot import bot
from frontend_bot.services.avatar_manager import load_avatar_fsm, remove_photo_from_avatar
from frontend_bot.services.state_manager import get_current_avatar_id, set_state
from frontend_bot.handlers.avatar.utils import get_progressbar
from frontend_bot.config import AVATAR_MIN_PHOTOS, AVATAR_MAX_PHOTOS
from frontend_bot.handlers.avatar.state import user_session, user_gallery

logger = logging.getLogger(__name__)

# Клавиатура галереи

def get_full_gallery_keyboard(idx, total):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("◀️ Назад", callback_data="avatar_gallery_prev"),
        InlineKeyboardButton("❌ Удалить", callback_data="avatar_gallery_delete"),
        InlineKeyboardButton("Вперёд ▶️", callback_data="avatar_gallery_next")
    )
    if total >= AVATAR_MIN_PHOTOS:
        markup.row(InlineKeyboardButton("✅ Продолжить", callback_data="avatar_gallery_continue"))
    markup.row(InlineKeyboardButton("↩️ Отмена", callback_data="avatar_cancel"))
    return markup

# Остальные функции и обработчики галереи (show_wizard_gallery, handle_gallery_prev, handle_gallery_next, handle_gallery_delete, handle_gallery_add, handle_gallery_continue, handle_show_photos) переносить по аналогии... 