"""
Обработчик для управления транскриптами.
"""
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from aisha_v2.app.utils.uuid_utils import safe_uuid

from aisha_v2.app.handlers.transcript_base import TranscriptBaseHandler
from aisha_v2.app.keyboards.transcript import get_transcript_menu_keyboard
from aisha_v2.app.core.di import (
    get_transcript_service,
    get_user_service,
)

logger = logging.getLogger(__name__)

class TranscriptManagementHandler(TranscriptBaseHandler):
    """
    Обработчик для управления транскриптами.
    Содержит методы для удаления и управления транскриптами.
    """
    
    def __init__(self):
        self.router = Router()

    async def register_handlers(self):
        """Регистрация обработчиков"""
        self.router.callback_query.register(
            self._delete_transcript,
            F.data.startswith("transcribe_delete_")
        )

    async def _delete_transcript(self, call: CallbackQuery, state: FSMContext):
        """
        Удаление транскрипта
        
        Args:
            call: CallbackQuery
            state: FSMContext
        """
        try:
            transcript_id = safe_uuid(call.data.replace("transcribe_delete_", "").strip())
            if not transcript_id:
                await call.answer("Ошибка: неверный формат ID транскрипта", show_alert=True)
                return
            
            async with self.get_session() as session:
                transcript_service = get_transcript_service(session)
                user_service = get_user_service(session)
                
                # Получаем пользователя по Telegram ID
                user = await user_service.get_user_by_telegram_id(call.from_user.id)
                if not user:
                    await call.answer("Ошибка: пользователь не найден", show_alert=True)
                    return
                
                # Удаляем транскрипт
                success = await transcript_service.delete_transcript(user.id, transcript_id)
                if not success:
                    await call.answer("Ошибка: не удалось удалить транскрипт", show_alert=True)
                    return
                
                # Удаляем сообщение с транскриптом
                await call.message.delete()
                
                # Отправляем сообщение об успешном удалении
                await call.message.answer(
                    "✅ Транскрипт успешно удален",
                    reply_markup=get_transcript_menu_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Error deleting transcript: {e}")
            await call.answer("Произошла ошибка при удалении транскрипта", show_alert=True)
