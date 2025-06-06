"""
Просмотр транскриптов
Выделено из app/handlers/transcript_main.py для соблюдения правила ≤500 строк
"""

import logging
from typing import Any, Dict, Optional, Union
from uuid import UUID

from aiogram.types import CallbackQuery, Message

from app.core.di import get_transcript_service
from app.keyboards.transcript import get_transcript_actions_keyboard
from app.utils.uuid_utils import safe_uuid

from .models import TranscriptMainConfig

logger = logging.getLogger(__name__)


class TranscriptViewer:
    """
    Просмотрщик транскриптов

    Отвечает за:
    - Получение транскриптов по ID
    - Загрузку содержимого транскриптов
    - Рендеринг карточек транскриптов
    - Отправку карточек пользователю
    """

    def __init__(self, get_session_func):
        """
        Инициализация просмотрщика транскриптов

        Args:
            get_session_func: Функция получения сессии БД
        """
        self.get_session = get_session_func
        self.config = TranscriptMainConfig()

    async def get_transcript_with_content(
        self, user_id: str, transcript_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Получает транскрипт с содержимым

        Args:
            user_id: ID пользователя
            transcript_id: ID транскрипта

        Returns:
            Данные транскрипта с preview или None
        """
        try:
            async with self.get_session() as session:
                transcript_service = get_transcript_service(session)

                # Получаем метаданные транскрипта
                transcript = await transcript_service.get_transcript(user_id, transcript_id)
                if not transcript:
                    logger.warning(
                        f"Транскрипт {transcript_id} не найден для пользователя {user_id}"
                    )
                    return None

                # Получаем содержимое для preview
                content = await transcript_service.get_transcript_content(user_id, transcript_id)
                if content:
                    try:
                        text = content.decode("utf-8")
                        if text:
                            # Добавляем preview в данные транскрипта
                            transcript["preview"] = text[: self.config.PREVIEW_LENGTH]
                            logger.debug(f"Добавлен preview для транскрипта {transcript_id}")
                    except Exception as decode_error:
                        logger.warning(
                            f"Не удалось декодировать содержимое транскрипта {transcript_id}: {decode_error}"
                        )

                return transcript

        except Exception as e:
            logger.error(
                f"Ошибка при получении транскрипта {transcript_id} для пользователя {user_id}: {e}"
            )
            return None

    async def render_transcript_card(self, transcript: Dict[str, Any], telegram_id: int) -> str:
        """Рендерит карточку транскрипта для отображения с учетом часового пояса"""
        try:
            # Используем функцию рендера из processing handler для единообразия
            from app.handlers.transcript_processing import TranscriptProcessingHandler

            handler = TranscriptProcessingHandler()
            return await handler.render_transcript_card(transcript, telegram_id)
        except Exception as e:
            logger.error(f"Ошибка при рендеринге карточки транскрипта: {e}")
            # Fallback к простому отображению
            return self._render_simple_card(transcript)

    def _render_simple_card(self, transcript: Dict[str, Any]) -> str:
        """
        Простой рендер карточки транскрипта (fallback)

        Args:
            transcript: Данные транскрипта

        Returns:
            Простой текст карточки
        """
        metadata = transcript.get("metadata", {})
        source = metadata.get("source", "unknown")
        created_at = transcript.get("created_at", "")

        # Определяем тип
        type_icon = "🎵" if source == "audio" else "📝"
        type_name = "Аудио" if source == "audio" else "Текст"

        # Формируем карточку
        card_lines = [
            f"📄 <b>Транскрипт</b>",
            f"🔹 Тип: {type_icon} {type_name}",
            f"📅 Создан: {created_at[:16] if created_at else '—'}",
        ]

        # Добавляем preview если есть
        preview = transcript.get("preview")
        if preview:
            card_lines.extend(
                ["", "<b>Содержимое:</b>", preview[:200] + ("..." if len(preview) > 200 else "")]
            )

        return "\n".join(card_lines)

    async def open_transcript_by_callback(self, call: CallbackQuery, user_id: str) -> bool:
        """
        Открывает транскрипт по callback-запросу

        Args:
            call: Callback-запрос
            user_id: ID пользователя (UUID строка)

        Returns:
            True если транскрипт успешно открыт, False иначе
        """
        try:
            # Извлекаем ID транскрипта из callback_data
            transcript_id = safe_uuid(call.data.replace("transcribe_open_", "").strip())
            if not transcript_id:
                await call.answer("❌ Неверный ID транскрипта", show_alert=True)
                return False

            # Получаем транскрипт с содержимым
            transcript = await self.get_transcript_with_content(user_id, transcript_id)
            if not transcript:
                await call.answer("❌ Транскрипт не найден", show_alert=True)
                return False

            # Рендерим карточку (используем telegram_id из call)
            telegram_id = call.from_user.id
            card_text = await self.render_transcript_card(transcript, telegram_id)
            keyboard = get_transcript_actions_keyboard(str(transcript["id"]))

            # Отправляем карточку
            await self._send_transcript_card(call, card_text, keyboard)

            logger.info(f"Транскрипт {transcript_id} успешно открыт для пользователя {user_id}")
            return True

        except Exception as e:
            logger.error(
                f"Ошибка при открытии транскрипта (callback) для пользователя {user_id}: {e}"
            )
            await call.answer("Ошибка при открытии транскрипта", show_alert=True)
            return False

    async def open_transcript_by_command(self, message: Message, user_id: str) -> bool:
        """
        Открывает транскрипт по команде /open_{id}

        Args:
            message: Сообщение с командой
            user_id: ID пользователя (UUID строка)

        Returns:
            True если транскрипт успешно открыт, False иначе
        """
        try:
            # Парсим ID из команды
            parts = message.text.strip().split("_", 1)
            if len(parts) != 2 or not parts[1]:
                await message.answer("❌ Неверная команда. Пример: /open_<id>")
                return False

            transcript_id = safe_uuid(parts[1])
            if not transcript_id:
                await message.answer("❌ Неверный ID транскрипта")
                return False

            # Получаем транскрипт с содержимым
            transcript = await self.get_transcript_with_content(user_id, transcript_id)
            if not transcript:
                await message.answer("❌ Транскрипт не найден")
                return False

            # Рендерим карточку (используем telegram_id из message)
            telegram_id = message.from_user.id
            card_text = await self.render_transcript_card(transcript, telegram_id)
            keyboard = get_transcript_actions_keyboard(str(transcript["id"]))

            # Отправляем карточку
            await message.answer(card_text, reply_markup=keyboard, parse_mode="HTML")

            logger.info(
                f"Транскрипт {transcript_id} успешно открыт по команде для пользователя {user_id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Ошибка при открытии транскрипта (команда) для пользователя {user_id}: {e}"
            )
            await message.answer("Произошла ошибка при открытии транскрипта.")
            return False

    async def _send_transcript_card(self, call: CallbackQuery, card_text: str, keyboard) -> None:
        """
        Отправляет карточку транскрипта

        Args:
            call: Callback-запрос
            card_text: Текст карточки
            keyboard: Клавиатура
        """
        try:
            # Проверяем, можно ли редактировать сообщение (есть ли в нем текст)
            if call.message.text:
                try:
                    await call.message.edit_text(
                        card_text, reply_markup=keyboard, parse_mode="HTML"
                    )
                    return
                except Exception as edit_error:
                    logger.warning(f"Не удалось отредактировать сообщение: {edit_error}")
                    # Если не удалось отредактировать, отправляем новое сообщение
                    await call.message.answer(card_text, reply_markup=keyboard, parse_mode="HTML")
            else:
                # Если сообщение содержит документ или другой контент, отправляем новое
                await call.message.answer(card_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при отправке карточки транскрипта: {e}")
            raise
