"""Обработчики главного меню и команд Telegram-бота Aisha."""

import os
from dotenv import load_dotenv
from telebot.types import Message
from frontend_bot.keyboards.reply import (
    business_assistant_keyboard,
    photo_menu_keyboard,
    photo_enhance_keyboard,
    ai_photographer_keyboard,
)
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
from frontend_bot.services.state_utils import set_state
from frontend_bot.texts.menu.texts import HELP_TEXT, BUSINESS_ASSISTANT_MENU_TEXT
from frontend_bot.services.shared_menu import send_main_menu
from frontend_bot.bot_instance import bot

# Загрузка переменных окружения из .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))


@bot.message_handler(commands=["start"])
async def start(message: Message) -> None:
    """Обработчик команды /start."""
    await send_main_menu(bot, message)


@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
async def help_handler(message: Message) -> None:
    """Обработчик кнопки 'Помощь'."""
    await bot.send_message(
        message.chat.id,
        HELP_TEXT,
        reply_markup=main_menu_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "🎤 Аудио")
async def audio_instruction(message: Message) -> None:
    """Обработчик кнопки 'Аудио'."""
    await set_state(message.from_user.id, "audio_transcribe")
    await bot.send_message(
        message.chat.id, "Пожалуйста, отправьте аудиофайл (mp3/ogg) для расшифровки."
    )


@bot.message_handler(func=lambda m: m.text == "📄 Текстовый транскрипт")
async def text_instruction(message: Message) -> None:
    """Обработчик кнопки 'Текстовый транскрипт'."""
    await set_state(message.from_user.id, "transcribe_txt")
    await bot.send_message(
        message.chat.id, "Пожалуйста, отправьте .txt-файл с транскриптом для обработки."
    )


@bot.message_handler(func=lambda m: m.text == "🤖 Бизнес-ассистент")
async def business_assistant_menu(message: Message) -> None:
    """Обработчик кнопки 'Бизнес-ассистент'."""
    user_id = message.from_user.id
    await set_state(user_id, "business_assistant")
    await bot.send_message(
        message.chat.id,
        BUSINESS_ASSISTANT_MENU_TEXT,
        reply_markup=business_assistant_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "🖼 Работа с фото")
async def photo_menu(message: Message) -> None:
    """Обработчик кнопки 'Работа с фото'."""
    user_id = message.from_user.id
    await set_state(user_id, "photo_menu")
    await bot.send_message(
        message.chat.id,
        "Выберите действие в разделе 'Работа с фото':",
        reply_markup=photo_menu_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "🤖 GPT-4o")
async def gpt4o_entrypoint(message: Message) -> None:
    """Обработчик входа в режим GPT-4o через Playwright."""
    await set_state(message.from_user.id, "gpt4o_query")
    await bot.send_message(
        message.chat.id,
        (
            "Вы выбрали режим GPT-4o. Пожалуйста, отправьте ваш запрос, "
            "и я обработаю его через GPT-4o (Playwright)."
        ),
    )


@bot.message_handler(func=lambda m: m.text == "✨ Улучшить фото")
async def photo_enhance_menu(message: Message) -> None:
    """Обработчик кнопки 'Улучшить фото'."""
    user_id = message.from_user.id
    await set_state(user_id, "photo_enhance")
    await bot.send_message(
        message.chat.id,
        "Загрузите фотографию для улучшения качества:",
        reply_markup=photo_enhance_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "🧑‍🎨 ИИ фотограф")
async def ai_photographer_menu(message: Message) -> None:
    """Обработчик кнопки 'ИИ фотограф'."""
    user_id = message.from_user.id
    await set_state(user_id, "ai_photographer")
    await bot.send_message(
        message.chat.id,
        "🧑‍🎨 ИИ фотограф\n\nСоздавайте аватары и образы с помощью ИИ.",
        reply_markup=ai_photographer_keyboard(),
    )


# Для запуска используйте:
# import asyncio
# asyncio.run(bot.polling())
