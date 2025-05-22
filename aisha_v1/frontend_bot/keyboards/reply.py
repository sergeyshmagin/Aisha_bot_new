"""
Клавиатуры для различных сценариев взаимодействия с пользователем.

в Telegram-боте Aisha.
"""

from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from functools import lru_cache
from typing import List, Optional, Tuple


def create_keyboard_with_back(buttons: Tuple[str, ...], row_width: int = 1) -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру с кнопками и кнопкой "Назад".
    
    Args:
        buttons: Кортеж текстов кнопок
        row_width: Количество кнопок в ряду
        
    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопками
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=row_width)
    for button in buttons:
        keyboard.add(KeyboardButton(button))
    keyboard.add(KeyboardButton("⬅️ Назад"))
    return keyboard


def error_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для ошибок с кнопками Повторить и Главное меню.

    Returns:
        ReplyKeyboardMarkup: Клавиатура ошибок.
    """
    return create_keyboard_with_back(("Повторить", "Главное меню"))


def back_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру с кнопкой Назад.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопкой Назад.
    """
    return create_keyboard_with_back(())


def transcript_format_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру выбора формата транскрипта.

    Returns:
        ReplyKeyboardMarkup: Клавиатура выбора формата транскрипта.
    """
    buttons = (
        "Полный официальный транскрипт",
        "Сводка на 1 страницу",
        "Сформировать MoM",
        "Сформировать ToDo-план с чеклистами",
        "Протокол заседания (Word)",
        "ℹ️ О форматах"
    )
    return create_keyboard_with_back(buttons)


def history_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для истории файлов пользователя.

    Returns:
        ReplyKeyboardMarkup: Клавиатура истории файлов.
    """
    return create_keyboard_with_back(("🗑 Удалить мой файл",))


def business_assistant_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру для меню 'Бизнес-ассистент'.

    Returns:
        ReplyKeyboardMarkup: Клавиатура бизнес-ассистента.
    """
    return create_keyboard_with_back(("🎤 Аудио", "📄 Текстовый транскрипт"))


def photo_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для меню 'Работа с фото'.
    """
    return create_keyboard_with_back(("✨ Улучшить фото", "🧑‍🎨 ИИ фотограф"))


def ai_photographer_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для меню 'ИИ фотограф'.
    """
    return create_keyboard_with_back(("🖼 Мои аватары", "🖼 Образы"))


def my_avatars_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для меню 'Мои аватары'.
    """
    return create_keyboard_with_back(("📷 Создать аватар", "👁 Просмотреть аватары"))


def avatar_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для подменю 'Аватары'."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.row(KeyboardButton("🧑‍🎨 Создать аватар"), KeyboardButton("↩️ В меню"))
    return keyboard


def build_avatars_keyboard(avatars):
    buttons = ["📷 Создать аватар"]
    for avatar in avatars:
        if not isinstance(avatar, dict):
            continue
        title = avatar.get("title")
        if title:
            buttons.append(str(title))
    return create_keyboard_with_back(tuple(buttons))


def avatar_photo_keyboard():
    """Клавиатура для загрузки фото аватара."""
    return create_keyboard_with_back(("Далее", "Отмена"))


def avatar_gender_keyboard():
    """Клавиатура для выбора пола аватара."""
    keyboard = ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    keyboard.add(
        KeyboardButton("Мужской"),
        KeyboardButton("Женский")
    )
    keyboard.add(KeyboardButton("Отмена"))
    return keyboard


def avatar_name_keyboard():
    """Клавиатура для ввода имени аватара."""
    return create_keyboard_with_back(("Отмена",))


def avatar_confirm_keyboard():
    """Клавиатура для подтверждения создания аватара."""
    keyboard = ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    keyboard.add(
        KeyboardButton("Подтвердить"),
        KeyboardButton("Отмена")
    )
    return keyboard


def photo_enhance_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для сценария улучшения фото.
    """
    return create_keyboard_with_back(("✨ Улучшить фото",))


def transcribe_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для сценария транскрибации.
    """
    return create_keyboard_with_back(("Транскрибировать",))
