from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# from telebot import TeleBot  # не используется, удаляю

# Импортируй свой бот, если он создаётся в другом месте
from frontend_bot.bot import (
    bot,  # путь может отличаться, скорректируй при необходимости
)

# Если у тебя есть функция для главного меню, импортируй её
# from frontend_bot.keyboards.main_menu import main_menu_keyboard

from frontend_bot.texts.menu.texts import START_WELCOME_TEXT
from frontend_bot.services.shared_menu import send_main_menu


def cancel_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("↩️ Отмена", callback_data="cancel_avatar_creation"))
    return markup


@bot.message_handler(commands=["start"])
async def handle_start(message: Message):
    user = message.from_user
    welcome_text = START_WELCOME_TEXT.format(
        first_name=user.first_name, user_id=user.id, username=user.username or "-"
    )
    await bot.send_message(message.chat.id, welcome_text)
    # Можно сразу показать главное меню:
    await send_main_menu(bot, message)


# УДАЛЕНО: @bot.message_handler(content_types=['photo'])
# def handle_avatar_photo(message: Message):
#     ...


# УДАЛЕНО: @bot.callback_query_handler(func=lambda call: call.data == 'start_avatar_wizard')
# def handle_start_avatar_wizard(call):
#     ...
