"""Модуль для обработки транскрипций и истории файлов через Telegram-бота."""

import os
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from uuid import uuid4
from dotenv import load_dotenv
from frontend_bot.handlers.general import bot  # Импортируем объект бота
from frontend_bot.services.gpt_assistant import format_transcript_with_gpt
from frontend_bot.utils.logger import get_logger
from frontend_bot.keyboards.reply import (
    transcript_format_keyboard,
)
from frontend_bot.services.state_utils import set_state_pg, get_state_pg, clear_state_pg
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
from frontend_bot.services.history_service import add_history_entry, HistoryService
from frontend_bot.services.transcribe_service import process_audio
from frontend_bot.config import settings
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from frontend_bot.services.transcript_service import TranscriptService
from minio import Minio
from datetime import datetime
from database.config import AsyncSessionLocal
import aiofiles
from frontend_bot.texts.menu.texts import (
    BUSINESS_ASSISTANT_MENU_TEXT,
    TRANSCRIBE_MENU_TEXT,
)
from frontend_bot.texts.transcribe.texts import (
    FORMATS_INFO_TEXT,
    PROTOCOL_CAPTION,
    PROTOCOL_ERROR_TEXT,
)
from frontend_bot.repositories.user_repository import UserRepository
from shared_storage.storage_utils import upload_file, download_file
from frontend_bot.services import transcript_cache as user_transcripts_store

logger = get_logger("transcribe")

# Загрузка переменных окружения из .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))
settings.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")

MAX_CHUNK_SIZE = 24 * 1024 * 1024  # 24 МБ

# Инициализация MinIO клиента и сервисов
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)
transcript_service = TranscriptService(minio_client)

def protocol_error_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для ошибок при генерации протокола."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Повторить генерацию протокола"))
    markup.add(KeyboardButton("⬅️ Назад"))
    return markup

