"""Обработчики главного меню и команд Telegram-бота Aisha."""
import os
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from frontend_bot.keyboards.reply import (
    business_assistant_keyboard, photo_menu_keyboard
)
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
from frontend_bot.services.state_manager import set_state

# Загрузка переменных окружения из .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = AsyncTeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=['start'])
async def start(message: Message) -> None:
    """Обработчик команды /start."""
    await bot.send_message(
        message.chat.id,
        (
            "👋 Привет! Я помогу оживить твои фотографии — "
            "придай им эмоции, голос и волшебство.\n\n"
            "Выбери, что хочешь сделать:"
        ),
        reply_markup=main_menu_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
async def help_handler(message: Message) -> None:
    """Обработчик кнопки 'Помощь'."""
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
async def audio_instruction(message: Message) -> None:
    """Обработчик кнопки 'Аудио'."""
    set_state(message.from_user.id, 'audio_transcribe')
    await bot.send_message(
        message.chat.id,
        "Пожалуйста, отправьте аудиофайл (mp3/ogg) для расшифровки."
    )


@bot.message_handler(func=lambda m: m.text == "📄 Текстовый транскрипт")
async def text_instruction(message: Message) -> None:
    """Обработчик кнопки 'Текстовый транскрипт'."""
    set_state(message.from_user.id, 'transcribe_txt')
    await bot.send_message(
        message.chat.id,
        "Пожалуйста, отправьте .txt-файл с транскриптом для обработки."
    )


@bot.message_handler(func=lambda m: m.text == "🤖 Бизнес-ассистент")
async def business_assistant_menu(message: Message) -> None:
    """Обработчик кнопки 'Бизнес-ассистент'."""
    await bot.send_message(
        message.chat.id,
        "Выберите действие в разделе 'Бизнес-ассистент':",
        reply_markup=business_assistant_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "🖼 Работа с фото")
async def photo_menu(message: Message) -> None:
    """Обработчик кнопки 'Работа с фото'."""
    await bot.send_message(
        message.chat.id,
        "Выберите действие в разделе 'Работа с фото':",
        reply_markup=photo_menu_keyboard()
    )


@bot.message_handler(func=lambda m: m.text == "🤖 GPT-4o")
async def gpt4o_entrypoint(message: Message) -> None:
    """Обработчик входа в режим GPT-4o через Playwright."""
    set_state(message.from_user.id, 'gpt4o_query')
    await bot.send_message(
        message.chat.id,
        (
            "Вы выбрали режим GPT-4o. Пожалуйста, отправьте ваш запрос, "
            "и я обработаю его через GPT-4o (Playwright)."
        )
    )

# Для запуска используйте:
# import asyncio
# asyncio.run(bot.polling())
