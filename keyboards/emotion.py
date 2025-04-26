from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def emotion_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("😊 Улыбка", callback_data="emotion:smile")],
        [InlineKeyboardButton("🥲 Трогательно", callback_data="emotion:soft")],
        [InlineKeyboardButton("🎉 Празднично", callback_data="emotion:celebrate")]
    ])
