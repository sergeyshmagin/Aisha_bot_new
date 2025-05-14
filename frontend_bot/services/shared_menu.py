from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
from frontend_bot.texts.menu.texts import BACK_TO_MENU_TEXT


async def send_main_menu(bot: AsyncTeleBot, message: Message) -> None:
    """
    Асинхронно отправляет пользователю главное меню с текстом и клавиатурой.

    :param bot: Экземпляр асинхронного бота
    :param message: Сообщение пользователя
    """
    await bot.send_message(
        message.chat.id,
        BACK_TO_MENU_TEXT,
        reply_markup=main_menu_keyboard(),
    )
