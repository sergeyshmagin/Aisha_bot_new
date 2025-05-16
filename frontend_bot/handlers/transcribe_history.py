"""
Обработчики для работы с историей транскрипций.
"""

import os
from telebot.types import Message
from frontend_bot.handlers.general import bot
from frontend_bot.services.history import (
    get_user_history,
    clear_user_history,
    STORAGE_DIR
)
from frontend_bot.keyboards.reply import history_keyboard
from frontend_bot.services.file_utils import async_remove, async_exists
from frontend_bot.utils.logger import get_logger
from frontend_bot.services import user_transcripts_store
from typing import List, Dict, Any
from pathlib import Path
from frontend_bot.services.transcribe_service import delete_user_transcripts

logger = get_logger("transcribe_history")

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
TRANSCRIPTS_DIR = os.path.join(STORAGE_DIR, "transcripts")


@bot.message_handler(commands=["history"])
async def show_history(message: Message):
    user_id = message.from_user.id
    entries = await get_user_history(str(user_id), STORAGE_DIR)
    if entries:
        msg = "Последние файлы:\n"
        for e in reversed(entries):
            msg += f"\n📄 {e['file']} | {e['type']} | {e['result']} | " f"{e['date']}"
        await bot.send_message(
            message.chat.id,
            msg,
            reply_markup=history_keyboard(),
        )
    else:
        await bot.send_message(
            message.chat.id,
            "У вас нет обработанных файлов.",
            reply_markup=history_keyboard(),
        )


@bot.message_handler(func=lambda m: m.text == "🗑 Удалить мой файл")
async def delete_my_file(message: Message):
    user_id = message.from_user.id
    transcript_path = await user_transcripts_store.get(user_id)
    if transcript_path and await async_exists(transcript_path):
        await async_remove(transcript_path)
        await user_transcripts_store.remove(user_id)
        await clear_user_history(str(user_id), STORAGE_DIR)
        await delete_user_transcripts(str(user_id), STORAGE_DIR)
        await bot.send_message(
            message.chat.id,
            "Ваш последний файл удалён.",
            reply_markup=history_keyboard(),
        )
    else:
        await bot.send_message(
            message.chat.id,
            "Нет файла для удаления.",
            reply_markup=history_keyboard(),
        )


async def get_history(user_id: str) -> List[Dict[str, Any]]:
    """Получает историю транскрипций пользователя."""
    return await get_user_history(user_id, STORAGE_DIR)


async def clear_history(user_id: str) -> None:
    """Очищает историю транскрипций пользователя."""
    await clear_user_history(user_id, STORAGE_DIR)
