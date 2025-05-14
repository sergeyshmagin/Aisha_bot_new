"""
Хендлеры для генерации протоколов, summary, MoM, ToDo по транскриптам.
"""

import os
import aiofiles
import io
from telebot.types import Message
from frontend_bot.handlers.general import bot
from frontend_bot.services.gpt_assistant import format_transcript_with_gpt
from frontend_bot.keyboards.reply import transcript_format_keyboard
from frontend_bot.services.file_utils import async_remove, async_exists
from frontend_bot.services.word_generator import generate_protocol_word

generate_word_protocol = generate_protocol_word
from frontend_bot.services.history import add_history_entry
from frontend_bot.utils.logger import get_logger
from frontend_bot.GPT_Prompts.transcribe.prompts import (
    PROTOCOL_PROMPT,
    SHORT_SUMMARY_PROMPT,
    MOM_PROMPT,
    TODO_PROMPT,
)
from datetime import datetime
from frontend_bot.services import user_transcripts_store

logger = get_logger("transcribe_protocol")

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
TRANSCRIPTS_DIR = os.path.join(STORAGE_DIR, "transcripts")


@bot.message_handler(func=lambda m: m.text == "Протокол заседания (Word)")
async def send_meeting_protocol(message: Message):
    logger.info(f"[HANDLER] send_meeting_protocol, message.text={message.text!r}")
    user_id = message.from_user.id
    transcript_path = await user_transcripts_store.get(user_id)
    logger.info(f"[DEBUG] user_transcripts: {user_transcripts_store}")
    logger.info(f"[DEBUG] transcript_path for user {user_id}: {transcript_path}")
    if not transcript_path or not await async_exists(transcript_path):
        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл "
            "или текстовый файл ещё раз.",
            reply_markup=transcript_format_keyboard(),
        )
        return
    try:
        async with aiofiles.open(transcript_path, "r", encoding="utf-8") as f:
            transcript = await f.read()
            if not transcript.strip():
                await bot.send_message(
                    message.chat.id,
                    "что-то пошло не так",
                    reply_markup=transcript_format_keyboard(),
                )
                return
    except Exception as e:
        logger.exception("Ошибка при чтении файла транскрипта")
        await bot.send_message(
            message.chat.id,
            "что-то пошло не так",
            reply_markup=transcript_format_keyboard(),
        )
        return

    await bot.send_chat_action(message.chat.id, "typing")
    await bot.send_message(
        message.chat.id, "🤖 Формирую официальный протокол заседания (Word)...")
    await bot.send_chat_action(message.chat.id, "typing")
    await bot.send_message(
        message.chat.id, "🤖 Формирую официальный протокол заседания (Word)..."
    )
    try:
        # Проверяем, что транскрипт не пустой
        if not transcript.strip():
            raise ValueError("что-то пошло не так")

        protocol_text = await format_transcript_with_gpt(
            transcript, custom_prompt=PROTOCOL_PROMPT, temperature=0.2, top_p=0.7
        )
        if not protocol_text.strip():
            await bot.send_message(
                message.chat.id,
                "что-то пошло не так",
                reply_markup=transcript_format_keyboard(),
            )
            return
        logger.info(f"GPT protocol_text: {protocol_text[:200]}...")
        
        if not protocol_text.strip():
            logger.error("GPT вернул пустой протокол!")
            raise ValueError("GPT вернул пустой протокол")

        # Генерируем Word-документ
        temp_filename = await generate_protocol_word(protocol_text)
        if not temp_filename or not await async_exists(temp_filename):
            raise FileNotFoundError("что-то пошло не так")

        filename = (
            f"protocol_{user_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.docx"
        )
        
        async with aiofiles.open(temp_filename, "rb") as f:
            data = await f.read()
            if not data:
                raise ValueError("что-то пошло не так")
            
            logger.info(f"[DEBUG] Sending file: {filename}, size: {len(data)} bytes")
            await bot.send_document(
                message.chat.id,
                (filename, io.BytesIO(data)),
                caption="📄 Протокол заседания (Word)",
                reply_markup=transcript_format_keyboard(),
            )
        
        await async_remove(temp_filename)
        await add_history_entry(str(user_id), temp_filename, "word", "protocol")
        
    except ValueError as e:
        logger.error(f"Ошибка значения: {str(e)}")
        error_msg = str(e)
    except FileNotFoundError as e:
        logger.error(f"Ошибка файла: {str(e)}")
        error_msg = str(e)
    except Exception as e:
        logger.exception("Неожиданная ошибка при формировании протокола")
        error_msg = "Что-то пошло не так при формировании протокола. Вы можете повторить попытку или выбрать другой формат."
    
    if 'error_msg' in locals():
        await bot.send_chat_action(message.chat.id, "typing")
        await bot.send_message(
            message.chat.id,
            error_msg,
            reply_markup=transcript_format_keyboard(),
        )


