import aiofiles
from frontend_bot.keyboards.reply import transcript_format_keyboard
from frontend_bot.services.file_utils import async_exists
from frontend_bot.services import user_transcripts_store
import io

async def get_user_transcript_or_error(bot, message, logger=None):
    user_id = message.from_user.id
    logger.info(f"[DEBUG] Getting transcript for user {user_id}")
    transcript_path = await user_transcripts_store.get(user_id)
    logger.info(f"[DEBUG] transcript_path: {transcript_path}")
    if not transcript_path or not await async_exists(transcript_path):
        logger.info(f"[DEBUG] No transcript found for user {user_id}")
        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл или текстовый файл ещё раз.",
            reply_markup=transcript_format_keyboard(),
        )
        return None
    try:
        async with aiofiles.open(transcript_path, "r", encoding="utf-8") as f:
            transcript = await f.read()
        logger.info(f"[DEBUG] Read transcript, length: {len(transcript)}")
        if not transcript.strip():
            logger.info("[DEBUG] Empty transcript")
            await bot.send_message(
                message.chat.id,
                "что-то пошло не так",
                reply_markup=transcript_format_keyboard(),
            )
            return None
        return transcript
    except Exception as e:
        if logger:
            logger.exception("Ошибка при чтении файла транскрипта")
        await bot.send_message(
            message.chat.id,
            "что-то пошло не так",
            reply_markup=transcript_format_keyboard(),
        )
        return None

async def send_document_with_caption(bot, chat_id, filename, data, caption: str, reply_markup=None):
    """
    Отправляет документ с подписью и клавиатурой.
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

async def send_transcript_error(bot, chat_id, error_msg: str, reply_markup=None):
    """
    Отправляет сообщение об ошибке с клавиатурой.
    """
    await bot.send_message(
        chat_id,
        error_msg,
        reply_markup=reply_markup,
    ) 