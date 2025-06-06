"""
Клавиатуры для работы с транскриптами.
"""
from typing import Dict, List
from uuid import UUID
from datetime import datetime
import logging

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.utils.timezone import TimezoneUtils
from app.utils.uuid_utils import safe_uuid
from app.utils.datetime_utils import format_datetime_for_user


def get_transcript_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура меню транскрибации
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎤 Аудио", callback_data="transcribe_audio"),
        InlineKeyboardButton(text="📝 Текст", callback_data="transcribe_text")
    )
    builder.row(
        InlineKeyboardButton(text="📜 История", callback_data="transcribe_history")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")
    )
    return builder.as_markup()


async def get_transcripts_keyboard(transcripts: List[Dict], telegram_id: int) -> InlineKeyboardMarkup:
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
        # Получаем created_at и форматируем с учетом часового пояса пользователя
        created_at = transcript.get("created_at")
        date_str = await format_datetime_for_user(created_at, telegram_id)
        
        source = transcript["metadata"].get("source", "unknown") if transcript.get("metadata") else "unknown"
        label = f"{'🎤' if source == 'audio' else '📄'} {date_str}"
        
        # Безопасно преобразуем UUID
        uuid_obj = safe_uuid(transcript['id'])
        if not uuid_obj:
            logging.error(f"Invalid UUID in transcript: {transcript['id']}")
            continue
            
        builder.add(
            InlineKeyboardButton(
                text=label, callback_data=f"transcribe_view_{str(uuid_obj)}"
            )
        )
    
    builder.row(        InlineKeyboardButton(text="⬅️ Назад", callback_data="transcribe_back_to_menu")    )
    
    return builder.as_markup()


def get_format_keyboard(transcript_id: str | UUID) -> InlineKeyboardMarkup:
    """Клавиатура выбора формата обработки"""
    uuid_obj = safe_uuid(transcript_id)
    if not uuid_obj:
        raise ValueError(f"Invalid UUID: {transcript_id}")
    transcript_id_str = str(uuid_obj)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📝 Краткое содержание",
            callback_data=f"transcribe_format_{transcript_id_str}_summary",
        ),
        InlineKeyboardButton(
            text="✅ Список задач",
            callback_data=f"transcribe_format_{transcript_id_str}_todo",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📊 Протокол",
            callback_data=f"transcribe_format_{transcript_id_str}_protocol",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад", callback_data="transcribe_back_to_menu"
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
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="transcribe_history"
        ),
        InlineKeyboardButton(
            text="🏠 В меню",
            callback_data="transcribe_back_to_menu"
        )
    )
    return builder.as_markup()


def get_back_to_transcript_keyboard(transcript_id: str | UUID) -> InlineKeyboardMarkup:
    """
    Клавиатура возврата в главное меню транскрипции
    
    Args:
        transcript_id: ID транскрипта (не используется, оставлен для совместимости)
        
    Returns:
        InlineKeyboardMarkup с кнопкой возврата в меню
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад в меню",
            callback_data="transcribe_back_to_menu"
        )
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
