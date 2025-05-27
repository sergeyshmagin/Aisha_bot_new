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

from app.core.config import settings
from app.handlers.transcript_base import TranscriptBaseHandler
from app.core.di import (
    get_audio_processing_service,
    get_text_processing_service,
    get_transcript_service,
    get_user_service_with_session,
)
from app.keyboards.transcript import (
    get_transcript_actions_keyboard,
    get_back_to_transcript_keyboard,
    get_back_to_menu_keyboard,
)
from app.utils.uuid_utils import safe_uuid
from app.handlers.state import TranscribeStates

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
        - Действий с транскриптом
        """
        logger.info("Регистрация обработчиков транскриптов")
        
        # ВАЖНО: Специфичные обработчики должны быть зарегистрированы РАНЬШЕ универсальных!
        
        # Обработка текста (специфичная - только в состоянии waiting_text)
        self.router.message.register(
            self._handle_text_processing,
            F.document,
            StateFilter(TranscribeStates.waiting_text)
        )
        
        # Универсальные обработчики аудио (работают в любом состоянии)
        # Регистрируем ПОСЛЕ специфичных обработчиков
        self.router.message.register(
            self._handle_audio_universal,
            F.audio
        )
        
        self.router.message.register(
            self._handle_audio_universal,
            F.voice
        )
        
        # Специфичные обработчики callback'ов
        self.router.callback_query.register(
            self._handle_transcript_format,
            F.data.startswith("transcript_format_")
        )
        
        # Обработчик действий с транскриптами (summary, todo, protocol)
        self.router.callback_query.register(
            self._handle_transcript_actions,
            F.data.startswith("transcript_summary_") | 
            F.data.startswith("transcript_todo_") | 
            F.data.startswith("transcript_protocol_")
        )
        
        self.router.callback_query.register(
            self._handle_back_to_transcribe_menu,
            F.data == "transcribe_back_to_menu"
        )

    async def _handle_audio_universal(self, message: Message, state: FSMContext) -> None:
        """
        Универсальный обработчик аудио и голосовых сообщений.
        Работает в любом состоянии и автоматически начинает обработку.
        
        Args:
            message: Входящее сообщение с аудио
            state: Контекст состояния FSM
        """
        current_state = await state.get_state()
        logger.info(f"[AUDIO_UNIVERSAL] Получено аудио/voice от user_id={message.from_user.id}, current_state={current_state}")
        
        # Если уже в процессе обработки, пропускаем
        if current_state in [TranscribeStates.processing, TranscribeStates.result]:
            logger.info(f"[AUDIO_UNIVERSAL] Пользователь уже в процессе обработки, пропускаем")
            return
            
        # Начинаем обработку
        logger.info(f"[AUDIO_UNIVERSAL] Начинаем обработку аудио")
        
        # Выполняем обработку аудио напрямую
        try:
            processing_msg = await message.answer("🎵 Начинаю обработку аудио...")
            await state.set_state(TranscribeStates.processing)

            # Скачиваем файл
            if message.voice:
                file_id = message.voice.file_id
                duration = message.voice.duration
                file_name = f"voice_{message.message_id}.ogg"
                file_size = message.voice.file_size
            else:
                file_id = message.audio.file_id  
                duration = message.audio.duration
                file_name = message.audio.file_name or f"audio_{message.message_id}.mp3"
                file_size = message.audio.file_size
            
            # Проверяем размер файла (используем настройки из конфигурации)
            max_file_size = settings.MAX_AUDIO_SIZE  # 1GB
            telegram_api_limit = settings.TELEGRAM_API_LIMIT  # 20MB - лимит Telegram Bot API для get_file()
            
            if file_size and file_size > max_file_size:
                logger.warning(f"[AUDIO_UNIVERSAL] Файл слишком большой: {file_size} байт (лимит: {max_file_size})")
                await message.reply(
                    f"❌ **Файл слишком большой**\n\n"
                    f"Размер файла: {file_size / (1024*1024):.1f} МБ\n"
                    f"Максимальный размер: {max_file_size / (1024*1024*1024)} ГБ\n\n"
                    f"Пожалуйста, отправьте файл меньшего размера.",
                    parse_mode="Markdown"
                )
                await state.set_state(TranscribeStates.error)
                return
            
            # Скачиваем файл (обычный или большой)
            if file_size and file_size > telegram_api_limit:
                logger.info(f"[AUDIO_UNIVERSAL] Большой файл ({file_size} байт), используем прямую ссылку")
                
                # Обновляем сообщение о прогрессе
                await processing_msg.edit_text(
                    f"📁 **Большой файл обнаружен**\n\n"
                    f"Размер: {file_size / (1024*1024):.1f} МБ\n"
                    f"🔄 Скачиваем через прямую ссылку...",
                    parse_mode="Markdown"
                )
                
                # Для больших файлов (>20MB) Telegram Bot API не предоставляет file_path
                # Уведомляем пользователя об ограничении
                logger.warning(f"[AUDIO_UNIVERSAL] Файл слишком большой для обработки: {file_size} байт")
                
                await message.reply(
                    f"❌ **Файл слишком большой**\n\n"
                    f"📊 **Размер файла:** {file_size / (1024*1024):.1f} МБ\n"
                    f"📏 **Максимальный размер:** {telegram_api_limit / (1024*1024):.0f} МБ\n\n"
                    f"💡 **Рекомендации:**\n"
                    f"• Сожмите аудио файл\n"
                    f"• Разделите на части до 20 МБ\n"
                    f"• Используйте формат MP3 с низким битрейтом",
                    parse_mode="Markdown"
                )
                await state.set_state(TranscribeStates.error)
                return
                
            else:
                # Обычное скачивание для файлов <= 20MB
                file = await message.bot.get_file(file_id)
                downloaded_file = await message.bot.download_file(file.file_path)

            # Транскрибируем
            async with self.get_session() as session:
                audio_service = get_audio_processing_service(session)
                result = await audio_service.process_audio(downloaded_file.getvalue())
                
                if not result.success:
                    logger.error(f"[AUDIO_UNIVERSAL] Ошибка транскрибации: {result.error}")
                    await message.reply("❌ Ошибка транскрибации аудио.")
                    return
                
                text = result.text
                logger.info(f"[AUDIO_UNIVERSAL] Получен текст транскрипта, длина: {len(text)}")
                
                # Сохраняем транскрипт
                user_service = get_user_service_with_session(session)
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user:
                    # Автоматически регистрируем пользователя
                    user_data = {
                        "id": message.from_user.id,
                        "username": message.from_user.username,
                        "first_name": message.from_user.first_name,
                        "last_name": message.from_user.last_name,
                        "language_code": message.from_user.language_code or "ru",
                        "is_bot": message.from_user.is_bot,
                        "is_premium": getattr(message.from_user, "is_premium", False)
                    }
                    user = await user_service.register_user(user_data)
                    if not user:
                        logger.error(f"[AUDIO_UNIVERSAL] Не удалось зарегистрировать пользователя: {message.from_user.id}")
                        await message.reply("❌ Ошибка регистрации пользователя")
                        return

                transcript_service = get_transcript_service(session)
                transcript = await transcript_service.save_transcript(
                    user_id=user.id,
                    audio_data=downloaded_file.getvalue(),
                    transcript_data=text.encode('utf-8'),
                    metadata={
                        "source": "audio",
                        "duration": duration,
                        "file_id": file_id,
                        "file_name": file_name,
                        "word_count": len(text.split()) if text else 0
                    }
                )
                
                if not transcript or not transcript.get("transcript_key"):
                    logger.error(f"[AUDIO_UNIVERSAL] Ошибка сохранения транскрипта: {transcript}")
                    await message.reply("❌ Ошибка при сохранении транскрипта")
                    return
                    
                logger.info(f"[AUDIO_UNIVERSAL] Транскрипт сохранен: {transcript}")

                await self._send_transcript_result(message, transcript, processing_msg)
                await state.set_state(TranscribeStates.result)

        except Exception as e:
            logger.exception(f"[AUDIO_UNIVERSAL] Ошибка при обработке аудио: {e}")
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

            file = await message.bot.get_file(message.document.file_id)
            file_bytes_io = await message.bot.download_file(file.file_path)
            text = file_bytes_io.read().decode("utf-8")
            file_name = message.document.file_name

            async with self.get_session() as session:
                text_service = get_text_processing_service(session)
                processed_text = await text_service.process_text(text)
                
                transcript_service = get_transcript_service(session)
                user_service = get_user_service_with_session(session)
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                
                if not user:
                    # Автоматически регистрируем пользователя
                    user_data = {
                        "id": message.from_user.id,
                        "username": message.from_user.username,
                        "first_name": message.from_user.first_name,
                        "last_name": message.from_user.last_name,
                        "language_code": message.from_user.language_code or "ru",
                        "is_bot": message.from_user.is_bot,
                        "is_premium": getattr(message.from_user, "is_premium", False)
                    }
                    user = await user_service.register_user(user_data)
                    if not user:
                        logger.error(f"[TEXT] Не удалось зарегистрировать пользователя: {message.from_user.id}")
                        await message.reply("❌ Ошибка регистрации пользователя")
                        return

                transcript = await transcript_service.save_transcript(
                    user_id=user.id,
                    transcript_data=processed_text.encode('utf-8'),
                    metadata={
                        "source": "text",
                        "length": len(text),
                        "file_name": file_name,
                        "word_count": len(processed_text.split()) if processed_text else 0
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

            async with self.get_session() as session:
                # Получаем транскрипт
                transcript_service = get_transcript_service(session)
                user_service = get_user_service_with_session(session)
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

    def render_transcript_card(self, transcript: dict) -> str:
        """
        Формирует текст карточки транскрипта для отправки пользователю.
        """
        # Извлекаем имя файла из метаданных
        metadata = transcript.get("metadata", {})
        file_name = metadata.get("file_name", "Файл")
        
        # Обрабатываем дату создания
        created_at = transcript.get("created_at")
        if isinstance(created_at, str):
            created_at_str = created_at.replace('T', ' ')[:16]
        elif created_at:
            created_at_str = created_at.strftime("%Y-%m-%d %H:%M")
        else:
            created_at_str = "—"
        
        # Определяем тип транскрипта
        transcript_type = "Аудио" if metadata.get("source") == "audio" else "Текст"
        
        # Подсчитываем количество слов
        word_count = metadata.get("word_count")
        if not word_count:
            text = transcript.get("text") or transcript.get("preview")
            if text:
                word_count = len(text.split())
            else:
                word_count = "—"
        
        # Формируем превью текста
        text_preview = transcript.get("preview")
        if not text_preview:
            text = transcript.get("text")
            if text:
                text_preview = text[:200] + "..." if len(text) > 200 else text
            else:
                text_preview = "—"
        
        card = (
            f"<b>Транскрипт</b>\n"
            f"📎 Файл: {file_name}\n"
            f"📅 Создан: {created_at_str}\n"
            f"📝 Тип: {transcript_type}\n"
            f"📊 Слов: {word_count}\n\n"
            f"«{text_preview}»"
        )
        return card

    async def _send_transcript_result(
        self, 
        message: Message, 
        transcript: Dict[str, Any], 
        status_message: Optional[Message] = None
    ) -> None:
        """
        Отправляет результат обработки транскрипта с файлом.
        """
        try:
            if status_message:
                await status_message.delete()
            
            transcript_result = TranscriptResult(
                id=str(transcript["id"]),
                transcript_key=transcript["transcript_key"],
                metadata=transcript.get("metadata", {})
            )
            
            # Получаем текст транскрипта для preview и отправки файла
            async with self.get_session() as session:
                transcript_service = get_transcript_service(session)
                user_service = get_user_service_with_session(session)
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                
                if not user:
                    await message.reply("❌ Ошибка: пользователь не найден")
                    return
                    
                content = await transcript_service.get_transcript_content(user.id, safe_uuid(transcript["id"]))
                if not content:
                    await message.reply("❌ Не удалось получить содержимое транскрипта")
                    return
                
                try:
                    text = content.decode("utf-8")
                    transcript["preview"] = text[:300] + "..." if len(text) > 300 else text
                    transcript["text"] = text  # Полный текст для подсчета слов
                except Exception as e:
                    logger.warning(f"Ошибка декодирования текста транскрипта: {e}")
                    await message.reply("❌ Ошибка при декодировании транскрипта")
                    return
                
                # Формируем имя файла для отправки
                metadata = transcript.get("metadata", {})
                original_file_name = metadata.get("file_name")
                if original_file_name:
                    # Используем оригинальное имя файла
                    file_name = original_file_name
                    if not file_name.endswith('.txt'):
                        file_name += '.txt'
                else:
                    # Генерируем имя на основе даты и ID
                    created_at = transcript.get("created_at", "")
                    if isinstance(created_at, str):
                        date_part = created_at[:10]  # YYYY-MM-DD
                    else:
                        date_part = "unknown"
                    file_name = f"{date_part}_transcript_{transcript['id'][:8]}.txt"
                
                # Создаем файл для отправки с помощью BufferedInputFile
                from aiogram.types import BufferedInputFile
                input_file = BufferedInputFile(content, filename=file_name)
                
                # Формируем карточку транскрипта
                keyboard = get_transcript_actions_keyboard(transcript_result.id)
                card_text = self.render_transcript_card(transcript)
                
                # Отправляем файл с карточкой как caption
                await message.answer_document(
                    document=input_file,
                    caption=card_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                
        except Exception as e:
            logger.exception(f"[RESULT] Ошибка при отправке результата: {e}")
            await message.answer(
                "❌ Произошла ошибка при отправке результата",
                reply_markup=get_back_to_menu_keyboard()
            )

    async def _handle_transcript_actions(self, call: CallbackQuery, state: FSMContext) -> None:
        """
        Обработка действий с транскриптом: summary, todo, protocol
        """
        try:
            # Разбираем callback data: transcript_summary_<id>, transcript_todo_<id>, etc.
            parts = call.data.split("_", 2)
            if len(parts) < 3:
                await call.answer("❌ Неверный формат данных")
                return
            
            action = parts[1]  # summary, todo, protocol
            transcript_id = safe_uuid(parts[2])
            
            if not transcript_id:
                await call.answer("❌ Неверный ID транскрипта")
                return
            
            # Обработка форматирования через GPT
            await state.set_state(TranscribeStates.format_selection)
            # Отправляем новое сообщение вместо редактирования
            processing_msg = await call.message.answer("⏳ Обрабатываю транскрипт с помощью GPT...")

            async with self.get_session() as session:
                transcript_service = get_transcript_service(session)
                user_service = get_user_service_with_session(session)
                user = await user_service.get_user_by_telegram_id(call.from_user.id)
                
                if not user:
                    await call.answer("❌ Ошибка: пользователь не найден")
                    return
                    
                content = await transcript_service.get_transcript_content(user.id, transcript_id)
                if not content:
                    logger.error(f"[GPT] Не удалось получить текст транскрипта: {transcript_id}")
                    await processing_msg.edit_text("❌ Ошибка: не удалось получить текст транскрипта")
                    return

                text = content.decode('utf-8')
                text_service = get_text_processing_service(session)
                
                # Обрабатываем текст через GPT
                if action == "summary":
                    formatted_text = await text_service.format_summary(text)
                    format_name = "Краткое содержание"
                    file_prefix = "summary"
                elif action == "todo":
                    formatted_text = await text_service.format_todo(text)
                    format_name = "Список задач"
                    file_prefix = "todo"
                elif action == "protocol":
                    formatted_text = await text_service.format_protocol(text)
                    format_name = "Протокол"
                    file_prefix = "protocol"
                else:
                    logger.error(f"[GPT] Неизвестный формат: {action}")
                    await processing_msg.edit_text("❌ Неизвестный формат")
                    return

                # Отправляем результат как файл
                from aiogram.types import BufferedInputFile
                file_data = formatted_text.encode('utf-8')
                input_file = BufferedInputFile(file_data, filename=f"{file_prefix}_{transcript_id}.txt")
                
                await processing_msg.delete()
                await call.message.answer_document(
                    document=input_file,
                    caption=f"📄 {format_name}",
                    reply_markup=get_back_to_transcript_keyboard(transcript_id)
                )
                await state.set_state(TranscribeStates.result)

        except Exception as e:
            logger.exception(f"[ACTIONS] Ошибка при обработке действий транскрипта: {e}")
            await state.set_state(TranscribeStates.error)
            await call.message.answer(
                "❌ Произошла ошибка при обработке.\nПожалуйста, попробуйте еще раз.",
                reply_markup=get_back_to_menu_keyboard()
            )

    async def _handle_transcript_format(self, call: CallbackQuery, state: FSMContext) -> None:
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

            async with self.get_session() as session:
                # Получаем транскрипт
                transcript_service = get_transcript_service(session)
                user_service = get_user_service_with_session(session)
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

    async def _handle_back_to_transcribe_menu(self, call: CallbackQuery, state: FSMContext) -> None:
        """
        Обработка возврата к меню транскриптов
        """
        await call.answer()
        await state.set_state(TranscribeStates.waiting_text)
