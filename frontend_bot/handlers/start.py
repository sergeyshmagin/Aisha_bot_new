from telebot.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton
)
# from telebot import TeleBot  # не используется, удаляю

# Импортируй свой бот, если он создаётся в другом месте
from frontend_bot.bot import (
    bot  # путь может отличаться, скорректируй при необходимости
)

# Если у тебя есть функция для главного меню, импортируй её
# from frontend_bot.keyboards.main_menu import main_menu_keyboard

def get_main_menu_keyboard():
    # Заглушка, если нет своей функции
    # Замени на свою реализацию, если есть
    from telebot.types import ReplyKeyboardMarkup, KeyboardButton
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('📷 Создать аватар'))
    return markup


def main_menu_keyboard():
    markup = InlineKeyboardMarkup()
    # Можно добавить другие кнопки
    return markup


def cancel_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            '↩️ Отмена',
            callback_data='cancel_avatar_creation'
        )
    )
    return markup


@bot.message_handler(commands=['start'])
def handle_start(message: Message):
    user = message.from_user
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n"
        f"Добро пожаловать в нашего бота.\n"
        f"Ваш Telegram ID: {user.id}\n"
        f"Username: @{user.username or '-'}"
    )
    bot.send_message(
        message.chat.id,
        welcome_text
    )


# УДАЛЕНО: @bot.message_handler(content_types=['photo'])
# def handle_avatar_photo(message: Message):
#     ...


# УДАЛЕНО: @bot.callback_query_handler(func=lambda call: call.data == 'start_avatar_wizard')
# def handle_start_avatar_wizard(call):
#     ... 