@bot.message_handler(func=lambda m: m.text == "📄 Текстовый транскрипт")
async def text_instruction(message: Message):
    """Обработчик выбора режима текстового транскрипта."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await message.reply("Пользователь не найден. Пожалуйста, /start.")
            return
        uuid_user_id = user.id
        try:
            await set_state_pg(uuid_user_id, "transcribe_txt", session)
            await session.commit()
            logger.info(f"[text_instruction] set_state_pg успешно для user_id={uuid_user_id} (type={type(uuid_user_id)})")
            # Проверяем, что состояние действительно обновилось
            state = await get_state_pg(uuid_user_id, session)
            logger.info(f"[text_instruction] Текущее состояние после установки: {state}")
        except Exception as e:
            logger.error(f"[text_instruction] Ошибка при set_state_pg: {e}")
            await bot.send_message(
                message.chat.id,
                "Ошибка при переходе в режим текстового транскрипта. Пожалуйста, попробуйте ещё раз."
            )
            return
    await bot.send_message(
        message.chat.id, "Пожалуйста, отправьте .txt-файл с транскриптом для обработки."
    )

@bot.message_handler(content_types=["document"])
async def handle_text_transcript_file(message: Message):
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await message.reply("Пользователь не найден. Пожалуйста, /start.")
            return
        uuid_user_id = user.id
        logger.info(
            f"Получен документ от {uuid_user_id}: "
            f"{getattr(message.document, 'file_name', 'NO_FILENAME')}"
        )
        try:
            state = await get_state_pg(uuid_user_id, session)
            logger.info(f"[handle_text_transcript_file] Текущее состояние: {state}")
            if not state or state.get("state") != "transcribe_txt":
                logger.info("[handle_text_transcript_file] State не совпадает, обработка прекращена")
                return
            if not message.document or not message.document.file_name.endswith(".txt"):
                logger.info("[handle_text_transcript_file] Файл не .txt, обработка прекращена")
                return
            
            file_info = await bot.get_file(message.document.file_id)
            downloaded_file = await bot.download_file(file_info.file_path)
            
            # Загружаем файл в MinIO
            minio_key = f"{uuid_user_id}/{message.document.file_name}"
            await upload_file(
                bucket=settings.MINIO_BUCKETS["transcripts"],
                object_name=minio_key,
                data=downloaded_file,
                content_type="text/plain"
            )
            # Сохраняем MinIO-ключ в кэш
            await user_transcripts_store.set(uuid_user_id, minio_key)
            logger.info(f"[handle_text_transcript_file] transcript_cache.set: user={uuid_user_id}, minio_key={minio_key}")
            # Добавляем запись в историю
            await HistoryService(session).add_entry(
                session,
                str(uuid_user_id),
                "transcribe",
                {
                    "filename": message.document.file_name,
                    "file_key": minio_key,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            await clear_state_pg(uuid_user_id, session)
            await session.commit()
            logger.info(f"[handle_text_transcript_file] Состояние очищено для user_id={uuid_user_id}")
            await bot.send_message(
                message.chat.id,
                "\u2705 Текстовый файл успешно загружен и сохранён как транскрипт.\n"
                "Выберите дальнейшее действие:",
                reply_markup=transcript_format_keyboard(),
            )
        except Exception as e:  
            logger.exception(f"[handle_text_transcript_file] Ошибка при обработке документа: {e}")
            await bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка при обработке файла. Сообщите поддержку.",
            )

@bot.message_handler(func=lambda m: m.text == "ℹ️ О форматах")
async def formats_info(message: Message):
    """Показывает информацию о доступных форматах."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await message.reply("Пользователь не найден. Пожалуйста, /start.")
            return
        uuid_user_id = user.id
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
    """Генерирует протокол заседания в формате Word."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await message.reply("Пользователь не найден. Пожалуйста, /start.")
            return
        uuid_user_id = user.id
        minio_key = await user_transcripts_store.get(uuid_user_id)
        if not minio_key:
            await bot.send_message(
                message.chat.id,
                "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл "
                "или текстовый файл ещё раз.",
                reply_markup=transcript_format_keyboard(),
            )
            return
        try:
            data = await download_file(
                bucket=settings.MINIO_BUCKETS["transcripts"],
                object_name=minio_key
            )
            transcript = data.decode("utf-8")
        except Exception as e:
            logger.error(f"Ошибка при скачивании транскрипта из MinIO: {e}")
            await bot.send_message(
                message.chat.id,
                "Ошибка при получении транскрипта из хранилища.",
                reply_markup=transcript_format_keyboard(),
            )
            return
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
                f"protocol_{uuid_user_id}_" f"{datetime.now().strftime('%Y-%m-%d_%H-%M')}.docx"
            )
            async with aiofiles.open(temp_filename, "rb") as f:
                data = await f.read()
                await bot.send_document(
                    message.chat.id,
                    (filename, io.BytesIO(data)),
                    caption="Протокол заседания (Word)",
                    reply_markup=transcript_format_keyboard(),
                )
            await async_remove(temp_filename)
            # Добавляем запись в историю
            await HistoryService(session).add_entry(
                session,
                str(uuid_user_id),
                "protocol",
                {
                    "filename": filename,
                    "type": "word",
                    "created_at": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.exception(f"Ошибка при формировании протокола: {e}")
            await bot.send_message(
                message.chat.id,
                "Что-то пошло не так при формировании протокола. "
                "Вы можете повторить попытку или выбрать другой формат.",
                reply_markup=protocol_error_keyboard(),
            )

@bot.message_handler(func=lambda m: m.text == "Повторить генерацию протокола")
async def retry_meeting_protocol(message: Message):
    """Повторяет генерацию протокола заседания."""
    await send_meeting_protocol(message)

async def transcribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает аудиосообщения и транскрибирует их.
    """
    try:
        message = update.message
        if not message:
            return

        # Проверяем, что это аудиосообщение
        if not (message.voice or message.audio):
            await message.reply_text("Пожалуйста, отправьте голосовое сообщение или аудиофайл.")
            return

        # Отправляем сообщение о начале обработки
        status_message = await message.reply_text("🎙️ Начинаю транскрибацию...")

        # Обрабатываем аудио
        result = await process_audio(
            message=message,
            bot=context.bot,
            openai_api_key=settings.OPENAI_API_KEY,
            storage_dir=str(STORAGE_DIR),
            transcripts_dir=str(STORAGE_DIR / "transcripts")
        )

        if not result.success:
            error_msg = "❌ Ошибка при транскрибации"
            if result.error == "unsupported_format":
                error_msg = "❌ Неподдерживаемый формат аудио"
            await status_message.edit_text(error_msg)
            return

        # Получаем последний транскрипт пользователя
        telegram_id = message.from_user.id
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                await status_message.edit_text("❌ Пользователь не найден")
                return
            uuid_user_id = user.id
            transcripts = await transcript_service.list_user_transcripts(
                user_id=uuid_user_id,
                limit=1
            )
            
            if not transcripts:
                await status_message.edit_text("❌ Не удалось найти транскрипт")
                return
            
            transcript = transcripts[0]
            
            # Добавляем запись в историю
            await HistoryService(session).add_entry(
                session,
                str(uuid_user_id),
                "transcribe",
                {
                    "filename": transcript.filename,
                    "file_path": transcript.file_path,
                    "created_at": datetime.now().isoformat()
                }
            )
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [
                InlineKeyboardButton("📝 Протокол", callback_data="protocol"),
                InlineKeyboardButton("📋 Задачи", callback_data="todo")
            ],
            [
                InlineKeyboardButton("📄 Сводка", callback_data="summary"),
                InlineKeyboardButton("📋 MoM", callback_data="mom")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await status_message.edit_text(
            "✅ Транскрибация завершена! Выберите формат:",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.exception(f"[transcribe_handler] Ошибка: {e}")
        await status_message.edit_text("❌ Произошла ошибка при транскрибации")
