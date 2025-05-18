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
from frontend_bot.services.shared_menu import send_main_menu
from frontend_bot.bot_instance import bot
from frontend_bot.texts.menu.texts import BUSINESS_ASSISTANT_MENU_TEXT
from frontend_bot.repositories.user_repository import UserRepository
from frontend_bot.texts.common import HELP_TEXT
from database.config import AsyncSessionLocal

# Загрузка переменных окружения из .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))


@bot.message_handler(commands=["start"])
async def start(message: Message) -> None:
    """Обработчик команды /start."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_or_create(
            telegram_id=telegram_id,
            username=getattr(message.from_user, 'username', None),
            first_name=getattr(message.from_user, 'first_name', None),
            last_name=getattr(message.from_user, 'last_name', None),
            language_code=getattr(message.from_user, 'language_code', None),
            is_bot=getattr(message.from_user, 'is_bot', False),
            is_premium=getattr(message.from_user, 'is_premium', None),
            phone_number=None,
        )
        await user_repo.update_if_changed(
            user,
            username=getattr(message.from_user, 'username', None),
            first_name=getattr(message.from_user, 'first_name', None),
            last_name=getattr(message.from_user, 'last_name', None),
        )
    await send_main_menu(bot, message)


@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
async def help_handler(message: Message) -> None:
    """Обработчик кнопки 'Помощь'."""
    await bot.send_message(
        message.chat.id,
        HELP_TEXT,
        reply_markup=main_menu_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "🤖 Бизнес-ассистент")
async def business_assistant_menu(message: Message) -> None:
    """Обработчик кнопки 'Бизнес-ассистент'."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_or_create(
            telegram_id=telegram_id,
            username=getattr(message.from_user, 'username', None),
            first_name=getattr(message.from_user, 'first_name', None),
            last_name=getattr(message.from_user, 'last_name', None),
            language_code=getattr(message.from_user, 'language_code', None),
            is_bot=getattr(message.from_user, 'is_bot', False),
            is_premium=getattr(message.from_user, 'is_premium', None),
            phone_number=None,
        )
        await user_repo.update_if_changed(
            user,
            username=getattr(message.from_user, 'username', None),
            first_name=getattr(message.from_user, 'first_name', None),
            last_name=getattr(message.from_user, 'last_name', None),
        )
    if not user:
        await bot.send_message(message.chat.id, "Пользователь не найден.")
        return
    uuid_user_id = user.id
    await bot.send_message(
        message.chat.id,
        BUSINESS_ASSISTANT_MENU_TEXT,
        reply_markup=business_assistant_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "🖼 Работа с фото")
async def photo_menu(message: Message) -> None:
    """Обработчик кнопки 'Работа с фото'."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_or_create(
            telegram_id=telegram_id,
            username=getattr(message.from_user, 'username', None),
            first_name=getattr(message.from_user, 'first_name', None),
            last_name=getattr(message.from_user, 'last_name', None),
            language_code=getattr(message.from_user, 'language_code', None),
            is_bot=getattr(message.from_user, 'is_bot', False),
            is_premium=getattr(message.from_user, 'is_premium', None),
            phone_number=None,
        )
        await user_repo.update_if_changed(
            user,
            username=getattr(message.from_user, 'username', None),
            first_name=getattr(message.from_user, 'first_name', None),
            last_name=getattr(message.from_user, 'last_name', None),
        )
    if not user:
        await bot.send_message(message.chat.id, "Пользователь не найден.")
        return
    uuid_user_id = user.id
    await bot.send_message(
        message.chat.id,
        "Выберите действие в разделе 'Работа с фото':",
        reply_markup=photo_menu_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "🤖 GPT-4o")
async def gpt4o_entrypoint(message: Message) -> None:
    """Обработчик входа в режим GPT-4o через Playwright."""
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
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_or_create(
            telegram_id=telegram_id,
            username=getattr(message.from_user, 'username', None),
            first_name=getattr(message.from_user, 'first_name', None),
            last_name=getattr(message.from_user, 'last_name', None),
            language_code=getattr(message.from_user, 'language_code', None),
            is_bot=getattr(message.from_user, 'is_bot', False),
            is_premium=getattr(message.from_user, 'is_premium', None),
            phone_number=None,
        )
        await user_repo.update_if_changed(
            user,
            username=getattr(message.from_user, 'username', None),
            first_name=getattr(message.from_user, 'first_name', None),
            last_name=getattr(message.from_user, 'last_name', None),
        )
    if not user:
        await bot.send_message(message.chat.id, "Пользователь не найден.")
        return
    uuid_user_id = user.id
    await bot.send_message(
        message.chat.id,
        "Загрузите фотографию для улучшения качества:",
        reply_markup=photo_enhance_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "🧑‍🎨 ИИ фотограф")
async def ai_photographer_menu(message: Message) -> None:
    """Обработчик кнопки 'ИИ фотограф'."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_or_create(
            telegram_id=telegram_id,
            username=getattr(message.from_user, 'username', None),
            first_name=getattr(message.from_user, 'first_name', None),
            last_name=getattr(message.from_user, 'last_name', None),
            language_code=getattr(message.from_user, 'language_code', None),
            is_bot=getattr(message.from_user, 'is_bot', False),
            is_premium=getattr(message.from_user, 'is_premium', None),
            phone_number=None,
        )
        await user_repo.update_if_changed(
            user,
            username=getattr(message.from_user, 'username', None),
            first_name=getattr(message.from_user, 'first_name', None),
            last_name=getattr(message.from_user, 'last_name', None),
        )
    if not user:
        await bot.send_message(message.chat.id, "Пользователь не найден.")
        return
    uuid_user_id = user.id
    await bot.send_message(
        message.chat.id,
        "🧑‍🎨 ИИ фотограф\n\nСоздавайте аватары и образы с помощью ИИ.",
        reply_markup=ai_photographer_keyboard(),
    )


# Для запуска используйте:
# import asyncio
# asyncio.run(bot.polling())

# TODO: Перевести на state_utils с поддержкой PostgreSQL
