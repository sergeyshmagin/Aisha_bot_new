"""
Клавиатуры для системы аватаров (чистая версия)
Исправленная версия без синтаксических ошибок
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import AvatarStatusdef get_avatar_main_menu(avatars_count: int = 0) -> InlineKeyboardMarkup:
    """Главное меню системы аватаров (упрощенное с портретной моделью)"""
    
    buttons = [
        [
            InlineKeyboardButton(
                text="🎭 Создать портретный аватар",
                callback_data="create_avatar"
            )
        ]
    ]
    
    if avatars_count > 0:
        buttons.append([
            InlineKeyboardButton(
                text=f"📁 Мои аватары ({avatars_count})",
                callback_data="avatar_gallery"
            )
        ])
    
    buttons.extend([
        [
            InlineKeyboardButton(
                text="ℹ️ Как работают аватары?",
                callback_data="avatar_help"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Главное меню",
                callback_data="back_to_main"
            )
        ]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
