"""Заглушки для тестов хендлеров."""

from telebot.types import Message
from frontend_bot.handlers.general import bot
from frontend_bot.keyboards.reply import (
    business_assistant_keyboard,
    photo_menu_keyboard,
    transcript_format_keyboard,
)
from frontend_bot.keyboards.main_menu_keyboard import main_menu_keyboard
import pytest
# from frontend_bot.services.state_utils import set_state
# TODO: Перевести тесты на state_utils с поддержкой PostgreSQL


async def handle_business_assistant_menu(bot, message: Message) -> None:
    """Заглушка для обработчика меню бизнес-ассистента."""
    await bot.send_message(
        message.chat.id,
        "Выберите действие",
        reply_markup=business_assistant_keyboard(),
    )
    # await set_state(message.from_user.id, "business_assistant")


async def handle_business_assistant_history(bot, message: Message) -> None:
    """Заглушка для обработчика истории бизнес-ассистента."""
    await bot.send_message(
        message.chat.id,
        "История диалогов",
    )
    # await set_state(message.from_user.id, "business_assistant_history")


async def handle_business_assistant_new_dialog(bot, message: Message) -> None:
    """Заглушка для обработчика нового диалога бизнес-ассистента."""
    await bot.send_message(
        message.chat.id,
        "Опишите вашу задачу",
    )
    # await set_state(message.from_user.id, "business_assistant_dialog")


async def handle_business_assistant_back(bot, message: Message) -> None:
    """Заглушка для обработчика возврата из бизнес-ассистента."""
    await bot.send_message(
        message.chat.id,
        "Главное меню",
        reply_markup=main_menu_keyboard(),
    )
    # await set_state(message.from_user.id, "main_menu")


async def handle_photo_enhance_menu(bot, message: Message) -> None:
    """Заглушка для обработчика меню улучшения фото."""
    await bot.send_message(
        message.chat.id,
        "Выберите действие",
        reply_markup=photo_menu_keyboard(),
    )
    # await set_state(message.from_user.id, "photo_enhance")


async def handle_photo_enhance_history(bot, message: Message) -> None:
    """Заглушка для обработчика истории улучшения фото."""
    await bot.send_message(
        message.chat.id,
        "История обработок",
    )
    # await set_state(message.from_user.id, "photo_enhance_history")


async def handle_photo_enhance_new(bot, message: Message) -> None:
    """Заглушка для обработчика нового улучшения фото."""
    await bot.send_message(
        message.chat.id,
        "Загрузите фотографию",
    )
    # await set_state(message.from_user.id, "photo_enhance_upload")


async def handle_photo_enhance_back(bot, message: Message) -> None:
    """Заглушка для обработчика возврата из улучшения фото."""
    user_id = message.from_user.id
    # state = await get_state(user_id)
    
    if state == "photo_enhance_history":
        await bot.send_message(
            message.chat.id,
            "Меню улучшения фото",
            reply_markup=photo_menu_keyboard(),
        )
        # await set_state(user_id, "photo_enhance")
    else:
        await bot.send_message(
            message.chat.id,
            "Главное меню",
            reply_markup=main_menu_keyboard(),
        )
        # await set_state(user_id, "main_menu")


async def handle_transcribe_menu(bot, message: Message) -> None:
    """Заглушка для обработчика меню транскрибации."""
    await bot.send_message(
        message.chat.id,
        "Выберите действие",
        reply_markup=transcript_format_keyboard(),
    )
    # await set_state(message.from_user.id, "transcribe")


async def handle_transcribe_history(bot, message: Message) -> None:
    """Заглушка для обработчика истории транскрибации."""
    await bot.send_message(
        message.chat.id,
        "История транскрибаций",
    )
    # await set_state(message.from_user.id, "transcribe_history")


async def handle_transcribe_new(bot, message: Message) -> None:
    """Заглушка для обработчика новой транскрибации."""
    await bot.send_message(
        message.chat.id,
        "Загрузите аудио или видео файл",
    )
    # await set_state(message.from_user.id, "transcribe_upload")


async def handle_transcribe_back(bot, message: Message) -> None:
    """Заглушка для обработчика возврата из транскрибации."""
    user_id = message.from_user.id
    # state = await get_state(user_id)
    
    if state == "transcribe_history":
        await bot.send_message(
            message.chat.id,
            "Меню транскрибации",
            reply_markup=transcript_format_keyboard(),
        )
        # await set_state(user_id, "transcribe")
    else:
        await bot.send_message(
            message.chat.id,
            "Главное меню",
            reply_markup=main_menu_keyboard(),
        )
        # await set_state(user_id, "main_menu") 