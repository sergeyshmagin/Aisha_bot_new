"""
Клавиатуры для раздела "❓ Помощь"
Переиспользует существующий функционал из app/handlers/profile/
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_help_menu() -> InlineKeyboardMarkup:
    """
    ❓ Помощь - справка и поддержка
    Переиспользует существующий функционал
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📖 Руководство",
                callback_data="profile_help"  # LEGACY - существующий обработчик
            )
        ],
        [
            InlineKeyboardButton(
                text="💬 Поддержка",
                url="https://t.me/aibots_support"  # Прямая ссылка
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 FAQ",
                callback_data="help_faq"  # Новый обработчик (заглушка)
            )
        ],
        [
            InlineKeyboardButton(
                text="🆕 Что нового",
                callback_data="help_changelog"  # Новый обработчик (заглушка)
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="main_menu_v2"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu_v2"
            )
        ]
    ])


def get_help_menu_legacy() -> InlineKeyboardMarkup:
    """
    LEGACY: Старая версия меню помощи
    Перенаправляет на справку профиля
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📖 Справка",
                callback_data="profile_help"  # LEGACY - существующий обработчик
            )
        ]
    ]) 