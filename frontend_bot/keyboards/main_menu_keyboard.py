from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        resize_keyboard=True
    ).add(
        KeyboardButton("🤖 Бизнес-ассистент")
    ).add(
        KeyboardButton("🖼 Работа с фото")
    ).add(
        KeyboardButton("❓ Помощь")
    )
