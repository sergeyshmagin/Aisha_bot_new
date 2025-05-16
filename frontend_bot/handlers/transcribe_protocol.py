"""
Хендлеры для генерации протоколов, summary, MoM, ToDo по транскриптам.
"""

import os
import aiofiles
import io
from telebot.types import Message
from telebot.async_telebot import AsyncTeleBot
from frontend_bot.handlers.general import bot
from frontend_bot.services.gpt_assistant import format_transcript_with_gpt
from frontend_bot.keyboards.reply import transcript_format_keyboard
from frontend_bot.services.file_utils import async_remove, async_exists
from frontend_bot.services.word_generator import generate_protocol_word
from frontend_bot.services.history import add_history_entry, STORAGE_DIR
from frontend_bot.utils.logger import get_logger
from frontend_bot.GPT_Prompts.transcribe.prompts import (
    PROTOCOL_PROMPT,
    SHORT_SUMMARY_PROMPT,
    MOM_PROMPT,
    TODO_PROMPT,
    FULL_TRANSCRIPT_PROMPT,
)
from datetime import datetime
from frontend_bot.services import transcript_cache
from frontend_bot.services.transcript_utils import get_user_transcript_or_error, send_document_with_caption, send_transcript_error

generate_word_protocol = generate_protocol_word

logger = get_logger("transcribe_protocol")

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
TRANSCRIPTS_DIR = os.path.join(STORAGE_DIR, "transcripts")

@bot.message_handler(func=lambda m: m.text == "Протокол заседания (Word)")
async def send_meeting_protocol(message: Message):
    logger.info(f"[HANDLER] send_meeting_protocol, message.text={message.text!r}")
    transcript = await get_user_transcript_or_error(bot, message, logger)
    if not transcript:
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
            f"protocol_{message.from_user.id}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.docx"
        )
        
        async with aiofiles.open(temp_filename, "rb") as f:
            data = await f.read()
            if not data:
                raise ValueError("что-то пошло не так")
            
            logger.info(f"[DEBUG] Sending file: {filename}, size: {len(data)} bytes")
            await send_document_with_caption(bot, message.chat.id, filename, data, "📄 Протокол заседания (Word)", transcript_format_keyboard())
        
        await async_remove(temp_filename)
        await add_history_entry(str(message.from_user.id), temp_filename, "word")
        
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
        await send_transcript_error(bot, message, error_msg, transcript_format_keyboard())


@bot.message_handler(func=lambda m: m.text == "Повторить генерацию протокола")
async def retry_meeting_protocol(message: Message):
    await send_meeting_protocol(message)


@bot.message_handler(func=lambda m: m.text == "Сводка на 1 страницу")
async def send_short_summary(message: Message):
    logger.info(f"[HANDLER] send_short_summary, message.text={message.text!r}")
    logger.info(f"[DEBUG] User ID: {message.from_user.id}")
    transcript = await get_user_transcript_or_error(bot, message, logger)
    logger.info(f"[DEBUG] transcript: {transcript[:100] if transcript else transcript}")
    if not transcript:
        logger.info("[DEBUG] transcript is None, return")
        return
    await bot.send_chat_action(message.chat.id, "typing")
    await bot.send_message(
        message.chat.id, "🤖 Формирую сводку на 1 страницу с помощью GPT..."
    )
    try:
        summary = await format_transcript_with_gpt(
            transcript, custom_prompt=SHORT_SUMMARY_PROMPT, temperature=0.3, top_p=0.7
        )
        logger.info(f"[DEBUG] summary: {summary[:100] if summary else summary}")
        if not summary.strip():
            logger.info("[DEBUG] Отправляю сообщение: summary пустой")
            await send_transcript_error(bot, message, "что-то пошло не так", transcript_format_keyboard())
            return
        filename = f"summary_{message.from_user.id}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
        data = summary.encode("utf-8")
        logger.info(f"[DEBUG] Sending file: {filename}, size: {len(data)} bytes")
        await send_document_with_caption(bot, message.chat.id, filename, data, "📝 Сводка на 1 страницу", transcript_format_keyboard())
    except Exception as exc:
        logger.exception("Ошибка при формировании сводки")
        await send_transcript_error(bot, message, "Что-то пошло не так. Попробуйте ещё раз или обратитесь в поддержку.", transcript_format_keyboard())


