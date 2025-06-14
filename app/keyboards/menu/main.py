"""
Главное меню бота - новая структура

6 основных разделов согласно оптимизированной схеме User Flow:
- 🎨 Творчество - процесс создания контента
- 🎭 Мои работы - результаты и управление  
- 🤖 Бизнес-ассистент - рабочие задачи
- 💰 Баланс - финансовые операции
- ⚙️ Настройки - персонализация
- ❓ Помощь - поддержка и обучение
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu(balance: float = None) -> InlineKeyboardMarkup:
    """
    🏠 Главное меню бота - новая структура
    
    6 основных разделов для оптимального User Flow
    
    Args:
        balance: Текущий баланс пользователя для отображения в кнопке
    """
    # Формируем текст кнопки баланса
    balance_text = "💰 Баланс"
    if balance is not None:
        balance_text = f"💰 Баланс ({balance:.0f})"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎨 Творчество",
                callback_data="creativity_menu"
            ),
            InlineKeyboardButton(
                text="🎭 Мои работы",
                callback_data="projects_menu"
            )
        ],
        [
            InlineKeyboardButton(
                text="🤖 Бизнес-ассистент",
                callback_data="business_menu"
            ),
            InlineKeyboardButton(
                text=balance_text,
                callback_data="balance_menu_v2"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚙️ Настройки",
                callback_data="settings_menu_v2"
            ),
            InlineKeyboardButton(
                text="❓ Помощь",
                callback_data="help_menu_v2"
            )
        ]
    ])


# Алиас для совместимости
get_main_menu_v2 = get_main_menu


# ==================== LEGACY ФУНКЦИИ (ЗАКОММЕНТИРОВАНЫ) ====================
# TODO: Удалить после полного перехода на новую структуру

# def get_main_menu_legacy() -> InlineKeyboardMarkup:
#     """
#     🏠 LEGACY: Старое главное меню - 3 основных раздела
#     TODO: Удалить после тестирования новой структуры
#     """
#     return InlineKeyboardMarkup(inline_keyboard=[
#         [
#             InlineKeyboardButton(
#                 text="🎨 Творчество",
#                 callback_data="ai_creativity_menu"  # LEGACY callback_data
#             ),
#             InlineKeyboardButton(
#                 text="🤖 ИИ Ассистент",
#                 callback_data="business_menu"
#             )
#         ],
#         [
#             InlineKeyboardButton(
#                 text="⚙️ Настройки",
#                 callback_data="profile_menu"  # LEGACY callback_data
#             )
#         ]
#     ]) 