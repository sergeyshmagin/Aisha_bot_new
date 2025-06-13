"""
Современные клавиатуры для личного кабинета и настроек
Обновленные для работы с новым интерфейсом
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_settings_menu() -> InlineKeyboardMarkup:
    """
    ⚙️ Настройки - современное меню настроек
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👤 Профиль",
                callback_data="profile_dashboard"
            ),
            InlineKeyboardButton(
                text="🔔 Уведомления",
                callback_data="settings_notifications"
            )
        ],
        [
            InlineKeyboardButton(
                text="🌍 Язык",
                callback_data="settings_language"
            ),
            InlineKeyboardButton(
                text="🔒 Приватность",
                callback_data="settings_privacy"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Главное меню",
                callback_data="main_menu"
            )
        ]
    ])


def get_profile_dashboard_menu() -> InlineKeyboardMarkup:
    """
    🏠 Личный кабинет - главная панель управления
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💰 Баланс",
                callback_data="profile_balance_info"
            ),
            InlineKeyboardButton(
                text="➕ Пополнить",
                callback_data="profile_topup_balance"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="profile_statistics"
            ),
            InlineKeyboardButton(
                text="⚙️ Настройки",
                callback_data="profile_settings"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎭 Мои аватары",
                callback_data="avatar_menu"
            ),
            InlineKeyboardButton(
                text="🖼️ Галерея",
                callback_data="my_gallery"
            )
        ],
        [
            InlineKeyboardButton(
                text="❓ Справка",
                callback_data="profile_help"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        ]
    ])


def get_balance_menu() -> InlineKeyboardMarkup:
    """
    💰 Меню управления балансом
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Пополнить баланс",
                callback_data="profile_topup_balance"
            ),
            InlineKeyboardButton(
                text="📈 История",
                callback_data="balance_history"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 В профиль",
                callback_data="profile_dashboard"
            )
        ]
    ])


def get_statistics_menu() -> InlineKeyboardMarkup:
    """
    📊 Меню статистики
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏆 Достижения",
                callback_data="stats_achievements"
            ),
            InlineKeyboardButton(
                text="📈 График",
                callback_data="stats_activity_chart"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 В профиль",
                callback_data="profile_dashboard"
            )
        ]
    ])


def get_profile_settings_menu() -> InlineKeyboardMarkup:
    """
    ⚙️ Меню настроек профиля
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔔 Уведомления",
                callback_data="settings_notifications"
            ),
            InlineKeyboardButton(
                text="🌍 Язык",
                callback_data="settings_language"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔒 Приватность",
                callback_data="settings_privacy"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 К настройкам",
                callback_data="settings_menu_v2"
            )
        ]
    ])


def get_topup_packages_keyboard(packages: list) -> InlineKeyboardMarkup:
    """
    💳 Клавиатура пакетов пополнения
    """
    buttons = []
    for i, package in enumerate(packages):
        button_text = f"{package['amount']} монет"
        if package['bonus'] > 0:
            button_text += f" (+{package['bonus']} 🎁)"
        
        if package['popular']:
            button_text = f"⭐ {button_text}"
        
        price_text = f" • {package['price_kzt']} ₸"
        button_text += price_text
        
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"topup_package_{i}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text="🔙 К балансу",
            callback_data="profile_balance_info"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_methods_keyboard(package_id: int) -> InlineKeyboardMarkup:
    """
    💳 Способы оплаты для пакета
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💳 Kaspi Pay",
                callback_data=f"pay_kaspi_{package_id}"
            ),
            InlineKeyboardButton(
                text="🏦 СБП (РФ)",
                callback_data=f"pay_sbp_{package_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🌐 Другие способы",
                callback_data=f"pay_other_{package_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Выбрать другой пакет",
                callback_data="profile_topup_balance"
            )
        ]
    ])


# === LEGACY SUPPORT ===

def get_settings_menu_legacy() -> InlineKeyboardMarkup:
    """
    LEGACY: Старое меню настроек - перенаправляет на новый интерфейс
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏠 Перейти к новому интерфейсу",
                callback_data="settings_menu_v2"
            )
        ]
    ]) 