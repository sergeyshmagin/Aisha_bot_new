import os
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from frontend_bot.keyboards.reply import business_assistant_keyboard, photo_menu_keyboard
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard

# Загрузка переменных окружения из .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = AsyncTeleBot(TELEGRAM_TOKEN)


def audio_menu_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Распознать запись встречи"))
    markup.add(KeyboardButton("Обработать текстовый транскрипт"))
    markup.add(KeyboardButton("Назад"))
    return markup


@bot.message_handler(commands=['start'])
async def start(message):
    await bot.send_message(
        message.chat.id,
        (
            "👋 Привет! Я помогу оживить твои фотографии — придай им эмоции, голос и "
            "волшебство.\n\nВыбери, что хочешь сделать:"
        ),
        reply_markup=main_menu_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
async def help_handler(message):
    await bot.send_message(
        message.chat.id,
        (
            "❓ Справка:\n\n"
            "📸 Оживить фото — добавь эмоции на лице\n"
            "🗣 Сделать говорящим — напиши текст, и фото 'скажет' его\n"
            "🎁 Видео-поздравление — оживлённое поздравление в видеоформате\n\n"
            "Просто отправь фото или нажми кнопку 👇"
        ),
        reply_markup=main_menu_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "🎤 Аудио")
async def audio_instruction(message):
    from frontend_bot.services.state_manager import set_state
    set_state(message.from_user.id, 'audio_transcribe')
    await bot.send_message(
        message.chat.id,
        "Пожалуйста, отправьте аудиофайл (mp3/ogg) для расшифровки."
    )


@bot.message_handler(func=lambda m: m.text == "📄 Текстовый транскрипт")
async def text_instruction(message):
    from frontend_bot.services.state_manager import set_state
    set_state(message.from_user.id, 'transcribe_txt')
    await bot.send_message(
        message.chat.id,
        "Пожалуйста, отправьте .txt-файл с транскриптом для обработки."
    )


@bot.message_handler(func=lambda m: m.text == "Назад")
async def back_to_main_menu(message):
    await bot.send_message(
        message.chat.id,
        "Главное меню. Выберите действие:\n\n"
        "🎤 Аудио — отправить аудиофайл для расшифровки\n"
        "📄 Текстовый транскрипт — отправить текстовый файл для обработки\n"
        "❓ Помощь — узнать о возможностях бота",
        reply_markup=main_menu_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "🤖 Бизнес-ассистент")
async def business_assistant_menu(message):
    await bot.send_message(
        message.chat.id,
        "Выберите действие в разделе 'Бизнес-ассистент':",
        reply_markup=business_assistant_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "🖼 Работа с фото")
async def photo_menu(message):
    await bot.send_message(
        message.chat.id,
        "Выберите действие в разделе 'Работа с фото':",
        reply_markup=photo_menu_keyboard()
    )

# Для запуска используйте:
# import asyncio
# asyncio.run(bot.polling())
