"""
Основной роутер для модуля личного кабинета пользователя
"""
from aiogram import Router

from .main_handler import router as main_router
from .balance_handler import router as balance_router
from .settings_handler import router as settings_router
from .stats_handler import router as stats_router

# Создаем основной роутер профиля
profile_router = Router(name="profile")

# Включаем все подроутеры
profile_router.include_router(main_router)
profile_router.include_router(balance_router)
profile_router.include_router(settings_router)
profile_router.include_router(stats_router)

# Регистрируем дополнительные обработчики
from aiogram import F
from aiogram.types import CallbackQuery

from .main_handler import profile_handler
from .balance_handler import balance_handler
from .settings_handler import SettingsHandler
from .stats_handler import StatsHandler

# Создаем экземпляры обработчиков
settings_handler = SettingsHandler()
stats_handler = StatsHandler()

# Регистрируем основные callback'и
@profile_router.callback_query(F.data == "profile_settings")
async def show_settings_callback(callback: CallbackQuery, state):
    """Callback для показа настроек"""
    await settings_handler.show_settings(callback, state)

@profile_router.callback_query(F.data == "profile_statistics")  
async def show_statistics_callback(callback: CallbackQuery, state):
    """Callback для показа статистики"""
    await stats_handler.show_statistics(callback, state)

# Настройки уведомлений
@profile_router.callback_query(F.data == "settings_notifications")
async def settings_notifications(callback: CallbackQuery):
    """Настройки уведомлений"""
    text = """🔔 <b>Настройки уведомлений</b>

<b>Выберите типы уведомлений:</b>

✅ <b>Аватары</b> — о завершении обучения
✅ <b>Баланс</b> — о пополнении и списаниях
✅ <b>Генерации</b> — о готовности изображений
✅ <b>Обновления</b> — новые функции и улучшения
❌ <b>Промо</b> — специальные предложения
❌ <b>Советы</b> — рекомендации по использованию

💡 <i>Критически важные уведомления всегда включены</i>"""

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔔 Аватары: ✅", callback_data="toggle_notif_avatars"),
            InlineKeyboardButton(text="💰 Баланс: ✅", callback_data="toggle_notif_balance")
        ],
        [
            InlineKeyboardButton(text="🎨 Генерации: ✅", callback_data="toggle_notif_generations"),
            InlineKeyboardButton(text="📢 Обновления: ✅", callback_data="toggle_notif_updates")
        ],
        [
            InlineKeyboardButton(text="🎁 Промо: ❌", callback_data="toggle_notif_promo"),
            InlineKeyboardButton(text="💡 Советы: ❌", callback_data="toggle_notif_tips")
        ],
        [
            InlineKeyboardButton(text="🔙 К настройкам", callback_data="profile_settings")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# Настройки языка
@profile_router.callback_query(F.data == "settings_language")
async def settings_language(callback: CallbackQuery):
    """Настройки языка и региона"""
    text = """🌍 <b>Язык и регион</b>

<b>Язык интерфейса:</b> Русский 🇷🇺
<b>Часовой пояс:</b> UTC+5 (Алматы) 🇰🇿
<b>Формат даты:</b> ДД.ММ.ГГГГ
<b>Валюта:</b> Тенге (₸)

<b>Доступные языки:</b>
• 🇷🇺 Русский (текущий)
• 🇺🇸 English
• 🇰🇿 Қазақша

<b>Часовые пояса:</b>
• UTC+5 Алматы (текущий)
• UTC+6 Астана
• UTC+3 Москва
• UTC+0 UTC"""

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en"),
            InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kz")
        ],
        [
            InlineKeyboardButton(text="🕐 Изменить часовой пояс", callback_data="change_timezone")
        ],
        [
            InlineKeyboardButton(text="🔙 К настройкам", callback_data="profile_settings")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# Прочие настройки
@profile_router.callback_query(F.data.startswith("toggle_notif_"))
async def toggle_notification(callback: CallbackQuery):
    """Переключение настроек уведомлений"""
    await callback.answer("💾 Настройка сохранена", show_alert=True)

@profile_router.callback_query(F.data.startswith("lang_"))
async def change_language(callback: CallbackQuery):
    """Изменение языка"""
    lang = callback.data.split("_")[1]
    lang_names = {"ru": "Русский", "en": "English", "kz": "Қазақша"}
    await callback.answer(f"🌍 Язык изменен на {lang_names.get(lang, 'неизвестный')}", show_alert=True)

@profile_router.callback_query(F.data == "settings_interface")
async def settings_interface(callback: CallbackQuery):
    """Настройки интерфейса"""
    await callback.answer("🎨 Настройки интерфейса в разработке", show_alert=True)

@profile_router.callback_query(F.data == "settings_payments")
async def settings_payments(callback: CallbackQuery):
    """Настройки платежей"""
    await callback.answer("💳 Настройки платежей в разработке", show_alert=True)

@profile_router.callback_query(F.data == "settings_privacy")
async def settings_privacy(callback: CallbackQuery):
    """Настройки приватности"""
    await callback.answer("🔒 Настройки приватности в разработке", show_alert=True) 