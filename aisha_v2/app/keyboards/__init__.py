"""
Экспорт клавиатур
"""
from aisha_v2.app.keyboards.main import get_main_menu
from aisha_v2.app.keyboards.avatar import *
from aisha_v2.app.keyboards.transcript import *
# from aisha_v2.app.keyboards.business import business_assistant_inline_keyboard  # Удалено, такой переменной нет

__all__ = [
    # Главное меню
    "get_main_menu",
    # Остальные клавиатуры добавить по мере необходимости
]
