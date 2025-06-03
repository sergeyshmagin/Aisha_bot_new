"""
Экспорт клавиатур
"""
from app.keyboards.main import get_main_menu
from app.keyboards.avatar_clean import *
from app.keyboards.transcript import *
# from app.keyboards.business import business_assistant_inline_keyboard  # Удалено, такой переменной нет

__all__ = [
    # Главное меню
    "get_main_menu",
    # Остальные клавиатуры добавить по мере необходимости
]
