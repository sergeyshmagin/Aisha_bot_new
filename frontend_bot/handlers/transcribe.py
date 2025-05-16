"""Модуль для обработки транскрипций и истории файлов через Telegram-бота."""

import os
import aiofiles
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from uuid import uuid4
from dotenv import load_dotenv
from frontend_bot.handlers.general import bot  # Импортируем объект бота
from frontend_bot.services.gpt_assistant import format_transcript_with_gpt
from frontend_bot.utils.logger import get_logger
from frontend_bot.keyboards.reply import (
    transcript_format_keyboard,
)
from frontend_bot.services.state_utils import set_state, get_state, clear_state
from frontend_bot.services.file_utils import (
    async_remove,
    async_makedirs,
    async_exists,
)
import io
from frontend_bot.GPT_Prompts.transcribe.prompts import (
    PROTOCOL_PROMPT,
)
import asyncio
from frontend_bot.services.word_generator import generate_protocol_word
from frontend_bot.services.history import add_history_entry, STORAGE_DIR
from frontend_bot.services import user_transcripts_store
from datetime import datetime

logger = get_logger("transcribe")

# Загрузка переменных окружения из .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
TRANSCRIPTS_DIR = os.path.join(STORAGE_DIR, "transcripts")
asyncio.get_event_loop().run_until_complete(async_makedirs(STORAGE_DIR, exist_ok=True))
asyncio.get_event_loop().run_until_complete(
    async_makedirs(TRANSCRIPTS_DIR, exist_ok=True)
)

MAX_CHUNK_SIZE = 24 * 1024 * 1024  # 24 МБ

HISTORY_FILE = os.path.join(STORAGE_DIR, "history.json")

user_states = {}


def protocol_error_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для ошибок при генерации протокола."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Повторить генерацию протокола"))
    markup.add(KeyboardButton("⬅️ Назад"))
    return markup


@bot.message_handler(func=lambda m: m.text == "📄 Текстовый транскрипт")
async def text_instruction(message: Message):
    await set_state(message.from_user.id, "transcribe_txt")
    logger.info(f"Пользователь {message.from_user.id} выбрал режим: transcribe_txt")
    await bot.send_message(
        message.chat.id, "Пожалуйста, отправьте .txt-файл с транскриптом для обработки."
    )


@bot.message_handler(content_types=["document"])
async def handle_text_transcript_file(message: Message):
    """Обрабатывает загруженные .txt-файлы."""
    logger.info(
        f"Получен документ от {message.from_user.id}: "
        f"{getattr(message.document, 'file_name', 'NO_FILENAME')}"
    )
    try:
        if await get_state(message.from_user.id) != "transcribe_txt":
            logger.info("State не совпадает, обработка прекращена")
            return
        if not message.document or not message.document.file_name.endswith(".txt"):
            logger.info("Файл не .txt, обработка прекращена")
            return
        user_id = message.from_user.id
        user_dir = os.path.join(TRANSCRIPTS_DIR, str(user_id))
        await async_makedirs(user_dir, exist_ok=True)
        file_info = await bot.get_file(message.document.file_id)
        file_path = os.path.join(user_dir, f"transcript_{uuid4()}.txt")
        downloaded_file = await bot.download_file(file_info.file_path)
        logger.info(f"Сохраняю файл по пути: {file_path}")
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(downloaded_file)
        await user_transcripts_store.set(user_id, file_path)
        logger.info("Файл успешно обработан, отправляю сообщение пользователю")
        await clear_state(user_id)
        await bot.send_message(
            message.chat.id,
            "\u2705 Текстовый файл успешно загружен и сохранён как транскрипт.\n"
            "Выберите дальнейшее действие:",
            reply_markup=transcript_format_keyboard(),
        )
    except Exception as e:  
        logger.exception(f"Ошибка при обработке документа: {e}")
        await bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при обработке файла. Сообщите поддержку.",
        )


@bot.message_handler(func=lambda m: m.text == "ℹ️ О форматах")
async def formats_info(message: Message):
    await bot.send_message(
        message.chat.id,
        "📚 Описание форматов:\n\n"
        "📝 Полный официальный транскрипт — структурированный текст встречи с "
        "выделением участников, тем и итогов.\n\n"
        "📄 Сводка на 1 страницу — краткое резюме для руководства.\n\n"
        "📋 MoM — протокол встречи с решениями и задачами.\n\n"
        "✅ ToDo-план — чеклист задач по итогам встречи.\n\n"
        "Выберите нужный формат ниже!",
        reply_markup=transcript_format_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "Протокол заседания (Word)")
async def send_meeting_protocol(message: Message):
    user_id = message.from_user.id
    transcript_path = await user_transcripts_store.get(user_id)
    if not transcript_path or not await async_exists(transcript_path):
        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл "
            "или текстовый файл ещё раз.",
            reply_markup=transcript_format_keyboard(),
        )
        return
    async with aiofiles.open(transcript_path, "r", encoding="utf-8") as f:
        transcript = await f.read()
    await bot.send_chat_action(message.chat.id, "typing")
    await bot.send_message(
        message.chat.id, "🤖 Формирую официальный протокол заседания (Word)..."
    )
    try:
        protocol_text = await format_transcript_with_gpt(
            transcript,
            custom_prompt=PROTOCOL_PROMPT,
            temperature=0.2,
            top_p=0.7,
        )
        logger.info(f"GPT protocol_text: {protocol_text[:200]}...")
        if not protocol_text.strip():
            logger.error("GPT вернул пустой протокол!")
            raise ValueError("GPT вернул пустой протокол")
        temp_filename = await generate_protocol_word(protocol_text)
        filename = (
            f"protocol_{user_id}_" f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}.docx"
        )
        async with aiofiles.open(temp_filename, "rb") as f:
            data = await f.read()
            await bot.send_document(
                message.chat.id,
                (filename, io.BytesIO(data)),
                caption="📄 Протокол заседания (Word)",
                reply_markup=transcript_format_keyboard(),
            )
        await async_remove(temp_filename)
        await add_history_entry(str(user_id), temp_filename, "word")
    except Exception:
        logger.exception("Ошибка при формировании протокола")
        await bot.send_message(
            message.chat.id,
            "Что-то пошло не так при формировании протокола. "
            "Вы можете повторить попытку или выбрать другой формат.",
            reply_markup=protocol_error_keyboard(),
        )


@bot.message_handler(func=lambda m: m.text == "Повторить генерацию протокола")
async def retry_meeting_protocol(message: Message):
    # Просто повторяем вызов генерации протокола
    await send_meeting_protocol(message)


async def handle_transcribe_file(message: Message, file_data: bytes, file_name: str) -> None:
    """Обрабатывает файл для транскрибации."""
    user_id = str(message.from_user.id)
    file_path = await save_transcribe_file(user_id, file_data, file_name, STORAGE_DIR)
    await add_history_entry(user_id, file_name, str(file_path), STORAGE_DIR)
    await bot.send_message(
        message.chat.id,
        f"Файл {file_name} сохранен и добавлен в историю.",
        reply_markup=transcribe_keyboard()
    )
