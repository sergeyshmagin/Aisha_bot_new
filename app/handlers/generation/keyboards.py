"""
Клавиатуры для системы генерации изображений
"""
from typing import List
from uuid import UUID

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.database.models.generation import StyleCategory, StyleTemplate


def build_generation_menu_keyboard(
    popular_categories: List[StyleCategory],
    favorites: List[StyleTemplate],
    avatar_id: UUID,
    user_balance: float,
    generation_cost: float
) -> InlineKeyboardMarkup:
    """Строит клавиатуру главного меню генерации"""
    
    buttons = []
    
    # Проверяем, достаточно ли баланса
    has_balance = user_balance >= generation_cost
    
    if has_balance:
        # Два варианта создания промпта в одной строке
        buttons.append([
            InlineKeyboardButton(
                text="📝 Свой промпт",
                callback_data=f"gen_custom:{avatar_id}"
            ),
            InlineKeyboardButton(
                text="📸 Промпт по фото",
                callback_data=f"gen_photo:{avatar_id}"
            )
        ])
    else:
        # Недостаточно баланса
        buttons.append([
            InlineKeyboardButton(
                text="💰 Пополнить баланс",
                callback_data="balance_topup"
            )
        ])
    
    # Сменить аватар
    buttons.append([
        InlineKeyboardButton(
            text="🔄 Сменить аватар",
            callback_data="gen_change_avatar"
        )
    ])
    
    # Моя галерея
    buttons.append([
        InlineKeyboardButton(
            text="🖼️ Моя галерея",
            callback_data="my_gallery"
        )
    ])
    
    # Назад
    buttons.append([
        InlineKeyboardButton(
            text="🔙 Главное меню",
            callback_data="main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_aspect_ratio_keyboard() -> InlineKeyboardMarkup:
    """Строит клавиатуру выбора соотношения сторон"""
    
    buttons = [
        [
            InlineKeyboardButton(
                text="📱 Портрет (9:16)",
                callback_data="aspect_ratio:9:16"
            ),
            InlineKeyboardButton(
                text="🖼️ Квадрат (1:1)",
                callback_data="aspect_ratio:1:1"
            )
        ],
        [
            InlineKeyboardButton(
                text="🖥️ Альбом (16:9)",
                callback_data="aspect_ratio:16:9"
            ),
            InlineKeyboardButton(
                text="📄 A4 (3:4)",
                callback_data="aspect_ratio:3:4"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="generation_menu"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_generation_result_keyboard(
    generation_id: UUID,
    show_full_prompt: bool = True
) -> InlineKeyboardMarkup:
    """Строит клавиатуру для результата генерации"""
    
    buttons = []
    
    # Основные действия
    buttons.append([
        InlineKeyboardButton(
            text="🔄 Генерировать еще",
            callback_data="generation_menu"
        ),
        InlineKeyboardButton(
            text="🖼️ В галерею",
            callback_data="my_gallery"
        )
    ])
    
    # Показать полный промпт
    if show_full_prompt:
        buttons.append([
            InlineKeyboardButton(
                text="📝 Показать промпт",
                callback_data=f"show_prompt:{generation_id}"
            )
        ])
    
    # Назад в главное меню
    buttons.append([
        InlineKeyboardButton(
            text="🔙 Главное меню",
            callback_data="main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_photo_prompt_keyboard() -> InlineKeyboardMarkup:
    """Строит клавиатуру для промпта по фото"""
    
    buttons = [
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="generation_menu"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_custom_prompt_keyboard() -> InlineKeyboardMarkup:
    """Строит клавиатуру для кастомного промпта"""
    
    buttons = [
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="generation_menu"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 