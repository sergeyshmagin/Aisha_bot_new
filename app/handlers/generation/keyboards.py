"""
Клавиатуры для системы генерации изображений
"""
from typing import List
from uuid import UUID

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.database.models import StyleCategory, StyleTemplate, UserSettings


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
                text="📝 Свой запрос",
                callback_data="avatar_custom_prompt"
            ),
            InlineKeyboardButton(
                text="📸 По образцу",
                callback_data="avatar_from_photo"
            )
        ])
        
        # Добавляем кнопку стилей как заглушку
        buttons.append([
            InlineKeyboardButton(
                text="🎨 Выбрать стиль",
                callback_data="avatar_styles_stub"
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
            text="🎭 Мои аватары",
            callback_data="gallery_avatars"
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
    
    # Получаем доступные варианты из модели
    aspect_options = UserSettings.get_aspect_ratio_options()
    
    buttons = []
    
    # Первая строка: портрет и квадрат
    buttons.append([
        InlineKeyboardButton(
            text=aspect_options["9:16"]["name"] + " (9:16)",
            callback_data="aspect_ratio:9:16"
        ),
        InlineKeyboardButton(
            text=aspect_options["1:1"]["name"] + " (1:1)",
            callback_data="aspect_ratio:1:1"
        )
    ])
    
    # Вторая строка: альбом и A4
    buttons.append([
        InlineKeyboardButton(
            text=aspect_options["16:9"]["name"] + " (16:9)",
            callback_data="aspect_ratio:16:9"
        ),
        InlineKeyboardButton(
            text=aspect_options["3:4"]["name"] + " (3:4)",
            callback_data="aspect_ratio:3:4"
        )
    ])
    
    # Кнопка "Назад"
    buttons.append([
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="avatar_generation_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_imagen4_aspect_ratio_keyboard() -> InlineKeyboardMarkup:
    """Строит клавиатуру выбора соотношения сторон для Imagen 4"""
    
    # Получаем доступные варианты из модели
    aspect_options = UserSettings.get_aspect_ratio_options()
    
    buttons = []
    
    # Первая строка: портрет и квадрат
    buttons.append([
        InlineKeyboardButton(
            text=aspect_options["9:16"]["name"] + " (9:16)",
            callback_data="imagen4_aspect_ratio:9:16"
        ),
        InlineKeyboardButton(
            text=aspect_options["1:1"]["name"] + " (1:1)",
            callback_data="imagen4_aspect_ratio:1:1"
        )
    ])
    
    # Вторая строка: альбом и A4
    buttons.append([
        InlineKeyboardButton(
            text=aspect_options["16:9"]["name"] + " (16:9)",
            callback_data="imagen4_aspect_ratio:16:9"
        ),
        InlineKeyboardButton(
            text=aspect_options["3:4"]["name"] + " (3:4)",
            callback_data="imagen4_aspect_ratio:3:4"
        )
    ])
    
    # Кнопка "Назад" - возврат к меню изображений
    buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="photo_menu"
        )
    ])
    
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
            text="🔄 Еще раз",
            callback_data=f"regenerate:{generation_id}"
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
                callback_data="avatar_generation_menu"
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
                callback_data="avatar_generation_menu"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_imagen4_menu_keyboard(
    user_balance: float,
    generation_cost: float
) -> InlineKeyboardMarkup:
    """Строит клавиатуру главного меню Imagen 4"""
    
    buttons = []
    
    # Проверяем, достаточно ли баланса
    has_balance = user_balance >= generation_cost
    
    if has_balance:
        # Кнопка создания изображения по описанию
        buttons.append([
            InlineKeyboardButton(
                text="📝 По описанию",
                callback_data="imagen4_prompt"
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
    
    # Моя галерея
    buttons.append([
        InlineKeyboardButton(
            text="🖼️ Моя галерея",
            callback_data="my_gallery"
        )
    ])
    
    # Назад к меню изображений
    buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="photo_menu"
        ),
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_imagen4_prompt_keyboard() -> InlineKeyboardMarkup:
    """Строит клавиатуру для ввода промпта Imagen 4"""
    
    buttons = [
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="photo_menu"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 