@bot.message_handler(func=lambda m: m.text == "Повторить генерацию протокола")
async def retry_meeting_protocol(message: Message):
    await send_meeting_protocol(message)


@bot.message_handler(func=lambda m: m.text and "сводка на 1 страницу" in m.text.lower())
async def send_short_summary(message: Message):
    logger.info(f"[HANDLER] send_short_summary, message.text={message.text!r}")
    user_id = message.from_user.id
    transcript_path = await user_transcripts_store.get(user_id)
    logger.info(f"[DEBUG] user_transcripts: {user_transcripts_store}")
    logger.info(f"[DEBUG] transcript_path for user {user_id}: {transcript_path}")
    if not transcript_path or not await async_exists(transcript_path):
        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл или текстовый файл ещё раз.",
            reply_markup=transcript_format_keyboard(),
        )
        return
    try:
        async with aiofiles.open(transcript_path, "r", encoding="utf-8") as f:
            transcript = await f.read()
        if not transcript.strip():
            logger.info("[DEBUG] Отправляю сообщение: transcript пустой")
            await bot.send_message(
                message.chat.id,
                "что-то пошло не так",
                reply_markup=transcript_format_keyboard(),
            )
            return
    except Exception as e:
        logger.exception("Ошибка при чтении файла транскрипта")
        await bot.send_message(
            message.chat.id,
            "что-то пошло не так",
            reply_markup=transcript_format_keyboard(),
        )
        return

    await bot.send_chat_action(message.chat.id, "typing")
    await bot.send_message(
        message.chat.id, "🤖 Формирую сводку на 1 страницу с помощью GPT..."
    )
    try:
        summary = await format_transcript_with_gpt(
            transcript, custom_prompt=SHORT_SUMMARY_PROMPT, temperature=0.3, top_p=0.7
        )
        if not summary.strip():
            logger.info("[DEBUG] Отправляю сообщение: summary пустой")
            await bot.send_message(
                message.chat.id,
                "что-то пошло не так",
                reply_markup=transcript_format_keyboard(),
            )
            return
        filename = f"summary_{user_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
        data = summary.encode("utf-8")
        logger.info(f"[DEBUG] Sending file: {filename}, size: {len(data)} bytes")
        await bot.send_document(
            message.chat.id,
            (filename, io.BytesIO(data)),
            caption="📝 Сводка на 1 страницу",
            reply_markup=transcript_format_keyboard(),
        )
    except Exception:
        logger.exception("Ошибка при формировании сводки")
        await bot.send_message(
            message.chat.id,
            "Что-то пошло не так. Попробуйте ещё раз или обратитесь в поддержку.",
            reply_markup=transcript_format_keyboard(),
        )


