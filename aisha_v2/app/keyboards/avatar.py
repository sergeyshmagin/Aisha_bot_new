"""
Клавиатуры для работы с аватарами
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_gender_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора пола аватара
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👨 Мужской",
                    callback_data="gender_male"
                ),
                InlineKeyboardButton(
                    text="👩 Женский",
                    callback_data="gender_female"
                )
            ]
        ]
    )
    return keyboard

def avatar_inline_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать аватар", callback_data="avatar_create"),
         InlineKeyboardButton(text="🖼 Мои аватары", callback_data="avatar_list")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="business_menu")]
    ])
    return kb

def get_avatar_menu() -> InlineKeyboardMarkup:
    """
    Создает меню аватаров с inline-кнопками.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура меню аватаров
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎨 Создать аватар",
                callback_data="avatar_create"
            )
        ],
        [
            InlineKeyboardButton(
                text="🖼 Мои аватары",
                callback_data="avatar_my"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎭 Стили",
                callback_data="avatar_styles"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="back_to_main"
            )
        ]
    ]) 