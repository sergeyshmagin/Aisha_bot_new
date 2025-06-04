"""
Клавиатуры для системы галереи изображений
"""
from typing import List
from uuid import UUID

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def build_gallery_image_keyboard(
    img_idx: int, 
    total_images: int, 
    generation_id: str,
    is_favorite: bool = False
) -> InlineKeyboardMarkup:
    """Строит клавиатуру для карточки изображения в галерее (как в оригинальном коде)"""
    
    buttons = []
    
    # 🔝 БЛОК 1: Фильтры и навигация по галерее (наверху)
    top_row = [
        InlineKeyboardButton(text="🔍 Фильтры", callback_data="gallery_filters"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="gallery_stats")
    ]
    buttons.append(top_row)
    
    # 🔄 БЛОК 2: Навигация по изображениям
    nav_row = []
    
    if img_idx > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"gallery_image_prev:{img_idx}"))
    else:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data="noop"))
    
    nav_row.append(InlineKeyboardButton(text=f"{img_idx + 1}/{total_images}", callback_data="noop"))
    
    if img_idx < total_images - 1:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data=f"gallery_image_next:{img_idx}"))
    else:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data="noop"))
    
    buttons.append(nav_row)
    
    # 📋 БЛОК 3: Действия с промптом и контентом
    content_row = [
        InlineKeyboardButton(text="📋 Промпт", callback_data=f"gallery_full_prompt:{generation_id}"),
        InlineKeyboardButton(text="🔄 Повторить", callback_data=f"gallery_regenerate:{generation_id}")
    ]
    buttons.append(content_row)
    
    # ❤️ БЛОК 4: Взаимодействие и управление
    interaction_row = [
        InlineKeyboardButton(text="❤️ Избранное", callback_data=f"gallery_toggle_favorite:{generation_id}"),
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"gallery_delete:{generation_id}")
    ]
    buttons.append(interaction_row)
    
    # 🏠 БЛОК 5: Навигация по приложению
    back_row = [
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
    ]
    buttons.append(back_row)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_gallery_stats_keyboard() -> InlineKeyboardMarkup:
    """Строит клавиатуру для статистики галереи"""
    
    buttons = [
        [
            InlineKeyboardButton(
                text="🔙 К галерее",
                callback_data="my_gallery"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_delete_confirmation_keyboard(generation_id: str) -> InlineKeyboardMarkup:
    """Строит клавиатуру подтверждения удаления"""
    
    buttons = [
        [
            InlineKeyboardButton(
                text="❌ Да, удалить",
                callback_data=f"gallery_delete_confirm:{generation_id}"
            ),
            InlineKeyboardButton(
                text="🔙 Отмена",
                callback_data="my_gallery"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_empty_gallery_keyboard() -> InlineKeyboardMarkup:
    """Строит клавиатуру для пустой галереи"""
    
    buttons = [
        [
            InlineKeyboardButton(
                text="🎨 Создать первое изображение",
                callback_data="generation_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_search_keyboard() -> InlineKeyboardMarkup:
    """Строит клавиатуру для поиска в галерее"""
    
    buttons = [
        [
            InlineKeyboardButton(
                text="📅 По дате",
                callback_data="gallery_filter_date"
            ),
            InlineKeyboardButton(
                text="🎭 По аватару",
                callback_data="gallery_filter_avatar"
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 По промпту",
                callback_data="gallery_filter_prompt"
            ),
            InlineKeyboardButton(
                text="💛 Избранные",
                callback_data="gallery_filter_favorites"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 К галерее",
                callback_data="my_gallery"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 