@bot.message_handler(func=lambda m: m.text and "mom" in m.text.lower())
async def send_mom(message: Message) -> None:
    """
    Формирует Minutes of Meeting (MoM) из транскрипта и отправляет пользователю.
    
    Args:
        message: Сообщение от пользователя
    """
    logger.info(f"[HANDLER] send_mom, message.text={message.text!r}")
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
    
    try:
        f_ctx = aiofiles.open(transcript_path, "r", encoding="utf-8")
        if hasattr(f_ctx, "__await__"):
            f_ctx = await f_ctx
        async with f_ctx as f:
            transcript = await f.read()

        if not transcript.strip():
            await bot.send_chat_action(message.chat.id, "typing")
            await bot.send_message(
                message.chat.id,
                "Транскрипт пустой. Пожалуйста, отправьте аудиофайл или текстовый файл ещё раз.",
                reply_markup=transcript_format_keyboard(),
            )
            return
        
        await bot.send_chat_action(message.chat.id, "typing")
        await bot.send_message(
            message.chat.id, "🤖 Формирую MoM (Minutes of Meeting) с помощью GPT..."
        )
        
        try:
            mom_text = await format_transcript_with_gpt(
                transcript, custom_prompt=MOM_PROMPT, temperature=0.2, top_p=0.6
            )
        except Exception as exc:
            logger.exception(f"Ошибка при формировании MoM: {exc}")
            await bot.send_chat_action(message.chat.id, "typing")
            await bot.send_message(
                message.chat.id,
                "Что-то пошло не так при формировании MoM. Пожалуйста, попробуйте ещё раз.",
                reply_markup=transcript_format_keyboard(),
            )
            return

        if not mom_text.strip():
            logger.error("GPT вернул пустой MoM!")
            await bot.send_message(
                message.chat.id,
                "Что-то пошло не так при формировании MoM. Пожалуйста, попробуйте ещё раз.",
                reply_markup=transcript_format_keyboard(),
            )
            return

        filename = f"mom_{user_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
        data = mom_text.encode("utf-8")
        logger.info(f"[DEBUG] Sending file: {filename}, size: {len(data)} bytes")
        
        await bot.send_document(
            message.chat.id,
            (filename, io.BytesIO(data)),
            caption="📝 MoM (Minutes of Meeting)",
            reply_markup=transcript_format_keyboard(),
        )
        
    except Exception as exc:
        logger.exception(f"Ошибка при формировании MoM: {exc}")
        await bot.send_chat_action(message.chat.id, "typing")
        await bot.send_message(
            message.chat.id,
            "Что-то пошло не так при формировании MoM. Пожалуйста, попробуйте ещё раз.",
            reply_markup=transcript_format_keyboard(),
        )


@bot.message_handler(func=lambda m: m.text and "todo" in m.text.lower())
async def send_todo_checklist(message: Message):
    logger.info(f"[HANDLER] send_todo_checklist, message.text={message.text!r}")
    user_id = message.from_user.id
    transcript_path = await user_transcripts_store.get(user_id)
    logger.info(f"[DEBUG] user_transcripts: {user_transcripts_store}")
    logger.info(f"[DEBUG] transcript_path for user {user_id}: {transcript_path}")
    if not transcript_path or not await async_exists(transcript_path):
        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл или текстовый файл ещё раз.",
            reply_markup=transcript_format_keyboard(),
        )
        return
    try:
        async with aiofiles.open(transcript_path, "r", encoding="utf-8") as f:
            transcript = await f.read()
            if not transcript.strip():
                await bot.send_message(
                    message.chat.id,
                    "что-то пошло не так",
                    reply_markup=transcript_format_keyboard(),
                )
                return
    except Exception as e:
        logger.exception("Ошибка при чтении файла транскрипта")
        await bot.send_message(
            message.chat.id,
            "что-то пошло не так",
            reply_markup=transcript_format_keyboard(),
        )
        return

        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл " "ещё раз.",
            reply_markup=transcript_format_keyboard(),
        )
        return
    async with aiofiles.open(transcript_path, "r", encoding="utf-8") as f:
        transcript = await f.read()
    if not transcript.strip():
        await bot.send_message(
            message.chat.id,
            "Транскрипт пустой. Пожалуйста, отправьте аудиофайл ещё раз.",
            reply_markup=transcript_format_keyboard(),
        )
        return
    await bot.send_chat_action(message.chat.id, "typing")
    await bot.send_message(
        message.chat.id, "🤖 Формирую ToDo-план с чеклистами с помощью GPT..."
    )
    try:
        todo_text = await format_transcript_with_gpt(
            transcript, custom_prompt=TODO_PROMPT, temperature=0.5, top_p=0.9
        )
        if not todo_text.strip():
            await bot.send_message(
                message.chat.id,
                "что-то пошло не так",
                reply_markup=transcript_format_keyboard(),
            )
            return
        if not todo_text.strip():
            logger.error("GPT вернул пустой ToDo!")
            raise ValueError("GPT вернул пустой ToDo")
        filename = f"todo_{user_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
        data = todo_text.encode("utf-8")
        logger.info(f"[DEBUG] Sending file: {filename}, size: {len(data)} bytes")
        await bot.send_document(
            message.chat.id,
            (filename, io.BytesIO(data)),
            caption="📝 ToDo-план с чеклистами",
            reply_markup=transcript_format_keyboard(),
        )
    except Exception:
        logger.exception("Ошибка при формировании ToDo")
        await bot.send_message(
            message.chat.id,
            "Что-то пошло не так. Попробуйте ещё раз или обратитесь в поддержку.",
            reply_markup=transcript_format_keyboard(),
        )


