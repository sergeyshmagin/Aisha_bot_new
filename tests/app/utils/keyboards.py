"""
Утилиты для создания клавиатур
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_gallery_keyboard(current_index: int, total_count: int, image_id: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для галереи изображений"""
    
    buttons = []
    
    # Навигация
    nav_row = []
    
    if current_index > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Пред.", callback_data=f"gallery_prev:{current_index}"))
    else:
        nav_row.append(InlineKeyboardButton(text="⬅️ Пред.", callback_data="noop"))
    
    nav_row.append(InlineKeyboardButton(text=f"{current_index + 1}/{total_count}", callback_data="noop"))
    
    if current_index < total_count - 1:
        nav_row.append(InlineKeyboardButton(text="След. ➡️", callback_data=f"gallery_next:{current_index}"))
    else:
        nav_row.append(InlineKeyboardButton(text="След. ➡️", callback_data="noop"))
    
    buttons.append(nav_row)
    
    # Действия с изображением
    action_row1 = [
        InlineKeyboardButton(text="📋 Промпт", callback_data=f"gallery_full_prompt:{image_id}"),
        InlineKeyboardButton(text="📄 Скопировать", callback_data=f"gallery_copy_prompt:{image_id}")
    ]
    buttons.append(action_row1)
    
    action_row2 = [
        InlineKeyboardButton(text="🔄 Повторить", callback_data=f"gallery_regenerate:{image_id}"),
        InlineKeyboardButton(text="❤️ Избранное", callback_data=f"gallery_toggle_favorite:{image_id}")
    ]
    buttons.append(action_row2)
    
    action_row3 = [
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"gallery_delete:{image_id}")
    ]
    buttons.append(action_row3)
    
    # Меню и настройки
    menu_row = [
        InlineKeyboardButton(text="📊 Статистика", callback_data="gallery_stats"),
        InlineKeyboardButton(text="🔍 Фильтры", callback_data="gallery_filters")
    ]
    buttons.append(menu_row)
    
    # Назад
    back_row = [
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
    ]
    buttons.append(back_row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 