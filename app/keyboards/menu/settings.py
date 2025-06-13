"""
Клавиатуры для раздела "⚙️ Настройки"
Переиспользует существующий функционал из app/handlers/profile/
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_settings_menu() -> InlineKeyboardMarkup:
    """
    ⚙️ Настройки - управление профилем и предпочтениями
    Переиспользует существующий SettingsHandler
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👤 Профиль",
                callback_data="profile_menu"  # LEGACY - существующий обработчик личного кабинета
            )
        ],
        [
            InlineKeyboardButton(
                text="🔔 Уведомления",
                callback_data="settings_notifications"  # LEGACY - существующий обработчик
            ),
            InlineKeyboardButton(
                text="🌍 Язык",
                callback_data="settings_language"  # LEGACY - существующий обработчик
            )
        ],
        [
            InlineKeyboardButton(
                text="🎨 Интерфейс",
                callback_data="settings_interface"  # LEGACY - существующий обработчик
            ),
            InlineKeyboardButton(
                text="🔒 Приватность",
                callback_data="settings_privacy"  # LEGACY - существующий обработчик
            )
        ],
        [
            InlineKeyboardButton(
                text="💳 Платежи",
                callback_data="settings_payments"  # LEGACY - существующий обработчик
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


def get_settings_menu_legacy() -> InlineKeyboardMarkup:
    """
    LEGACY: Старая версия меню настроек
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