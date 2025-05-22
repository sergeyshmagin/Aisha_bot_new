"""
Обработчик для работы с транскриптами.
"""
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter

from aisha_v2.app.core.config import settings
from aisha_v2.app.handlers.transcript_base import TranscriptBaseHandler
from aisha_v2.app.core.di import (
    get_audio_processing_service,
    get_text_processing_service,
    get_transcript_service,
    get_user_service,
)
from aisha_v2.app.keyboards.transcript import (
    get_transcript_actions_keyboard,
    get_back_to_transcript_keyboard,
    get_back_to_menu_keyboard,
)
from aisha_v2.app.utils.uuid_utils import safe_uuid
from aisha_v2.app.handlers.state import TranscribeStates
from aisha_v2.app.services.audio_processing.service import AudioService
from aisha_v2.app.services.audio_processing.factory import get_audio_service

logger = logging.getLogger(__name__)

class TranscriptProcessingHandler(TranscriptBaseHandler):
    """
    Обработчик для обработки транскриптов.
    Содержит методы для форматирования и обработки транскриптов.
    """
    
    def __init__(self):
        self.router = Router()

    async def register_handlers(self):
        """Регистрация обработчиков"""
        # Обработка аудио
        self.router.message.register(
            self._handle_audio_processing,
            F.audio,
            StateFilter(TranscribeStates.waiting_audio)
        )
        
        # Обработка текста
        self.router.message.register(
            self._handle_text_processing,
            F.text,
            StateFilter(TranscribeStates.waiting_text)
        )
        
        # Обработка форматирования транскрипта
        self.router.callback_query.register(
            self._handle_format_transcript,
            F.data.startswith("transcribe_format_")
        )

    async def _handle_audio_processing(self, message: Message, state: FSMContext):
        """Обработка аудио и голосовых сообщений"""
        logger.info(f"[AUDIO] Получено аудио/voice от user_id={message.from_user.id}, state={await state.get_state()}")
        try:
            processing_msg = await message.answer("🎵 Начинаю обработку аудио...")
            await state.set_state(TranscribeStates.processing)

            # Определяем тип файла
            if message.audio:
                file = await message.audio.get_file()
                duration = message.audio.duration
                file_id = message.audio.file_id
            elif message.voice:
                file = await message.voice.get_file()
                duration = message.voice.duration
                file_id = message.voice.file_id
            else:
                await message.reply("Не удалось определить тип аудиосообщения.")
                return
            downloaded_file = await message.bot.download_file(file.file_path)

            # Обрабатываем аудио
            async with self.get_session() as session:
                audio_service = get_audio_processing_service(session)
                text = await audio_service.transcribe_audio(downloaded_file)

                # Сохраняем транскрипт
                transcript_service = get_transcript_service(session)
                user_service = get_user_service(session)
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user:
                    await message.reply("❌ Ошибка: пользователь не найден")
                    return
                transcript = await transcript_service.create_transcript(
                    user_id=user.id,
                    text=text,
                    metadata={
                        "source": "audio",
                        "duration": duration,
                        "file_id": file_id
                    }
                )
                await self._send_transcript_result(message, transcript, processing_msg)
                await state.set_state(TranscribeStates.result)

        except Exception as e:
            logger.error(f"Ошибка при обработке аудио: {e}")
            await state.set_state(TranscribeStates.error)
            await message.reply(
                "❌ Произошла ошибка при обработке аудио.\n"
                "Пожалуйста, попробуйте еще раз.",
                reply_markup=get_back_to_menu_keyboard()
            )

    async def _handle_text_processing(self, message: Message, state: FSMContext):
        """Обработка текста"""
        logger.info(f"[TEXT] Получен текст от user_id={message.from_user.id}, state={await state.get_state()}, text={message.text[:100]}")
        try:
            # Отправляем статус
            processing_msg = await message.answer("📝 Обрабатываю текст...")
            await state.set_state(TranscribeStates.processing)

            # Обрабатываем текст
            async with self.get_session() as session:
                text_service = get_text_processing_service(session)
                processed_text = await text_service.process_text(message.text)

                # Сохраняем транскрипт
                transcript_service = get_transcript_service(session)
                user_service = get_user_service(session)
                
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user:
                    await message.reply("❌ Ошибка: пользователь не найден")
                    return

                transcript = await transcript_service.create_transcript(
                    user_id=user.id,
                    text=processed_text,
                    metadata={
                        "source": "text",
                        "length": len(message.text)
                    }
                )

                # Отправляем результат
                await self._send_transcript_result(message, transcript, processing_msg)
                await state.set_state(TranscribeStates.result)

        except Exception as e:
            logger.error(f"Ошибка при обработке текста: {e}")
            await state.set_state(TranscribeStates.error)
            await message.reply(
                "❌ Произошла ошибка при обработке текста.\n"
                "Пожалуйста, попробуйте еще раз.",
                reply_markup=get_back_to_menu_keyboard()
            )

    async def _handle_format_transcript(self, call: CallbackQuery, state: FSMContext):
        """Обработка форматирования транскрипта"""
        try:
            # Получаем данные из callback
            data = call.data.split("_")
            if len(data) < 4:
                await call.answer("Неверный формат данных")
                return

            transcript_id = safe_uuid(data[2])
            if not transcript_id:
                await call.answer("Неверный ID транскрипта")
                return

            format_type = data[3]
            await state.set_state(TranscribeStates.format_selection)

            # Получаем транскрипт
            async with self.get_session() as session:
                transcript_service = get_transcript_service(session)
                transcript = await transcript_service.get_transcript(transcript_id)
                
                if not transcript:
                    await call.answer("Транскрипт не найден")
                    return

                # Форматируем текст
                text_service = get_text_processing_service(session)
                formatted_text = await text_service.format_text(transcript.text, format_type)

                # Отправляем результат
                await call.message.edit_text(
                    f"📝 Форматированный текст:\n\n{formatted_text}",
                    reply_markup=get_back_to_transcript_keyboard(str(transcript_id))
                )
                await state.set_state(TranscribeStates.result)

        except Exception as e:
            logger.error(f"Ошибка при форматировании: {e}")
            await state.set_state(TranscribeStates.error)
            await call.answer("Произошла ошибка при форматировании")

    async def _send_transcript_result(self, message: Message, transcript: Dict, status_message: Message):
        """Отправка результата обработки транскрипта"""
        try:
            # Удаляем сообщение со статусом
            await status_message.delete()

            # Отправляем результат
            await message.reply(
                f"✅ Транскрипт успешно создан!\n\n"
                f"📝 Текст:\n{transcript['text'][:1000]}...\n\n"
                f"Выберите действие:",
                reply_markup=get_transcript_actions_keyboard(str(transcript['id']))
            )

        except Exception as e:
            logger.error(f"Ошибка при отправке результата: {e}")
            await message.reply(
                "❌ Произошла ошибка при отправке результата.\n"
                "Пожалуйста, попробуйте еще раз.",
                reply_markup=get_back_to_menu_keyboard()
            )