@bot.message_handler(
    func=lambda m: m.text and "официальный транскрипт" in m.text.lower()
)
async def send_full_official_transcript(message: Message):
    logger.info(
        f"[HANDLER] send_full_official_transcript, message.text={message.text!r}"
    )
    user_id = message.from_user.id
    transcript_path = await user_transcripts_store.get(user_id)
    logger.info(f"[DEBUG] user_transcripts: {user_transcripts_store}")
    logger.info(f"[DEBUG] transcript_path for user {user_id}: {transcript_path}")
    if not transcript_path or not await async_exists(transcript_path):
        await bot.send_message(
            message.chat.id,
            "Нет сохранённого транскрипта. Пожалуйста, отправьте аудиофайл или текстовый файл ещё раз.",
            reply_markup=transcript_format_keyboard(),
        )
        return
    async with aiofiles.open(transcript_path, "r", encoding="utf-8") as f:
        transcript = await f.read()
    await bot.send_chat_action(message.chat.id, "typing")
    await bot.send_message(
        message.chat.id, "🤖 Формирую полный официальный транскрипт с помощью GPT..."
    )
    try:
        full_prompt = (
            "Ты — профессиональный аналитик и бизнес-ассистент. "
            "На вход подаётся текст стенограммы рабочей встречи в "
            "неструктурированном виде (реплики участников идут сплошняком, "
            "без указания говорящего и без форматирования).\n"
            "Твоя задача:\n"
            "1. Выделить **участников встречи** и их роли (если указано).\n"
            "2. Сформировать **читабельный, логически разбитый транскрипт**, "
            "выделяя:\n"
            "   - Кто говорит (например, **Игорь:**).\n"
            "   - Темы обсуждения (блоками: 🔹 Архитектура, 🔹 Сроки, "
            "🔹 Организация работы и т.п.).\n"
            "3. Минимально редактировать речь: убрать повторы, «э-э», "
            "вводные слова, но не искажать смысл.\n"
            "4. Сохранить **хронологический порядок** и ключевые детали "
            "договорённостей.\n"
            "5. В финале — выделить **итоги встречи** и следующие шаги.\n"
            "Сохраняй деловой стиль, избегай художественности.\n\n"
            "Пример форматирования:\n---\n"
            "## 🗓 Название встречи  \n"
            "**Формат:** Онлайн  \n"
            "**Участники:**  \n"
            "– Иван (PM), – Ольга (Аналитик), – Сергей (Dev)\n\n"
            "### 🔹 Обсуждение архитектуры  \n"
            "**Ольга:** Обновили стек, теперь используем React и WebView...  \n"
            "**Сергей:** Нужно отдельный репозиторий, там уже есть наброски...\n\n"
            "### 🔹 Дальнейшие шаги  \n"
            "- Создать форк на Android  \n"
            "- Подготовить URL для WebView  \n---\n\n"
            "Начни с анализа участников, потом переходи к структурированной "
            "расшифровке. Входной текст ниже:"
        )
        formatted = await format_transcript_with_gpt(
            transcript, custom_prompt=full_prompt, temperature=0.2, top_p=0.7
        )
        logger.info(f"[DEBUG] Sending full transcript, length: {len(formatted)}")
        filename = (
            f"full_transcript_{user_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
        )
        data = formatted.encode("utf-8")
        await bot.send_document(
            message.chat.id,
            (filename, io.BytesIO(data)),
            caption="📝 Полный официальный транскрипт",
            reply_markup=transcript_format_keyboard(),
        )
    except Exception:
        logger.exception("Ошибка при формировании полного транскрипта")
        await bot.send_message(
            message.chat.id,
            "Что-то пошло не так. Попробуйте ещё раз или обратитесь в поддержку.",
            reply_markup=transcript_format_keyboard(),
        )
