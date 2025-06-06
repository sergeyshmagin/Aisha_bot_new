"""
Основной обработчик транскриптов
Рефакторинг app/handlers/transcript_processing.py (1007 строк → модули)
Объединяет AudioHandler, TextHandler, AIFormatter
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.handlers.state import TranscribeStates
from app.handlers.transcript_base import TranscriptBaseHandler
from app.keyboards.transcript import get_back_to_menu_keyboard, get_transcript_actions_keyboard

from .ai_formatter import AIFormatter
from .audio_handler import AudioHandler
from .text_handler import TextHandler

logger = logging.getLogger(__name__)


class TranscriptProcessingHandler(TranscriptBaseHandler):
    """
    Основной обработчик для обработки транскриптов.
    Объединяет модули: AudioHandler, TextHandler, AIFormatter
    """

    def __init__(self):
        """Инициализация обработчика транскриптов"""
        super().__init__()
        self.router = Router()

        # Инициализируем модули
        self.audio_handler = AudioHandler(self.get_session)
        self.text_handler = TextHandler(self.get_session)
        self.ai_formatter = AIFormatter(self.get_session)

        logger.info("Инициализирован TranscriptProcessingHandler с модулями")

    async def register_handlers(self):
        """
        Регистрация обработчиков для:
        - Обработки аудио (AudioHandler)
        - Обработки текста (TextHandler)
        - AI форматирования (AIFormatter)
        - Действий с транскриптом
        """
        logger.info("Регистрация обработчиков транскриптов")

        # ВАЖНО: Специфичные обработчики должны быть зарегистрированы РАНЬШЕ универсальных!

        # Обработка текста (специфичная - только в состоянии waiting_text)
        self.router.message.register(
            self._handle_text_processing,
            F.document & F.document.mime_type.in_(["text/plain"]),
            StateFilter(TranscribeStates.waiting_text),
        )

        # Универсальные обработчики аудио (работают в любом состоянии)
        self.router.message.register(self._handle_audio_universal, F.audio)

        self.router.message.register(self._handle_audio_universal, F.voice)

        # Обработка аудио файлов, отправленных как документы
        self.router.message.register(self._handle_audio_document, F.document)

        # Обработчики callback'ов для AI форматирования
        self.router.callback_query.register(
            self._handle_transcript_format, F.data.startswith("transcript_format_")
        )

        # Обработчик действий с транскриптами (summary, todo, protocol)
        self.router.callback_query.register(
            self._handle_transcript_actions,
            F.data.startswith("transcript_summary_")
            | F.data.startswith("transcript_todo_")
            | F.data.startswith("transcript_protocol_"),
        )

        # Обработчик возврата к меню
        self.router.callback_query.register(
            self._handle_back_to_transcribe_menu, F.data == "transcribe_back_to_menu"
        )

    # Делегирование к модулям
    async def _handle_audio_universal(self, message: Message, state: FSMContext) -> None:
        """Делегирует обработку аудио к AudioHandler"""
        await self.audio_handler.handle_audio_universal(message, state)

    async def _handle_audio_document(self, message: Message, state: FSMContext) -> None:
        """Делегирует обработку аудио документов к AudioHandler"""
        await self.audio_handler.handle_audio_document(message, state)

    async def _handle_text_processing(self, message: Message, state: FSMContext) -> None:
        """Делегирует обработку текста к TextHandler"""
        await self.text_handler.handle_text_processing(message, state)

    async def _handle_transcript_actions(self, call: CallbackQuery, state: FSMContext) -> None:
        """Делегирует AI форматирование к AIFormatter"""
        await self.ai_formatter.handle_transcript_actions(call, state)

    async def _handle_transcript_format(self, call: CallbackQuery, state: FSMContext) -> None:
        """Делегирует форматирование к AIFormatter (legacy метод)"""
        await self.ai_formatter.handle_transcript_format(call, state)

    async def _handle_back_to_transcribe_menu(self, call: CallbackQuery, state: FSMContext) -> None:
        """Обработка возврата к меню транскриптов"""
        await call.answer()
        await state.set_state(TranscribeStates.waiting_text)

    # Общие методы для всех модулей
    async def render_transcript_card(self, transcript: dict, telegram_id: int) -> str:
        """
        Формирует текст карточки транскрипта для отправки пользователю
        с учетом часового пояса пользователя.
        """
        # Извлекаем имя файла из метаданных
        metadata = transcript.get("metadata", {})
        file_name = metadata.get("file_name", "Файл")

        # Обрабатываем дату создания с учетом часового пояса
        created_at = transcript.get("created_at")
        async with self.get_session() as session:
            from app.core.di import get_timezone_handler_with_session

            tz_handler = get_timezone_handler_with_session(session)
            created_at_str = await tz_handler.format_metadata_date(
                {"created_at": created_at}, telegram_id
            )

        # Определяем тип транскрипта (как в старом коде)
        source = metadata.get("source", "unknown")
        transcript_type = "Аудио" if source in ["audio", "voice"] else "Текст"

        # Подсчитываем количество слов
        word_count = metadata.get("word_count")
        if not word_count:
            text = transcript.get("text") or transcript.get("preview")
            if text:
                word_count = len(text.split())
            else:
                word_count = "—"

        # Формируем превью текста (как в старом коде)
        text_preview = transcript.get("preview")
        if not text_preview:
            text = transcript.get("text")
            if text:
                text_preview = text[:200] + "..." if len(text) > 200 else text
            else:
                text_preview = "—"

        # Формируем карточку в HTML формате (как в старом коде)
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
        self, message: Message, transcript: Dict[str, Any], status_message: Optional[Message] = None
    ) -> None:
        """
        Отправляет результат транскрипта пользователю с клавиатурой действий.

        Args:
            message: Сообщение для ответа
            transcript: Данные транскрипта
            status_message: Сообщение статуса для удаления (опционально)
        """
        try:
            # Удаляем сообщение о статусе если есть
            if status_message:
                try:
                    await status_message.delete()
                except Exception:
                    pass  # Игнорируем ошибки удаления

            # Получаем содержимое транскрипта из БД
            async with self.get_session() as session:
                from app.core.di import get_transcript_service, get_user_service_with_session
                from app.utils.uuid_utils import safe_uuid

                transcript_service = get_transcript_service(session)
                user_service = get_user_service_with_session(session)
                user = await user_service.get_user_by_telegram_id(message.from_user.id)

                if not user:
                    await message.reply("❌ Ошибка: пользователь не найден")
                    return

                # Получаем содержимое транскрипта
                transcript_id = safe_uuid(transcript.get("id"))
                if not transcript_id:
                    await message.reply("❌ Ошибка: неверный ID транскрипта")
                    return

                content = await transcript_service.get_transcript_content(user.id, transcript_id)
                if not content:
                    await message.reply("❌ Не удалось получить содержимое транскрипта")
                    return

                try:
                    text = content.decode("utf-8")
                    # Добавляем текст и превью в transcript для карточки
                    transcript["text"] = text
                    transcript["preview"] = text[:300] + "..." if len(text) > 300 else text
                except UnicodeDecodeError as e:
                    logger.warning(f"Ошибка декодирования текста транскрипта: {e}")
                    await message.reply("❌ Ошибка при декодировании транскрипта")
                    return

            # Формируем карточку транскрипта (теперь с превью)
            card_text = await self.render_transcript_card(transcript, message.from_user.id)

            # Получаем ID транскрипта для клавиатуры
            transcript_id_str = str(transcript.get("id"))

            # Формируем клавиатуру с действиями
            keyboard = get_transcript_actions_keyboard(transcript_id_str)

            # Формируем имя файла для отправки
            metadata = transcript.get("metadata", {})
            original_file_name = metadata.get("file_name", "transcript")

            # Создаем имя файла .txt
            if original_file_name.endswith((".ogg", ".mp3", ".wav", ".m4a", ".aac")):
                # Заменяем расширение аудио на .txt
                file_name = original_file_name.rsplit(".", 1)[0] + ".txt"
            elif not original_file_name.endswith(".txt"):
                file_name = original_file_name + ".txt"
            else:
                file_name = original_file_name

            # Отправляем файл с карточкой как caption
            from aiogram.types import BufferedInputFile

            input_file = BufferedInputFile(content, filename=file_name)

            await message.answer_document(
                document=input_file, caption=card_text, reply_markup=keyboard, parse_mode="HTML"
            )

            logger.info(f"Отправлен транскрипт с файлом: {transcript_id_str}, файл: {file_name}")

        except Exception as e:
            logger.exception(f"Ошибка при отправке результата транскрипта: {e}")
            await message.answer(
                "✅ Транскрипт готов, но произошла ошибка при отображении.\n"
                "Проверьте историю транскриптов.",
                reply_markup=get_back_to_menu_keyboard(),
            )
