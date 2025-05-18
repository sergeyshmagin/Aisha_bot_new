"""
Хендлеры для загрузки и транскрибации аудиофайлов через Telegram-бота.
"""

import os
from telebot.types import Message
from frontend_bot.handlers.general import bot
from frontend_bot.services.transcribe_service import (
    process_audio,
    cleanup_old_transcripts,
    ensure_transcribe_dirs,
)
from frontend_bot.services.state_utils import set_state_pg, get_state_pg, clear_state_pg
from frontend_bot.keyboards.reply import transcript_format_keyboard
from frontend_bot.services.shared_menu import send_main_menu
from frontend_bot.utils.logger import get_logger
import asyncio
import io
from datetime import datetime
from frontend_bot.repositories.user_repository import UserRepository
from database.config import AsyncSessionLocal
from frontend_bot.config import settings
from shared_storage.storage_utils import download_file, upload_file
from frontend_bot.services import transcript_cache as user_transcripts_store
import aiofiles

logger = get_logger("transcribe_audio")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
TRANSCRIPTS_DIR = os.path.join(STORAGE_DIR, "transcripts")


@bot.message_handler(func=lambda m: m.text == "🎤 Аудио")
async def audio_instruction(message: Message):
    """Включает режим ожидания аудиофайла."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        logger.error(f"User {telegram_id} not found in the database")
        return
    uuid_user_id = user.id  # UUID
    try:
        await set_state_pg(uuid_user_id, "audio_transcribe", session)
        await session.commit()
        logger.info(f"[audio_instruction] set_state_pg успешно для user_id={uuid_user_id} (type={type(uuid_user_id)})")
        # Проверяем, что состояние действительно обновилось
        state = await get_state_pg(uuid_user_id, session)
        logger.info(f"[audio_instruction] Текущее состояние после установки: {state}")
    except Exception as e:
        logger.error(f"[audio_instruction] Ошибка при set_state_pg: {e}")
        await bot.send_message(
            message.chat.id,
            "Ошибка при переходе в режим аудио. Пожалуйста, попробуйте ещё раз."
        )
        return
    await bot.send_message(
        message.chat.id, "Пожалуйста, отправьте аудиофайл (mp3/ogg) для расшифровки."
    )


@bot.message_handler(content_types=["voice", "audio"])
async def transcribe_audio(message: Message):
    """Обрабатывает аудиофайлы и голосовые сообщения."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        logger.error(f"User {telegram_id} not found in the database")
        return
    uuid_user_id = user.id
    logger.info(f"[transcribe_audio] Старт обработки для user_id={uuid_user_id} (type={type(uuid_user_id)})")
    state = await get_state_pg(uuid_user_id, session)
    logger.info(f"[transcribe_audio] Текущее состояние пользователя: {state}")
    if not state or state.get("state") != "audio_transcribe":
        logger.info("[transcribe_audio] Состояние не audio_transcribe, выход")
        await bot.send_message(
            message.chat.id,
            "Пожалуйста, сначала выберите режим 'Аудио' в меню (кнопка 🎤 Аудио)."
        )
        return
    await bot.send_chat_action(message.chat.id, "typing")
    await bot.send_message(message.chat.id, "⏳ Файл получен! Начинаю обработку...")
    result = await process_audio(
        message, bot, OPENAI_API_KEY, STORAGE_DIR, TRANSCRIPTS_DIR, uuid_user_id
    )
    if not result.success:
        error_messages = {
            "file_too_large": f"Файл слишком большой (максимум {settings.MAX_FILE_SIZE / 1024 / 1024}MB)",
            "ffmpeg_not_found": "Ошибка: ffmpeg не установлен или недоступен. Пожалуйста, сообщите администратору.",
            "unsupported_format": "Ваш файл не является поддерживаемой аудиозаписью. "
                                "Пожалуйста, загрузите аудиофайл в одном из следующих форматов: "
                                "mp3, wav, ogg, m4a, flac, aac, wma, opus.",
            "processing_error": "Произошла ошибка при обработке файла. Пожалуйста, попробуйте еще раз."
        }
        error_msg = error_messages.get(result.error, f"Ошибка при обработке файла: {result.error}")
        await bot.send_message(message.chat.id, error_msg)
        return

    # Загружаем файл в MinIO
    async with aiofiles.open(result.transcript_path, "rb") as f:
        transcript_data = await f.read()
    minio_key = f"{uuid_user_id}/{os.path.basename(result.transcript_path)}"
    await upload_file(
        bucket=settings.MINIO_BUCKETS["transcripts"],
        object_name=minio_key,
        data=transcript_data,
        content_type="text/plain"
    )
    # Сохраняем MinIO-ключ в кэш
    await user_transcripts_store.set(uuid_user_id, minio_key)
    logger.info(f"[transcribe_audio] transcript_cache.set: user={uuid_user_id}, minio_key={minio_key}")
    # Успешно — отправляем транскрипт
    filename = f"transcript_{uuid_user_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
    try:
        # Получаем транскрипт из MinIO
        data = await download_file(
            bucket=settings.MINIO_BUCKETS["transcripts"],
            object_name=minio_key
        )
        
        await bot.send_document(
            message.chat.id,
            (filename, io.BytesIO(data)),
            caption="Ваш транскрипт",
            reply_markup=transcript_format_keyboard(),
        )
        # Очищаем состояние
        await clear_state_pg(uuid_user_id, session)
        
    except Exception as e:
        logger.error(f"Ошибка при отправке транскрипта: {str(e)}")
        await bot.send_message(
            message.chat.id,
            "Произошла ошибка при отправке транскрипта. Пожалуйста, попробуйте еще раз."
        )


@bot.message_handler(func=lambda m: m.text == "Повторить")
async def repeat_audio_instruction(message: Message):
    """Просит пользователя отправить аудиофайл заново."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        logger.error(f"User {telegram_id} not found in the database")
        return
    uuid_user_id = user.id
    await bot.send_message(
        message.chat.id,
        "Пожалуйста, отправьте аудиофайл или голосовое сообщение "
        "в этот чат ещё раз.",
        reply_markup=None,
    )
    logger.info(f"User {uuid_user_id} requested to repeat audio upload.")


@bot.message_handler(func=lambda m: m.text == "Главное меню")
async def back_to_main_menu_from_anywhere(message: Message):
    """Возвращает пользователя в главное меню."""
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        logger.error(f"User {telegram_id} not found in the database")
        return
    uuid_user_id = user.id
    await send_main_menu(bot, message)
    logger.info(f"User {uuid_user_id} returned to main menu.")
