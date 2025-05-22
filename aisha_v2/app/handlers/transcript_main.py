"""
Основной обработчик команд для работы с транскриптами.
Делегирует задачи специализированным обработчикам.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from aisha_v2.app.handlers.transcript_base import TranscriptBaseHandler
from aisha_v2.app.core.di import (
    get_audio_processing_service,
    get_text_processing_service,
    get_transcript_service,
    get_user_service,
)
from aisha_v2.app.utils.uuid_utils import safe_uuid
from aisha_v2.app.keyboards.transcript import get_transcript_menu_keyboard, get_back_to_menu_keyboard
from aisha_v2.app.handlers.state import TranscribeStates

logger = logging.getLogger(__name__)


class TranscriptMainHandler(TranscriptBaseHandler):
    """
    Основной обработчик команд для работы с транскриптами (FSM).
    """

    def __init__(self):
        self.router = Router()

    async def register_handlers(self):
        """Регистрация всех хендлеров"""
        self.router.message.register(self._handle_transcribe_command, Command("transcribe"))
        self.router.message.register(self._handle_transcribe_menu, StateFilter(TranscribeStates.menu), F.text == "🎤 Транскрибация")
        self.router.message.register(self._handle_history_command, Command("history"))
        self.router.message.register(self._handle_audio, F.audio, StateFilter(TranscribeStates.waiting_audio))
        self.router.message.register(self._handle_voice, F.voice, StateFilter(TranscribeStates.waiting_audio))
        self.router.message.register(self._handle_text, F.text, StateFilter(TranscribeStates.waiting_text))
        self.router.callback_query.register(self._handle_transcript_callback, F.data.startswith("transcribe_"))

    async def _handle_transcribe_command(self, message: Message, state: FSMContext):
        """
        Обработка команды /transcribe
        
        Args:
            message: Объект сообщения
            state: Состояние FSM
        """
        try:
            await state.set_state(TranscribeStates.menu)
            await message.answer(
                "🎙 <b>Транскрибация</b>\n\nВыберите действие:",
                parse_mode="HTML",
                reply_markup=get_transcript_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Ошибка при обработке команды /transcribe: {e}")
            await state.set_state(TranscribeStates.error)
            await message.answer("Произошла ошибка. Попробуйте позже.")

    async def _handle_transcribe_menu(self, message: Message, state: FSMContext):
        """Обработка входа в меню транскрибации"""
        try:
            await state.set_state(TranscribeStates.menu)
            await message.answer(
                "🎙 <b>Транскрибация</b>\n\nВыберите действие:",
                parse_mode="HTML",
                reply_markup=get_transcript_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Ошибка при входе в меню транскрибации: {e}")
            await state.set_state(TranscribeStates.error)
            await message.answer("Произошла ошибка. Попробуйте позже.")

    async def _handle_history_command(self, message: Message, state: FSMContext):
        """
        Обработка команды /history
        
        Args:
            message: Объект сообщения
            state: Состояние FSM
        """
        try:
            async with self.get_session() as session:
                user_service = get_user_service(session)
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user:
                    await message.reply("❌ Ошибка: пользователь не найден")
                    return
                
                # Получаем историю транскриптов
                transcripts = await user_service.get_user_transcripts(user.id)
                
                if not transcripts:
                    await message.reply("У вас пока нет транскриптов.")
                    return
                
                # Формируем сообщение с историей
                history_text = "📜 История транскриптов:\n\n"
                for transcript in transcripts:
                    history_text += f"• {transcript['created_at']}: {transcript['text'][:100]}...\n"
                
                await message.reply(history_text)
        except Exception as e:
            logger.error(f"Ошибка при получении истории: {e}")
            await message.reply("Произошла ошибка при получении истории.")
    
    async def _handle_audio(self, message: Message, state: FSMContext):
        """
        Обработка аудио
        
        Args:
            message: Объект сообщения
            state: Состояние FSM
        """
        try:
            from aisha_v2.app.handlers.transcript_processing import TranscriptProcessingHandler
            
            # Делегируем обработку специализированному обработчику
            processing_handler = TranscriptProcessingHandler()
            await processing_handler._handle_audio_processing(message, state)
        except Exception as e:
            logger.error(f"Ошибка при обработке аудио: {e}")
            await state.set_state(TranscribeStates.error)
            await message.reply("Произошла ошибка при обработке аудио.")
    
    async def _handle_voice(self, message: Message, state: FSMContext):
        """
        Обработка голосового сообщения
        
        Args:
            message: Объект сообщения
            state: Состояние FSM
        """
        try:
            from aisha_v2.app.handlers.transcript_processing import TranscriptProcessingHandler
            
            # Делегируем обработку специализированному обработчику
            processing_handler = TranscriptProcessingHandler()
            await processing_handler._handle_audio_processing(message, state)
        except Exception as e:
            logger.error(f"Ошибка при обработке голосового сообщения: {e}")
            await state.set_state(TranscribeStates.error)
            await message.reply("Произошла ошибка при обработке голосового сообщения.")
    
    async def _handle_text(self, message: Message, state: FSMContext):
        """
        Обработка текстовых сообщений
        
        Args:
            message: Объект сообщения
            state: Состояние FSM
        """
        try:
            from aisha_v2.app.handlers.transcript_processing import TranscriptProcessingHandler
            
            # Делегируем обработку специализированному обработчику
            processing_handler = TranscriptProcessingHandler()
            await processing_handler._handle_text_processing(message, state)
        except Exception as e:
            logger.error(f"Ошибка при обработке текста: {e}")
            await state.set_state(TranscribeStates.error)
            await message.reply("Произошла ошибка при обработке текста.")
    
    async def _handle_transcript_callback(self, call: CallbackQuery, state: FSMContext):
        """
        Обработка callback-запросов для транскриптов
        
        Args:
            call: Объект CallbackQuery
            state: Состояние FSM
        """
        try:
            action = call.data.split("_")[1]
            
            if action == "audio":
                await state.set_state(TranscribeStates.waiting_audio)
                await call.message.edit_text(
                    "🎤 Отправьте аудио или голосовое сообщение для транскрибации:",
                    reply_markup=get_back_to_menu_keyboard()
                )
                
            elif action == "text":
                await state.set_state(TranscribeStates.waiting_text)
                await call.message.edit_text(
                    "📝 Отправьте текст для обработки:",
                    reply_markup=get_back_to_menu_keyboard()
                )
                
            elif action == "history":
                await call.message.edit_text(
                    "📜 История транскриптов:\n\nПока пусто",
                    reply_markup=get_back_to_menu_keyboard()
                )
                
            elif action == "back":
                await state.clear()
                await call.message.edit_text(
                    "🎙 <b>Транскрибация</b>\n\nВыберите действие:",
                    parse_mode="HTML",
                    reply_markup=get_transcript_menu_keyboard()
                )
            
            else:
                logger.warning(f"Неизвестное действие в callback: {action}")
                await call.answer("Неизвестное действие")
                
            await call.answer()
            
        except Exception as e:
            logger.error(f"Ошибка при обработке callback: {e}")
            await state.set_state(TranscribeStates.error)
            await call.answer("Произошла ошибка. Попробуйте еще раз.")
