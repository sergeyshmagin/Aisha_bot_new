"""
Клавиатуры для работы с транскриптами.
"""
from typing import Dict, List
from uuid import UUID
from datetime import datetime
import logging

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aisha_v2.app.utils.timezone import TimezoneUtils
from aisha_v2.app.utils.uuid_utils import safe_uuid


def get_transcript_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура меню транскрибации
    """
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="🎤 Аудио", callback_data="transcribe_audio"),
        InlineKeyboardButton(text="📝 Текст", callback_data="transcribe_text")
    )
    keyboard.row(
        InlineKeyboardButton(text="📜 История", callback_data="transcribe_history")
    )
    keyboard.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="transcribe_back_to_menu")
    )
    return keyboard


def get_transcripts_keyboard(transcripts: List[Dict], telegram_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура списка транскриптов
    
    Args:
        transcripts: Список транскриптов
        telegram_id: Telegram ID пользователя
        
    Returns:
        Клавиатура с транскриптами
    """
    builder = InlineKeyboardBuilder()
    
    for transcript in transcripts:
        # Получаем created_at
        created_at = transcript.get("created_at")
        
        # Форматируем дату для отображения
        date_str = "неизвестно"
        try:
            # Используем простое форматирование даты
            if isinstance(created_at, int):
                # Если это timestamp (целое число), преобразуем в datetime
                dt = datetime.fromtimestamp(created_at)
                date_str = dt.strftime("%d.%m.%Y %H:%M")
            elif isinstance(created_at, datetime):
                # Если это datetime
                date_str = created_at.strftime("%d.%m.%Y %H:%M")
            elif isinstance(created_at, str):
                # Если это строка, пробуем преобразовать в datetime
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_str = dt.strftime("%d.%m.%Y %H:%M")
                except ValueError:
                    date_str = created_at
            else:
                # В остальных случаях используем строковое представление
                date_str = str(created_at) if created_at is not None else "неизвестно"
        except Exception as e:
            logging.error(f"Error formatting date in get_transcripts_keyboard: {e}, type: {type(created_at)}, value: {created_at}")
            date_str = str(created_at) if created_at is not None else "неизвестно"
        
        source = transcript["metadata"].get("source", "unknown") if transcript.get("metadata") else "unknown"
        label = f"{'🎤' if source == 'audio' else '📄'} {date_str}"
        
        # Безопасно преобразуем UUID
        uuid_obj = safe_uuid(transcript['id'])
        if not uuid_obj:
            logging.error(f"Invalid UUID in transcript: {transcript['id']}")
            continue
            
        builder.add(
            InlineKeyboardButton(
                label, callback_data=f"transcribe_view_{str(uuid_obj)}"
            )
        )
    
    builder.row(
        InlineKeyboardButton("⬅️ Назад", callback_data="transcribe_back_to_menu")
    )
    
    return builder.as_markup()


def get_format_keyboard(transcript_id: str | UUID) -> InlineKeyboardMarkup:
    """Клавиатура выбора формата обработки"""
    # Безопасно преобразуем в UUID и обратно в строку
    uuid_obj = safe_uuid(transcript_id)
    if not uuid_obj:
        raise ValueError(f"Invalid UUID: {transcript_id}")
    transcript_id_str = str(uuid_obj)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            "📝 Краткое содержание",
            callback_data=f"transcribe_format_{transcript_id_str}_summary",
        ),
        InlineKeyboardButton(
            "✅ Список задач",
            callback_data=f"transcribe_format_{transcript_id_str}_todo",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            "📊 Протокол",
            callback_data=f"transcribe_format_{transcript_id_str}_protocol",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            "⬅️ Назад", callback_data="transcribe_back_to_menu"
        )
    )
    return builder.as_markup()


def get_transcript_actions_keyboard(transcript_id: str | UUID) -> InlineKeyboardMarkup:
    """
    Клавиатура действий с транскриптом
    
    Args:
        transcript_id: ID транскрипта (строка или UUID)
        
    Returns:
        InlineKeyboardMarkup с кнопками действий
    """
    # Безопасно преобразуем в UUID и обратно в строку
    uuid_obj = safe_uuid(transcript_id)
    if not uuid_obj:
        raise ValueError(f"Invalid UUID: {transcript_id}")
    transcript_id_str = str(uuid_obj)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📝 Краткое содержание",
            callback_data=f"transcript_summary_{transcript_id_str}"
        ),
        InlineKeyboardButton(
            text="✅ Список задач",
            callback_data=f"transcript_todo_{transcript_id_str}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📊 Протокол",
            callback_data=f"transcript_protocol_{transcript_id_str}"
        ),
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"transcript_back_{transcript_id_str}"
        )
    )
    return builder.as_markup()


def get_back_to_transcript_keyboard(transcript_id: str | UUID) -> InlineKeyboardMarkup:
    """
    Клавиатура для возврата к транскрипту
    """
    # Безопасно преобразуем в UUID и обратно в строку
    uuid_obj = safe_uuid(transcript_id)
    if not uuid_obj:
        raise ValueError(f"Invalid UUID: {transcript_id}")
    transcript_id_str = str(uuid_obj)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ К транскрипту", callback_data=f"transcribe_back_to_transcript_{transcript_id_str}")
    )
    return builder.as_markup()


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для возврата в меню
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ Назад в меню", callback_data="transcribe_back_to_menu")
    )
    return builder.as_markup()
