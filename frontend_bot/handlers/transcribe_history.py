"""
Хендлеры для работы с историей транскриптов пользователя.
"""

import os
from telebot.types import Message
from frontend_bot.handlers.general import bot
from frontend_bot.services.history import (
    get_user_history as service_get_user_history,
    remove_last_history_entry as service_remove_last_history_entry,
)
from frontend_bot.keyboards.reply import history_keyboard
from frontend_bot.services.file_utils import async_remove, async_exists
from frontend_bot.utils.logger import get_logger
from frontend_bot.services import user_transcripts_store

logger = get_logger("transcribe_history")

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
TRANSCRIPTS_DIR = os.path.join(STORAGE_DIR, "transcripts")


@bot.message_handler(commands=["history"])
async def show_history(message: Message):
    user_id = message.from_user.id
    entries = await service_get_user_history(str(user_id))
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
        await service_remove_last_history_entry(str(user_id))
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
