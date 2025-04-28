"""
Клавиатуры для различных сценариев взаимодействия с пользователем.

в Telegram-боте Aisha.
"""
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from functools import lru_cache


@lru_cache(maxsize=1)
def error_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для ошибок с кнопками Повторить и Главное меню.

    Returns:
        ReplyKeyboardMarkup: Клавиатура ошибок.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Повторить"))
    keyboard.add(KeyboardButton("Главное меню"))
    return keyboard


@lru_cache(maxsize=1)
def back_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру с кнопкой Назад.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопкой Назад.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Назад"))
    return keyboard


@lru_cache(maxsize=1)
def transcript_format_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру выбора формата транскрипта.

    Returns:
        ReplyKeyboardMarkup: Клавиатура выбора формата транскрипта.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Полный официальный транскрипт"))
    keyboard.add(KeyboardButton("Сводка на 1 страницу"))
    keyboard.add(KeyboardButton("Сформировать MoM"))
    keyboard.add(KeyboardButton("Сформировать ToDo-план с чеклистами"))
    keyboard.add(KeyboardButton("Протокол заседания (Word)"))
    keyboard.add(KeyboardButton("ℹ️ О форматах"))
    keyboard.add(KeyboardButton("Назад"))
    return keyboard


@lru_cache(maxsize=1)
def history_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для истории файлов пользователя.

    Returns:
        ReplyKeyboardMarkup: Клавиатура истории файлов.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🗑 Удалить мой файл"))
    keyboard.add(KeyboardButton("Назад"))
    return keyboard


@lru_cache(maxsize=1)
def business_assistant_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для меню 'Бизнес-ассистент'.

    Returns:
        ReplyKeyboardMarkup: Клавиатура бизнес-ассистента.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🎤 Аудио"))
    keyboard.add(KeyboardButton("📄 Текстовый транскрипт"))
    keyboard.add(KeyboardButton("Назад"))
    return keyboard


@lru_cache(maxsize=1)
def photo_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для меню 'Работа с фото'.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton("✨ Улучшить фото"),
        KeyboardButton("🧑‍🎨 Аватары")
    )
    keyboard.add(KeyboardButton("🖼 Образы"))
    keyboard.add(KeyboardButton("Назад"))
    return keyboard


@lru_cache(maxsize=1)
def avatar_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для подменю 'Аватары'."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(
        KeyboardButton("🧑‍🎨 Создать аватар"),
        KeyboardButton("↩️ В меню")
    )
    return keyboard 