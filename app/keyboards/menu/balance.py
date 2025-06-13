"""
Клавиатуры для раздела "💰 Баланс"
Переиспользует существующий функционал из app/handlers/profile/
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_balance_menu() -> InlineKeyboardMarkup:
    """
    💰 Баланс - управление средствами
    Переиспользует существующий ProfileMainHandler
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💰 Мой баланс",
                callback_data="profile_balance_info"  # LEGACY - существующий обработчик
            )
        ],
        [
            InlineKeyboardButton(
                text="➕ Пополнить",
                callback_data="profile_topup_balance"  # LEGACY - существующий обработчик
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 История операций",
                callback_data="balance_history"  # LEGACY - существующий обработчик
            )
        ],
        [
            InlineKeyboardButton(
                text="📈 Аналитика трат",
                callback_data="balance_analytics"  # LEGACY - существующий обработчик
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


def get_balance_menu_legacy() -> InlineKeyboardMarkup:
    """
    LEGACY: Старая версия меню баланса
    Перенаправляет на личный кабинет
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏠 Личный кабинет",
                callback_data="profile_menu"  # LEGACY - существующий обработчик
            )
        ]
    ]) 