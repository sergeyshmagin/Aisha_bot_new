"""
Обработчики для работы с историей транскрипций.
"""

import os
from telebot.types import Message
from frontend_bot.handlers.general import bot
from frontend_bot.services.history_service import HistoryService
from frontend_bot.keyboards.reply import history_keyboard
from frontend_bot.services.file_utils import async_remove, async_exists
from frontend_bot.utils.logger import get_logger
from typing import List, Dict, Any
from pathlib import Path
from frontend_bot.services.transcribe_service import delete_user_transcripts
from frontend_bot.services.transcript_service_context import transcript_service_context
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.config import AsyncSessionLocal
from frontend_bot.repositories.user_repository import UserRepository

logger = get_logger("transcribe_history")

STORAGE_DIR = os.getenv("STORAGE_DIR", "storage")
TRANSCRIPTS_DIR = os.path.join(STORAGE_DIR, "transcripts")

@bot.message_handler(commands=["history"])
async def show_history(message: Message):
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await bot.send_message(
                message.chat.id,
                "Пользователь не найден в базе данных.",
                reply_markup=history_keyboard(),
            )
            return
        uuid_user_id = user.id
        history_service = HistoryService(session)
        entries = await history_service.get_user_history(
            session,
            str(uuid_user_id),
            limit=10
        )
        
    if entries:
        msg = "Последние файлы:\n"
        for entry in reversed(entries):
            action_data = entry.action_data
            msg += f"\n📄 {action_data.get('filename', 'Неизвестно')} | {entry.action_type} | {action_data.get('type', 'Неизвестно')} | {entry.created_at}"
        await bot.send_message(
            message.chat.id,
            msg,
            reply_markup=history_keyboard(),
        )
    else:
        await bot.send_message(
            message.chat.id,
            "У вас нет обработанных файлов.",
            reply_markup=history_keyboard(),
        )


@bot.message_handler(func=lambda m: m.text == "🗑 Удалить мой файл")
async def delete_my_file(message: Message):
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await bot.send_message(
                message.chat.id,
                "Пользователь не найден в базе данных.",
                reply_markup=history_keyboard(),
            )
            return
        uuid_user_id = user.id
        async with transcript_service_context as transcript_service:
            transcript_path = await transcript_service.get_transcript_path(uuid_user_id)
            if transcript_path and await async_exists(transcript_path):
                await async_remove(transcript_path)
                await transcript_service.clear_transcript_cache(uuid_user_id)
                
                # Очищаем историю через HistoryService
                async with AsyncSessionLocal() as session:
                    history_service = HistoryService(session)
                    await history_service.clear_user_history(session, str(uuid_user_id))
                    
                await delete_user_transcripts(str(uuid_user_id), STORAGE_DIR)
                await bot.send_message(
                    message.chat.id,
                    "Ваш последний файл удалён.",
                    reply_markup=history_keyboard(),
                )
            else:
                await bot.send_message(
                    message.chat.id,
                    "Нет файла для удаления.",
                    reply_markup=history_keyboard(),
                )


async def get_history(user_id: str) -> List[Dict[str, Any]]:
    """Получает историю транскрипций пользователя."""
    async with AsyncSessionLocal() as session:
        history_service = HistoryService(session)
        entries = await history_service.get_user_history(session, user_id)
        return [
            {
                "id": entry.id,
                "action_type": entry.action_type,
                "action_data": entry.action_data,
                "created_at": entry.created_at.isoformat()
            }
            for entry in entries
        ]


async def clear_history(user_id: str) -> None:
    """Очищает историю транскрипций пользователя."""
    async with AsyncSessionLocal() as session:
        history_service = HistoryService(session)
        await history_service.clear_user_history(session, user_id)


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Показывает историю транскрипций пользователя.
    """
    try:
        telegram_id = update.effective_user.id
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                await update.message.reply_text("Пользователь не найден в базе данных.")
                return
            uuid_user_id = user.id
            history_service = HistoryService(session)
            entries = await history_service.get_user_history(
                session,
                str(uuid_user_id),
                limit=10
            )
        
        if not entries:
            await update.message.reply_text("У вас пока нет транскрипций.")
            return
            
        # Формируем сообщение с историей
        message = "📚 Ваши последние транскрипции:\n\n"
        for i, entry in enumerate(entries, 1):
            action_data = entry.action_data
            message += f"{i}. {action_data.get('filename', 'Неизвестно')} ({entry.action_type}) - {entry.created_at}\n"
            
        # Создаем клавиатуру с кнопками
        keyboard = [
            [
                InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear_history"),
                InlineKeyboardButton("📥 Экспорт", callback_data="export_history")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
        
    except Exception as e:
        logger.exception(f"[history_handler] Ошибка: {e}")
        await update.message.reply_text("❌ Произошла ошибка при получении истории")


async def clear_history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Очищает историю транскрипций пользователя.
    """
    try:
        telegram_id = update.effective_user.id
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_telegram_id(telegram_id)
            if not user:
                await update.message.reply_text("Пользователь не найден в базе данных.")
                return
            uuid_user_id = user.id
            
            # Очищаем историю через HistoryService
            async with AsyncSessionLocal() as session:
                history_service = HistoryService(session)
                await history_service.clear_user_history(session, str(uuid_user_id))
            
        await update.message.reply_text("✅ История транскрипций очищена")
        
    except Exception as e:
        logger.exception(f"[clear_history_handler] Ошибка: {e}")
        await update.message.reply_text("❌ Произошла ошибка при очистке истории")

# TODO: Перевести работу с транскриптами на MinIO/PostgreSQL
