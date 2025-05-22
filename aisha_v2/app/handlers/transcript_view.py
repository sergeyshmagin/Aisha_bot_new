"""
Обработчик для просмотра транскриптов.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from io import BytesIO

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from aisha_v2.app.handlers.transcript_base import TranscriptBaseHandler
from aisha_v2.app.utils.timezone import TimezoneUtils
from aisha_v2.app.keyboards.transcript import (
    get_back_to_transcript_keyboard,
    get_transcript_actions_keyboard,
    get_transcripts_keyboard,
    get_transcript_menu_keyboard,
)
from aisha_v2.app.core.di import (
    get_transcript_service,
    get_user_service,
)
from aisha_v2.app.utils.uuid_utils import safe_uuid

logger = logging.getLogger(__name__)

class TranscriptViewHandler(TranscriptBaseHandler):
    """
    Обработчик для просмотра транскриптов.
    Содержит методы для просмотра списка транскриптов и отдельных транскриптов.
    """
    
    def __init__(self):
        self.router = Router()

    async def register_handlers(self):
        """Регистрация обработчиков"""
        self.router.callback_query.register(
            self._handle_transcribe_menu,
            F.data == "transcribe_back_to_menu"
        )
        self.router.callback_query.register(
            self._handle_view_transcript,
            F.data.startswith("transcribe_view_")
        )

    async def _handle_transcribe_menu(self, call: CallbackQuery, state: FSMContext):
        """
        Обработка возврата в меню транскрибации
        """
        await call.message.delete()
        await call.message.answer(
            "🎙 <b>Транскрибация</b>\n\nВыберите действие:",
            parse_mode="HTML",
            reply_markup=get_transcript_menu_keyboard()
        )
    
    async def _view_transcript(self, call: CallbackQuery, state: FSMContext, telegram_id: int, transcript_id):
        """
        Просмотр транскрипта
        
        Args:
            call: CallbackQuery
            telegram_id: Telegram ID пользователя
            transcript_id: UUID транскрипта
        """
        async with self.get_session() as session:
            transcript_service = get_transcript_service(session)
            user_service = get_user_service(session)
            
            # Получаем пользователя по Telegram ID
            user = await user_service.get_user_by_telegram_id(telegram_id)
            if not user:
                await call.answer("Ошибка: пользователь не найден", show_alert=True)
                return
            
            # Получаем транскрипт
            transcript = await transcript_service.get_transcript(user.id, transcript_id)
            if not transcript:
                await call.answer("Ошибка: транскрипт не найден", show_alert=True)
                return
            
            # Получаем содержимое транскрипта
            content = await transcript_service.get_transcript_content(user.id, transcript_id)
            if not content:
                await call.answer("Ошибка: не удалось получить содержимое", show_alert=True)
                return
            
            # Декодируем содержимое
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    text = content.decode("cp1251")
                except UnicodeDecodeError:
                    await call.answer("Ошибка при декодировании файла", show_alert=True)
                    return
            
            # Получаем текущее состояние пользователя
            user_state = await user_service.get_user_state(user.id)
            
            # Получаем дату создания транскрипта
            created_at = transcript.get("created_at")
            date_str = ""
            try:
                if isinstance(created_at, str):
                    try:
                        dt = datetime.fromisoformat(created_at)
                        date_str = dt.strftime('%Y-%m-%d_%H-%M')
                    except ValueError:
                        date_str = datetime.now().strftime('%Y-%m-%d_%H-%M')
                elif hasattr(created_at, 'strftime'):
                    date_str = created_at.strftime('%Y-%m-%d_%H-%M')
                else:
                    date_str = datetime.now().strftime('%Y-%m-%d_%H-%M')
            except Exception as e:
                date_str = datetime.now().strftime('%Y-%m-%d_%H-%M')
                logger.debug(f"Error processing date: {e}, using current date")
            
            # Получаем метаданные
            metadata = transcript.get("metadata", {})
            source = metadata.get("source", "text")
            filename = metadata.get("filename", "")
            duration = metadata.get("duration", "")
            
            # Форматируем дату для отображения с учетом часового пояса пользователя
            display_date = ''
            try:
                user_timezone = "UTC+5"
                if user and hasattr(user, 'timezone') and user.timezone:
                    user_timezone = user.timezone
                if isinstance(created_at, datetime) or isinstance(created_at, str):
                    display_date = TimezoneUtils.format_date_with_timezone(
                        created_at, user_timezone, "%d.%m.%Y %H:%M"
                    )
                else:
                    display_date = date_str.replace('_', ' ')
            except Exception as e:
                logger.error(f"Error formatting date with timezone: {e}")
                display_date = date_str.replace('_', ' ')
            
            # Формируем имя файла для отправки
            file_prefix = "audio" if source == "audio" else "text"
            file_name = f"{file_prefix}_{date_str}.txt"
            
            # Подготавливаем информативное сообщение
            word_count = len(text.split()) if text else 0
            duration_str = f"{duration} сек." if duration else ""
            
            # Удаляем предыдущие сообщения, если они есть
            if user_state and user_state.get("message_id") and user_state.get("message_id") != call.message.message_id:
                try:
                    await call.message.bot.delete_message(
                        chat_id=call.message.chat.id,
                        message_id=user_state["message_id"]
                    )
                except Exception as e:
                    logger.error(f"Error deleting previous message: {e}")
            
            # Удаляем текущее сообщение
            await call.message.delete()
            
            # Отправляем файл с транскриптом
            caption = f"📝 Транскрипт\n\n"
            if source == "audio":
                caption += f"🎤 Аудиофайл: {filename if filename else 'Неизвестно'}\n"
                if duration_str:
                    caption += f"⏱ Длительность: {duration_str}\n"
            else:
                caption += f"📄 Текстовый файл: {filename if filename else 'Неизвестно'}\n"
            caption += f"📊 Количество слов: {word_count}\n"
            caption += f"🕒 Дата создания: {display_date}\n"
            file = BytesIO(text.encode('utf-8'))
            file.name = file_name
            sent_message = await call.message.answer_document(
                document=file,
                caption=caption,
                reply_markup=get_transcript_actions_keyboard(str(transcript_id))
            )
            
            # Сохраняем ID сообщения в состоянии пользователя
            await user_service.set_user_state(user.id, {
                "state": "view_transcript",
                "message_id": sent_message.message_id,
                "transcript_id": str(transcript_id)
            })
    
    async def _handle_view_transcript(self, call: CallbackQuery, state: FSMContext):
        """
        Обработка просмотра транскрипта
        """
        try:
            transcript_id = safe_uuid(call.data.replace("transcribe_view_", "").strip())
            if not transcript_id:
                await call.answer("Ошибка: неверный формат ID транскрипта", show_alert=True)
                return
            await self._view_transcript(call, state, call.from_user.id, transcript_id)
        except ValueError as e:
            logger.error(f"Error parsing UUID: {e}")
            await call.answer("Ошибка: неверный формат ID транскрипта", show_alert=True)