async def get_transcript_text(transcript_id: str) -> str:
    """
    Получает текст транскрипта по его ID из БД.
    """
    async with self.get_session() as session:
        transcript_service = get_transcript_service(session)
        transcript = await transcript_service.get_transcript(transcript_id)
        if not transcript:
            return ""
        return transcript.text

@router.callback_query(F.data.startswith("transcript_"))
async def process_transcript_format(call: CallbackQuery, state: FSMContext):
    """
    Универсальный хендлер для обработки кнопок формата транскрипта (summary, todo, protocol).
    """
    data = call.data.split("_")
    if len(data) < 3:
        await call.answer("Некорректный запрос", show_alert=True)
        return
    action, format_type, transcript_id = data[0], data[1], "_".join(data[2:])
    transcript_text = await get_transcript_text(transcript_id)
    audio_service = get_audio_service()
    if format_type == "summary":
        result_text = await audio_service.summarize_text(transcript_text)
        file_name = f"summary_{transcript_id}.txt"
        caption = "📝 <b>Краткое содержание</b>"
    elif format_type == "todo":
        result_text = await audio_service.create_bullet_points(transcript_text)
        file_name = f"todo_{transcript_id}.txt"
        caption = "✅ <b>Список задач</b>"
    elif format_type == "protocol":
        result_text = await audio_service.generate_protocol(transcript_text)
        file_name = f"protocol_{transcript_id}.txt"
        caption = "📊 <b>Протокол</b>"
    else:
        await call.answer("Неизвестный формат", show_alert=True)
        return
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(result_text)
    await call.message.answer_document(
        FSInputFile(file_name),
        caption=caption,
        reply_markup=get_transcript_actions_keyboard(transcript_id),
        parse_mode="HTML"
    )
