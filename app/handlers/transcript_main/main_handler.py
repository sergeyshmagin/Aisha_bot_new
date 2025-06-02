"""
Основной обработчик транскриптов - координатор
Выделено из app/handlers/transcript_main.py для соблюдения правила ≤500 строк
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from app.handlers.transcript_base import TranscriptBaseHandler
from app.keyboards.transcript import get_transcript_menu_keyboard, get_back_to_menu_keyboard
from app.handlers.state import TranscribeStates
from .user_manager import TranscriptUserManager
from .history_manager import TranscriptHistoryManager
from .transcript_viewer import TranscriptViewer

logger = logging.getLogger(__name__)class TranscriptMainHandler(TranscriptBaseHandler):
    """
    Основной обработчик команд для работы с транскриптами (FSM).
    
    Координирует работу специализированных модулей:
    - TranscriptUserManager - управление пользователями
    - TranscriptHistoryManager - история транскриптов
    - TranscriptViewer - просмотр транскриптов
    """

    def __init__(self):
        """Инициализация обработчика и его компонентов"""
        super().__init__()
        self.router = Router()
