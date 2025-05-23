"""
Обработчик для работы с транскриптами.
Содержит методы для обработки аудио, текста и форматирования транскриптов.
Интеграция с TranscriptService (MinIO + БД).
"""
import logging
from datetime import datetime
from typing import Dict, Optional, Any, Union
from io import BytesIO
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from uuid import UUID
from pydantic import BaseModel, Field

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

logger = logging.getLogger(__name__)

class TranscriptResult(BaseModel):
    """Модель результата транскрипта"""
    id: str = Field(..., description="Уникальный идентификатор транскрипта")
    transcript_key: str = Field(..., description="Ключ для доступа к транскрипту в хранилище")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные транскрипта")

class TranscriptProcessingHandler(TranscriptBaseHandler):
    """
    Обработчик для обработки транскриптов.
    Содержит методы для форматирования и обработки транскриптов.
    Интеграция с TranscriptService (MinIO + БД).
    """
    
    def __init__(self):
        """Инициализация обработчика транскриптов"""
        super().__init__()
        self.router = Router()
        logger.info("Инициализирован TranscriptProcessingHandler")

    async def register_handlers(self):
        """
        Регистрация обработчиков для:
        - Обработки аудио
        - Обработки текста
        - Форматирования транскрипта
        """
        logger.info("Регистрация обработчиков транскриптов")
        
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

    async def _handle_audio_processing(self, message: Message, state: FSMContext) -> None:
        """
        Обработка аудио и голосовых сообщений.
        
        Args:
            message: Входящее сообщение с аудио
            state: Контекст состояния FSM
        """
        logger.info(f"[AUDIO] Получено аудио/voice от user_id={message.from_user.id}, state={await state.get_state()}")
        try:
            processing_msg = await message.answer("🎵 Начинаю обработку аудио...")
            await state.set_state(TranscribeStates.processing)

            # Определяем тип аудио
            if message.audio:
                file_id = message.audio.file_id
                duration = message.audio.duration
            elif message.voice:
                file_id = message.voice.file_id
                duration = message.voice.duration
            else:
                await message.reply("❌ Не удалось определить тип аудиосообщения.")
                return

            # Получаем файл
            file = await message.bot.get_file(file_id)
            downloaded_file = await message.bot.download_file(file.file_path)

            # Обрабатываем аудио
            async with (await self.get_session()) as session:
                audio_service = get_audio_processing_service(session)
                result = await audio_service.process_audio(
                    audio_data=downloaded_file.getvalue(),
                    language="ru", 
                    save_original=True,
                    normalize=True,
                    remove_silence=True
                )
                
                if not result.success:
                    logger.error(f"[AUDIO] Ошибка транскрибации: {result.error}")
                    await message.reply("❌ Ошибка транскрибации аудио.")
                    return

                text = result.text
                logger.info(f"[AUDIO] Получен текст транскрипта, длина: {len(text)}")

                # Сохраняем транскрипт
                user_service = get_user_service(session)
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user:
                    logger.error(f"[AUDIO] Пользователь не найден: {message.from_user.id}")
                    await message.reply("❌ Ошибка: пользователь не найден")
                    return

                transcript_service = get_transcript_service(session)
                transcript = await transcript_service.save_transcript(
                    user_id=user.id,
                    audio_data=downloaded_file.getvalue(),
                    transcript_data=text.encode('utf-8'),
                    metadata={
                        "source": "audio",
                        "duration": duration,
                        "file_id": file_id
                    }
                )
                
                if not transcript or not transcript.get("transcript_key"):
                    logger.error(f"[AUDIO] Ошибка сохранения транскрипта: {transcript}")
                    await message.reply("❌ Ошибка при сохранении транскрипта")
                    return
                    
                logger.info(f"[AUDIO] Транскрипт сохранен: {transcript}")

                await self._send_transcript_result(message, transcript, processing_msg)
                await state.set_state(TranscribeStates.result)

        except Exception as e:
            logger.exception(f"[AUDIO] Ошибка при обработке аудио: {e}")
            await state.set_state(TranscribeStates.error)
            await message.reply(
                "❌ Произошла ошибка при обработке аудио.\n"
                "Пожалуйста, попробуйте еще раз.",
                reply_markup=get_back_to_menu_keyboard()
            )

    async def _handle_text_processing(self, message: Message, state: FSMContext) -> None:
        """
        Обработка текста из файла .txt
        
        Args:
            message: Входящее сообщение с текстовым файлом
            state: Контекст состояния FSM
        """
        logger.info(f"[TEXT] Получен файл от user_id={message.from_user.id}, state={await state.get_state()}")
        try:
            if not message.document or message.document.mime_type != "text/plain" or not message.document.file_name.endswith(".txt"):
                await message.reply(
                    "❌ Пожалуйста, отправьте файл в формате .txt",
                    reply_markup=get_back_to_menu_keyboard()
                )
                return

            processing_msg = await message.answer("📝 Обрабатываю текстовый файл...")
            await state.set_state(TranscribeStates.processing)

            file = await message.document.get_file()
            file_bytes = await message.bot.download_file(file.file_path)
            text = file_bytes.read().decode("utf-8")

            async with (await self.get_session()) as session:
                text_service = get_text_processing_service(session)
                processed_text = await text_service.process_text(text)
                
                transcript_service = get_transcript_service(session)
                user_service = get_user_service(session)
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                
                if not user:
                    logger.error(f"[TEXT] Пользователь не найден: {message.from_user.id}")
                    await message.reply("❌ Ошибка: пользователь не найден")
                    return

                transcript = await transcript_service.save_transcript(
                    user_id=user.id,
                    transcript_data=processed_text.encode('utf-8'),
                    metadata={
                        "source": "text",
                        "length": len(text)
                    }
                )
                
                await self._send_transcript_result(message, transcript, processing_msg)
                await state.set_state(TranscribeStates.result)

        except Exception as e:
            logger.exception(f"[TEXT] Ошибка при обработке текста: {e}")
            await state.set_state(TranscribeStates.error)
            await message.reply(
                "❌ Произошла ошибка при обработке текста.\nПожалуйста, попробуйте еще раз.",
                reply_markup=get_back_to_menu_keyboard()
            )

    async def _handle_format_transcript(self, call: CallbackQuery, state: FSMContext) -> None:
        """
        Обработка форматирования транскрипта
        
        Args:
            call: CallbackQuery с данными о форматировании
            state: Контекст состояния FSM
        """
        try:
            # Получаем данные из callback
            data = call.data.split("_")
            if len(data) < 4:
                await call.answer("❌ Неверный формат данных")
                return

            transcript_id = safe_uuid(data[2])
            if not transcript_id:
                await call.answer("❌ Неверный ID транскрипта")
                return

            format_type = data[3]
            await state.set_state(TranscribeStates.format_selection)

            async with (await self.get_session()) as session:
                # Получаем транскрипт
                transcript_service = get_transcript_service(session)
                user_service = get_user_service(session)
                user = await user_service.get_user_by_telegram_id(call.from_user.id)
                
                if not user:
                    logger.error(f"[FORMAT] Пользователь не найден: {call.from_user.id}")
                    await call.answer("❌ Ошибка: пользователь не найден")
                    return
                    
                content = await transcript_service.get_transcript_content(user.id, transcript_id)
                if not content:
                    logger.error(f"[FORMAT] Не удалось получить текст транскрипта: {transcript_id}")
                    await call.answer("❌ Ошибка: не удалось получить текст транскрипта")
                    return

                text = content.decode('utf-8')
                text_service = get_text_processing_service(session)
                
                # Форматируем текст
                if format_type == "summary":
                    formatted_text = await text_service.format_summary(text)
                elif format_type == "todo":
                    formatted_text = await text_service.format_todo(text)
                elif format_type == "protocol":
                    formatted_text = await text_service.format_protocol(text)
                else:
                    logger.error(f"[FORMAT] Неизвестный формат: {format_type}")
                    await call.answer("❌ Неизвестный формат")
                    return

                # Сохраняем отформатированный текст
                formatted_transcript = await transcript_service.save_transcript(
                    user_id=call.from_user.id,
                    transcript_data=formatted_text.encode('utf-8'),
                    metadata={
                        "source": "format",
                        "original_id": str(transcript_id),
                        "format_type": format_type
                    }
                )

                # Отправляем результат
                await self._send_transcript_result(call.message, formatted_transcript, None)
                await state.set_state(TranscribeStates.result)

        except Exception as e:
            logger.exception(f"[FORMAT] Ошибка при форматировании транскрипта: {e}")
            await state.set_state(TranscribeStates.error)
            await call.message.reply(
                "❌ Произошла ошибка при форматировании.\n"
                "Пожалуйста, попробуйте еще раз.",
                reply_markup=get_back_to_menu_keyboard()
            )

    async def _send_transcript_result(
        self, 
        message: Message, 
        transcript: Dict[str, Any], 
        status_message: Optional[Message] = None
    ) -> None:
        """
        Отправляет результат обработки транскрипта.
        
        Args:
            message: Сообщение для ответа
            transcript: Данные транскрипта
            status_message: Сообщение о статусе обработки
        """
        try:
            if status_message:
                await status_message.delete()
            
            # Создаем экземпляр TranscriptResult
            transcript_result = TranscriptResult(
                id=str(transcript["id"]),
                transcript_key=transcript["transcript_key"],
                metadata=transcript.get("metadata", {})
            )
            
            # Получаем клавиатуру с действиями
            keyboard = get_transcript_actions_keyboard(transcript_result.id)
            
            await message.answer(
                "✅ Транскрипт готов!",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.exception(f"[RESULT] Ошибка при отправке результата: {e}")
            await message.answer(
                "❌ Произошла ошибка при отправке результата",
                reply_markup=get_back_to_menu_keyboard()
            )
