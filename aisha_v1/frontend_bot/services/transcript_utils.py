"""
Утилиты для работы с транскриптами.
"""
import io
import logging
from typing import Optional, Any

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
import aiofiles

from frontend_bot.keyboards.reply import transcript_format_keyboard
from frontend_bot.services.file_utils import async_exists
from frontend_bot.services import transcript_cache as user_transcripts_store
from frontend_bot.utils.logger import get_logger
from frontend_bot.repositories.user_repository import UserRepository
from database.config import AsyncSessionLocal
from frontend_bot.services.minio_client import download_file
from frontend_bot.config import settings

logger = get_logger(__name__)

async def get_user_transcript_or_error(
    bot: AsyncTeleBot,
    message: Message,
    logger: Optional[logging.Logger] = None
) -> Optional[str]:
    """
    Получает транскрипт пользователя или отправляет сообщение об ошибке.
    
    Args:
        bot: Экземпляр бота
        message: Сообщение пользователя
        logger: Логгер (опционально)
        
    Returns:
        Optional[str]: Текст транскрипта или None
    """
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            logger.info(f"[DEBUG] No user found for telegram_id {message.from_user.id}")
            await bot.send_message(
                message.chat.id,
                "Пользователь не найден. Пожалуйста, /start.",
                reply_markup=transcript_format_keyboard(),
            )
            return None
        uuid_user_id = user.id
        logger.info(f"[DEBUG] Getting transcript for user {uuid_user_id}")
        minio_key = await user_transcripts_store.get(uuid_user_id)
        logger.info(f"[DEBUG] minio_key: {minio_key}")
    
    if not minio_key:
        logger.info(f"[DEBUG] No transcript found for user {uuid_user_id}")
        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл или текстовый файл ещё раз.",
            reply_markup=transcript_format_keyboard(),
        )
        return None
        
    try:
        # Скачиваем файл из MinIO
        data = await download_file(
            bucket=settings.MINIO_BUCKETS["transcripts"],
            object_name=minio_key
        )
        transcript = data.decode("utf-8")
        logger.info(f"[DEBUG] Read transcript from MinIO, length: {len(transcript)}")
        if not transcript.strip():
            logger.info("[DEBUG] Empty transcript")
            await bot.send_message(
                message.chat.id,
                "Транскрипт пустой. Пожалуйста, отправьте аудиофайл или текстовый файл ещё раз.",
                reply_markup=transcript_format_keyboard(),
            )
            return None
        return transcript
    except Exception as e:
        if logger:
            logger.exception(f"Ошибка при чтении файла из MinIO: {e}")
        await bot.send_message(
            message.chat.id,
            "Ошибка при чтении файла транскрипта. Пожалуйста, попробуйте ещё раз.",
            reply_markup=transcript_format_keyboard(),
        )
        return None

async def send_document_with_caption(
    bot: AsyncTeleBot,
    chat_id: int,
    filename: str,
    data: bytes,
    caption: str,
    reply_markup: Optional[Any] = None
) -> None:
    """
    Отправляет документ с подписью и клавиатурой.
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        filename: Имя файла
        data: Данные файла
        caption: Подпись к файлу
        reply_markup: Клавиатура (опционально)
    """
    # Универсальная обработка: поддержка bytes и io.BytesIO
    if isinstance(data, bytes):
        file_obj = io.BytesIO(data)
    else:
        file_obj = data  # предполагаем, что это уже io.BytesIO

    await bot.send_document(
        chat_id,
        (filename, file_obj),
        caption=caption,
        reply_markup=reply_markup,
    )

async def send_transcript_error(
    bot: AsyncTeleBot,
    chat_id: int,
    error_msg: str,
    reply_markup: Optional[Any] = None
) -> None:
    """
    Отправляет сообщение об ошибке с клавиатурой.
    
    Args:
        bot: Экземпляр бота
        chat_id: ID чата
        error_msg: Текст ошибки
        reply_markup: Клавиатура (опционально)
    """
    await bot.send_message(
        chat_id,
        error_msg,
        reply_markup=reply_markup,
    ) 