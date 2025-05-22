"""Клавиатура главного меню для Telegram-бота Aisha."""

from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from functools import lru_cache


@lru_cache(maxsize=1)
def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру главного меню.

    Клавиатура кэшируется для повышения производительности.
    Returns:
        ReplyKeyboardMarkup: Клавиатура главного меню.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🤖 Бизнес-ассистент"))
    keyboard.add(KeyboardButton("🖼 Работа с фото"))
    keyboard.add(KeyboardButton("❓ Помощь"))
    # keyboard.add(KeyboardButton("🤖 GPT-4o"))
    return keyboard