@bot.message_handler(func=lambda m: m.text == "Сформировать MoM")
async def send_mom(message: Message) -> None:
    """
    Формирует Minutes of Meeting (MoM) из транскрипта и отправляет пользователю.
    
    Args:
        message: Сообщение от пользователя
    """
    logger.info(f"[HANDLER] send_mom, message.text={message.text!r}")
    
    try:
        # Получаем транскрипт
        transcript = await get_user_transcript_or_error(bot, message, logger)
        if not transcript:
            return
            
        await bot.send_chat_action(message.chat.id, "typing")
        await bot.send_message(
            message.chat.id, "🤖 Формирую MoM (Minutes of Meeting) с помощью GPT..."
        )
            
        # Форматируем транскрипт через GPT
        mom_text = await format_transcript_with_gpt(
            transcript, custom_prompt=MOM_PROMPT, temperature=0.2, top_p=0.6
        )
        if not mom_text:
            await bot.send_message(
                message.chat.id,
                "Не удалось сформировать протокол встречи. Пожалуйста, попробуйте позже.",
                reply_markup=transcript_format_keyboard(),
            )
            return
            
        # Создаем временный файл
        temp_file = f"mom_{message.from_user.id}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
        temp_path = os.path.join("storage", "temp", temp_file)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        # Сохраняем MoM во временный файл
        async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
            await f.write(mom_text)
            
        # Отправляем файл
        async with aiofiles.open(temp_path, "rb") as f:
            await bot.send_document(
                message.chat.id,
                (temp_file, f),
                caption="📋 Протокол встречи (MoM)",
                reply_markup=transcript_format_keyboard(),
            )
            
        # Удаляем временный файл
        try:
            os.remove(temp_path)
        except Exception as e:
            logger.error(f"Ошибка при удалении временного файла: {e}")
            
    except Exception as e:
        logger.exception(f"Ошибка при формировании MoM: {e}")
        await bot.send_message(
            message.chat.id,
            "Произошла ошибка при формировании протокола встречи. Пожалуйста, попробуйте позже.",
            reply_markup=transcript_format_keyboard(),
        )


@bot.message_handler(func=lambda m: m.text == "Сформировать ToDo-план с чеклистами")
async def send_todo_checklist(message: Message):
    logger.info(f"[HANDLER] send_todo_checklist, message.text={message.text!r}")
    transcript = await get_user_transcript_or_error(bot, message, logger)
    if not transcript:
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
        filename = f"todo_{message.from_user.id}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
        data = todo_text.encode("utf-8")
        logger.info(f"[DEBUG] Sending file: {filename}, size: {len(data)} bytes")
        await send_document_with_caption(bot, message.chat.id, filename, data, "📝 ToDo-план с чеклистами", transcript_format_keyboard())
    except Exception:
        logger.exception("Ошибка при формировании ToDo")
        await send_transcript_error(bot, message, "Что-то пошло не так. Попробуйте ещё раз или обратитесь в поддержку.", transcript_format_keyboard())


@bot.message_handler(func=lambda m: m.text == "Полный официальный транскрипт")
async def send_full_official_transcript(message: Message):
    logger.info(f"[HANDLER] send_full_official_transcript, message.text={message.text!r}")
    logger.info(f"[DEBUG] User ID: {message.from_user.id}")
    transcript = await get_user_transcript_or_error(bot, message, logger)
    logger.info(f"[DEBUG] transcript: {transcript[:100] if transcript else transcript}")
    if not transcript:
        logger.info("[DEBUG] transcript is None, return")
        return
    await bot.send_chat_action(message.chat.id, "typing")
    await bot.send_message(
        message.chat.id, "🤖 Формирую полный официальный транскрипт с помощью GPT..."
    )
    try:
        formatted = await format_transcript_with_gpt(
            transcript, custom_prompt=FULL_TRANSCRIPT_PROMPT, temperature=0.2, top_p=0.7
        )
        logger.info(f"[DEBUG] Sending full transcript, length: {len(formatted)}")
        filename = (
            f"full_transcript_{message.from_user.id}_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
        )
        data = formatted.encode("utf-8")
        await send_document_with_caption(bot, message.chat.id, filename, data, "📝 Полный официальный транскрипт", transcript_format_keyboard())
    except Exception:
        logger.exception("Ошибка при формировании полного транскрипта")
        await send_transcript_error(bot, message, "Что-то пошло не так. Попробуйте ещё раз или обратитесь в поддержку.", transcript_format_keyboard())

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
