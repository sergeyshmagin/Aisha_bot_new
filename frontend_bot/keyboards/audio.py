"""Клавиатура для меню работы с аудио в Telegram-боте Aisha."""

from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from functools import lru_cache


@lru_cache(maxsize=1)
def audio_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для меню работы с аудио.

    Returns:
        ReplyKeyboardMarkup: Клавиатура аудио-меню.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Распознать запись встречи"))
    keyboard.add(KeyboardButton("Обработать текстовый транскрипт"))
    keyboard.add(KeyboardButton("⬅️ Назад"))
    return keyboard
