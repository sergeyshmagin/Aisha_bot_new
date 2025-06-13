"""
Клавиатуры для раздела "🤖 Бизнес-ассистент"

Переиспользует существующий функционал из app/keyboards/main.py
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_business_menu_v2() -> InlineKeyboardMarkup:
    """
    🤖 Бизнес-ассистент v2 - управление командой и задачами
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📋 Задачи",
                callback_data="tasks_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="📰 Новости",
                callback_data="news_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 Голос в текст",
                callback_data="transcribe_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="👥 В группу",
                callback_data="add_to_chat"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu_v2"
            )
        ]
    ])


def get_tasks_section_menu() -> InlineKeyboardMarkup:
    """
    📋 Задачи - управление задачами и проектами
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Новая задача",
                callback_data="task_create"
            ),
            InlineKeyboardButton(
                text="📋 Мои задачи",
                callback_data="task_list"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Проекты",
                callback_data="project_list"
            ),
            InlineKeyboardButton(
                text="📈 Аналитика",
                callback_data="task_analytics"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="business_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu_v2"
            )
        ]
    ])


def get_news_section_menu() -> InlineKeyboardMarkup:
    """
    📰 Новости - мониторинг и аналитика
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📱 Мои каналы",
                callback_data="my_channels"
            ),
            InlineKeyboardButton(
                text="➕ Добавить",
                callback_data="add_channel"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔥 Сегодня",
                callback_data="trending_today"
            ),
            InlineKeyboardButton(
                text="📊 За неделю",
                callback_data="trending_week"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎯 Контент",
                callback_data="content_from_news"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="business_menu"
            ),
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu_v2"
            )
        ]
    ]) 