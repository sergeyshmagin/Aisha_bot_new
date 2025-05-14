"""
Хендлеры для загрузки и транскрибации аудиофайлов через Telegram-бота.
"""

import os
from telebot.types import Message
from frontend_bot.handlers.general import bot
from frontend_bot.services.transcribe_service import process_audio
from frontend_bot.services.state_manager import set_state, get_state, clear_state
from frontend_bot.keyboards.reply import transcript_format_keyboard
from frontend_bot.services.file_utils import async_makedirs
from frontend_bot.services.shared_menu import send_main_menu
from frontend_bot.utils.logger import get_logger
import asyncio
import io
from datetime import datetime
import aiofiles

logger = get_logger("transcribe_audio")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
TRANSCRIPTS_DIR = os.path.join(STORAGE_DIR, "transcripts")
asyncio.get_event_loop().run_until_complete(async_makedirs(STORAGE_DIR, exist_ok=True))
asyncio.get_event_loop().run_until_complete(
    async_makedirs(TRANSCRIPTS_DIR, exist_ok=True)
)


@bot.message_handler(func=lambda m: m.text == "🎤 Аудио")
async def audio_instruction(message: Message):
    """Включает режим ожидания аудиофайла."""
    await set_state(message.from_user.id, "audio_transcribe")
    await bot.send_message(
        message.chat.id, "Пожалуйста, отправьте аудиофайл (mp3/ogg) для расшифровки."
    )


@bot.message_handler(content_types=["voice", "audio"])
async def transcribe_audio(message: Message):
    """Обрабатывает аудиофайлы и голосовые сообщения."""
    logger.info(
        f"[transcribe_audio] Старт обработки для user_id={message.from_user.id}"
    )
    if await get_state(message.from_user.id) != "audio_transcribe":
        logger.info("[transcribe_audio] Состояние не audio_transcribe, выход")
        return
    await clear_state(message.from_user.id)
    await bot.send_chat_action(message.chat.id, "typing")
    await bot.send_message(message.chat.id, "⏳ Файл получен! Начинаю обработку...")
    result = await process_audio(
        message, bot, OPENAI_API_KEY, STORAGE_DIR, TRANSCRIPTS_DIR
    )
    if not result.success:
        if result.error == "unsupported_format":
            await bot.send_message(
                message.chat.id,
                "Ваш файл не является поддерживаемой аудиозаписью. "
                "Пожалуйста, загрузите аудиофайл в одном из следующих форматов: "
                "mp3, wav, ogg, m4a, flac, aac, wma, opus.",
            )
        else:
            await bot.send_message(
                message.chat.id, f"Ошибка при обработке файла: {result.error}"
            )
        return
    # Успешно — отправляем транскрипт
    filename = f"transcript_{message.from_user.id}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
    async with aiofiles.open(result.transcript_path, "rb") as f:
        data = await f.read()
    await bot.send_document(
        message.chat.id,
        (filename, io.BytesIO(data)),
        caption="Ваш транскрипт",
        reply_markup=transcript_format_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "Повторить")
async def repeat_audio_instruction(message: Message):
    """Просит пользователя отправить аудиофайл заново."""
    await bot.send_message(
        message.chat.id,
        "Пожалуйста, отправьте аудиофайл или голосовое сообщение "
        "в этот чат ещё раз.",
        reply_markup=None,
    )
    logger.info(f"User {message.from_user.id} requested to repeat audio upload.")


@bot.message_handler(func=lambda m: m.text == "Главное меню")
async def back_to_main_menu_from_anywhere(message: Message):
    """Возвращает пользователя в главное меню."""
    await send_main_menu(bot, message)
    logger.info(f"User {message.from_user.id} returned to main menu.")
