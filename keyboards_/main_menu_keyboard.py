from telegram import ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("📸 Оживить фото")],
            [KeyboardButton("🗣 Говорящее фото"), KeyboardButton("🎁 Видео-поздравление")],
            [KeyboardButton("❓ Помощь")]
        ],
        resize_keyboard=True
    )
