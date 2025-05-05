"""Клавиатура эмоций для Telegram-бота Aisha."""
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from functools import lru_cache


@lru_cache(maxsize=1)
def emotion_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает инлайн-клавиатуру с эмоциями и дополнительной кнопкой улучшения фото.

    Клавиатура кэшируется для повышения производительности.
    Returns:
        InlineKeyboardMarkup: Инлайн-клавиатура эмоций.
    """
    keyboard = [
        [InlineKeyboardButton(
            "😊 Улыбка", callback_data="emotion:smile"
        )],
        [InlineKeyboardButton(
            "🥲 Трогательно", callback_data="emotion:soft"
        )],
        [InlineKeyboardButton(
            "🎉 Празднично", callback_data="emotion:celebrate"
        )],
        [InlineKeyboardButton(
            "✨ Улучшить фото",
            callback_data="gfpgan:enhance"
        )]
    ]
    return InlineKeyboardMarkup(keyboard)
