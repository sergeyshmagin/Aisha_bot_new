"""
Обработчики отмены создания аватара с улучшенным UX
Реализует рекомендации из docs/UX_CANCEL_GUIDELINES.md
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.core.di import get_user_service, get_avatar_service
from app.core.logger import get_logger
from app.keyboards.main import get_main_menu
from app.handlers.state import AvatarStates

logger = get_logger(__name__)
router = Router()async def get_cancel_confirmation_dialog(step: str, context: dict = None) -> tuple[str, InlineKeyboardMarkup]:
    """
    Создаёт диалог подтверждения отмены в зависимости от этапа создания
    
    Args:
        step: Этап создания (training_type, gender, name, photos, training)
        context: Дополнительная информация (имя аватара, количество фото и т.д.)
        
    Returns:
        tuple[str, InlineKeyboardMarkup]: Текст и клавиатура диалога
    """
    
    if step == "training_type":
