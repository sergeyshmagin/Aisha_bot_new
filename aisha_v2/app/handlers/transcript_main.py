"""
--- LEGACY: основной обработчик транскриптов, частично устарел ---
# Современные сценарии используют TranscriptProcessingHandler
# Данный файл содержит:
# - История транскриптов (актуально)
# - Основное меню транскрибации (актуально)
# - Обработка аудио/текста (LEGACY - перенесено в TranscriptProcessingHandler)
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
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
from aisha_v2.app.keyboards.transcript import get_transcript_menu_keyboard, get_back_to_menu_keyboard, get_transcript_actions_keyboard
from aisha_v2.app.handlers.state import TranscribeStates

logger = logging.getLogger(__name__)


class TranscriptMainHandler(TranscriptBaseHandler):
    """
    Основной обработчик команд для работы с транскриптами (FSM).
    """

    PAGE_SIZE = 5

    def __init__(self):
        self.router = Router()
        # Команды
        self.router.message.register(self._handle_open_transcript, F.text.regexp(r"^/open_"))  # legacy, можно удалить позже
        self.router.message.register(self._handle_history_command, Command("history"))
        
        # Специфичные callback-обработчики (порядок важен!)
        self.router.callback_query.register(self._handle_history_page, F.data.startswith("transcribe_history_page_"))
        self.router.callback_query.register(self._handle_open_transcript_cb, F.data.startswith("transcribe_open_"))
        
        # Обработчик основных кнопок меню транскрибации (только transcribe_*)
        self.router.callback_query.register(
            self._handle_transcript_callback, 
            F.data.in_(["transcribe_audio", "transcribe_text", "transcribe_history", "transcribe_back_to_menu"])
        )
        
        # Команды открытия транскрипта (legacy)
        self.router.message.register(
            self._handle_open_transcript,
            F.text.regexp(r'^/open_[a-f0-9\-]+$')
        )

    async def register_handlers(self):
        """Регистрация всех хендлеров"""
        self.router.message.register(self._handle_transcribe_command, Command("transcribe"))
        self.router.message.register(self._handle_transcribe_menu, StateFilter(TranscribeStates.menu), F.text == "🎤 Транскрибация")
        
        # Callback-обработчики
        self.router.callback_query.register(
            self._handle_history_page,
            F.data.startswith("transcribe_history_page_")
        )
        
        self.router.callback_query.register(
            self._handle_open_transcript_cb,
            F.data.startswith("transcribe_open_")
        )
        
        self.router.callback_query.register(
            self._handle_transcript_callback,
            F.data.startswith("transcribe_")
        )
        
        # --- УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК ОТКЛЮЧЕН: мешает работе transcript_* действий ---
        # self.router.callback_query.register(
        #     self._handle_unknown_callback,
        #     F.data.regexp(r'.*')
        # )
        
        # --- LEGACY: обработчики аудио/текста закомментированы, используется TranscriptProcessingHandler ---
        # self.router.message.register(self._handle_audio, F.audio, StateFilter(TranscribeStates.waiting_audio))
        # self.router.message.register(self._handle_voice, F.voice, StateFilter(TranscribeStates.waiting_audio))
        # self.router.message.register(self._handle_text, F.text, StateFilter(TranscribeStates.waiting_text))

    async def _handle_transcribe_command(self, message: Message, state: FSMContext):
        """
        Обработка команды /transcribe
        
        Args:
            message: Объект сообщения
            state: Состояние FSM
        """
        try:
            await state.set_state(TranscribeStates.menu)
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="🎤 Аудио", callback_data="transcribe_audio"),
                InlineKeyboardButton(text="📝 Текст", callback_data="transcribe_text")
            )
            builder.row(InlineKeyboardButton(text="📜 История", callback_data="transcribe_history"))
            builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="transcribe_back_to_menu"))
            
            await message.answer(
                "🎙 <b>Транскрибация</b>\n\nВыберите действие:",
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            logger.error(f"Ошибка при обработке команды /transcribe: {e}")
            await state.set_state(TranscribeStates.error)
            await message.answer("Произошла ошибка. Попробуйте позже.")

    async def _handle_transcribe_menu(self, message: Message, state: FSMContext):
        """Обработка входа в меню транскрибации"""
        try:
            await state.set_state(TranscribeStates.menu)
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="🎤 Аудио", callback_data="transcribe_audio"),
                InlineKeyboardButton(text="📝 Текст", callback_data="transcribe_text")
            )
            builder.row(InlineKeyboardButton(text="📜 История", callback_data="transcribe_history"))
            builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="transcribe_back_to_menu"))
            
            await message.answer(
                "🎙 <b>Транскрибация</b>\n\nВыберите действие:",
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            logger.error(f"Ошибка при входе в меню транскрибации: {e}")
            await state.set_state(TranscribeStates.error)
            await message.answer("Произошла ошибка. Попробуйте позже.")

    async def _send_history_page(self, message_or_call, user_id: int, page: int = 0, edit: bool = False):
        """
        Отправляет страницу истории транскриптов с inline-кнопками и пагинацией
        """
        async with self.get_session() as session:
            transcript_service = get_transcript_service(session)
            # Преобразуем user_id в строку для совместимости с TranscriptService
            user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
            transcripts = await transcript_service.list_transcripts(user_id_str, limit=self.PAGE_SIZE, offset=page * self.PAGE_SIZE)
            total = len(transcripts)
            if not transcripts:
                text = "📜 История транскриптов:\n\nПока пусто"
                kb = get_back_to_menu_keyboard()
                if edit and hasattr(message_or_call, 'message') and message_or_call.message.text:
                    try:
                        await message_or_call.message.edit_text(text, reply_markup=kb)
                    except Exception:
                        # Если не удалось отредактировать, отправляем новое сообщение
                        await message_or_call.message.answer(text, reply_markup=kb)
                else:
                    await message_or_call.answer(text, reply_markup=kb)
                return
            text = f"📜 <b>История транскриптов</b> (стр. {page+1}):\n\n"
            builder = InlineKeyboardBuilder()
            for t in transcripts:
                # Транскрипты уже возвращаются как словари из сервиса
                file_name = t.get("metadata", {}).get("file_name") or str(t.get("id"))
                created_at = t.get("created_at", "—")
                if isinstance(created_at, str):
                    created_at = created_at.replace('T', ' ')[:16]
                transcript_type = "Аудио" if t.get("metadata", {}).get("source") == "audio" else "Текст"
                btn_text = f"{file_name} | {created_at} | {transcript_type}"
                builder.row(InlineKeyboardButton(text=btn_text, callback_data=f"transcribe_open_{t['id']}"))
            # Пагинация
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"transcribe_history_page_{page-1}"))
            if total == self.PAGE_SIZE:
                nav_buttons.append(InlineKeyboardButton("Вперёд ➡️", callback_data=f"transcribe_history_page_{page+1}"))
            if nav_buttons:
                builder.row(*nav_buttons)
            builder.row(InlineKeyboardButton(text="◀️ Назад в меню", callback_data="transcribe_back_to_menu"))
            if edit and hasattr(message_or_call, 'message') and message_or_call.message.text:
                try:
                    await message_or_call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
                except Exception:
                    # Если не удалось отредактировать, отправляем новое сообщение
                    await message_or_call.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            else:
                await message_or_call.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

    async def _handle_history_command(self, message: Message, state: FSMContext):
        """
        История транскриптов с inline-кнопками и пагинацией
        """
        async with self.get_session() as session:
            user_service = get_user_service(session)
            user = await user_service.get_user_by_telegram_id(message.from_user.id)
            if not user:
                await message.reply("❌ Ошибка: пользователь не найден")
                return
            await self._send_history_page(message, str(user.id), page=0)

    async def _handle_history_page(self, call: CallbackQuery, state: FSMContext):
        """
        Callback для смены страницы истории
        """
        try:
            page = int(call.data.rsplit("_", 1)[-1])
            async with self.get_session() as session:
                user_service = get_user_service(session)
                user = await user_service.get_user_by_telegram_id(call.from_user.id)
                if not user:
                    await call.answer("Ошибка: пользователь не найден", show_alert=True)
                    return
                await self._send_history_page(call, str(user.id), page=page, edit=True)
        except Exception as e:
            logger.exception(f"Ошибка пагинации истории: {e}")
            await call.answer("Ошибка пагинации", show_alert=True)

    async def _handle_open_transcript_cb(self, call: CallbackQuery, state: FSMContext):
        """
        Callback для открытия карточки транскрипта из истории
        """
        try:
            transcript_id = safe_uuid(call.data.replace("transcribe_open_", "").strip())
            if not transcript_id:
                await call.answer("❌ Неверный ID транскрипта", show_alert=True)
                return
            async with self.get_session() as session:
                transcript_service = get_transcript_service(session)
                user_service = get_user_service(session)
                user = await user_service.get_user_by_telegram_id(call.from_user.id)
                if not user:
                    await call.answer("❌ Ошибка: пользователь не найден", show_alert=True)
                    return
                transcript = await transcript_service.get_transcript(str(user.id), transcript_id)
                if not transcript:
                    await call.answer("❌ Транскрипт не найден", show_alert=True)
                    return
                content = await transcript_service.get_transcript_content(str(user.id), transcript_id)
                if content:
                    try:
                        text = content.decode("utf-8")
                    except Exception:
                        text = None
                    if text:
                        transcript["preview"] = text[:300]
                from aisha_v2.app.handlers.transcript_processing import TranscriptProcessingHandler
                card_text = TranscriptProcessingHandler().render_transcript_card(transcript)
                keyboard = get_transcript_actions_keyboard(str(transcript["id"]))
                
                # Проверяем, можно ли редактировать сообщение (есть ли в нем текст)
                if call.message.text:
                    try:
                        await call.message.edit_text(card_text, reply_markup=keyboard, parse_mode="HTML")
                    except Exception:
                        # Если не удалось отредактировать, отправляем новое сообщение
                        await call.message.answer(card_text, reply_markup=keyboard, parse_mode="HTML")
                else:
                    # Если сообщение содержит документ или другой контент, отправляем новое
                    await call.message.answer(card_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.exception(f"Ошибка при открытии транскрипта (callback): {e}")
            await call.answer("Ошибка при открытии транскрипта", show_alert=True)

    # --- LEGACY: методы обработки аудио/текста перенесены в TranscriptProcessingHandler ---
    # async def _handle_audio(self, message: Message, state: FSMContext):
    #     """
    #     Обработка аудио
    #     
    #     Args:
    #         message: Объект сообщения
    #         state: Состояние FSM
    #     """
    #     try:
    #         from aisha_v2.app.handlers.transcript_processing import TranscriptProcessingHandler
    #         
    #         # Делегируем обработку специализированному обработчику
    #         processing_handler = TranscriptProcessingHandler()
    #         await processing_handler._handle_audio_processing(message, state)
    #     except Exception as e:
    #         logger.error(f"Ошибка при обработке аудио: {e}")
    #         await state.set_state(TranscribeStates.error)
    #         await message.reply("Произошла ошибка при обработке аудио.")
    
    # async def _handle_voice(self, message: Message, state: FSMContext):
    #     """
    #     Обработка голосового сообщения
    #     
    #     Args:
    #         message: Объект сообщения
    #         state: Состояние FSM
    #     """
    #     try:
    #         from aisha_v2.app.handlers.transcript_processing import TranscriptProcessingHandler
    #         
    #         # Делегируем обработку специализированному обработчику
    #         processing_handler = TranscriptProcessingHandler()
    #         await processing_handler._handle_audio_processing(message, state)
    #     except Exception as e:
    #         logger.error(f"Ошибка при обработке голосового сообщения: {e}")
    #         await state.set_state(TranscribeStates.error)
    #         await message.reply("Произошла ошибка при обработке голосового сообщения.")
    
    # async def _handle_text(self, message: Message, state: FSMContext):
    #     """
    #     Обработка текстовых сообщений
    #     
    #     Args:
    #         message: Объект сообщения
    #         state: Состояние FSM
    #     """
    #     try:
    #         from aisha_v2.app.handlers.transcript_processing import TranscriptProcessingHandler
    #         
    #         # Делегируем обработку специализированному обработчику
    #         processing_handler = TranscriptProcessingHandler()
    #         await processing_handler._handle_text_processing(message, state)
    #     except Exception as e:
    #         logger.error(f"Ошибка при обработке текста: {e}")
    #         await state.set_state(TranscribeStates.error)
    #         await message.reply("Произошла ошибка при обработке текста.")

    async def _handle_open_transcript(self, message: Message, state: FSMContext):
        """
        Открывает карточку транскрипта по команде /open_{id} из истории
        """
        try:
            parts = message.text.strip().split("_", 1)
            if len(parts) != 2 or not parts[1]:
                await message.answer("❌ Неверная команда. Пример: /open_<id>")
                return
            transcript_id = safe_uuid(parts[1])
            if not transcript_id:
                await message.answer("❌ Неверный ID транскрипта")
                return
            async with self.get_session() as session:
                transcript_service = get_transcript_service(session)
                user_service = get_user_service(session)
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user:
                    await message.answer("❌ Ошибка: пользователь не найден")
                    return
                transcript = await transcript_service.get_transcript(str(user.id), transcript_id)
                if not transcript:
                    await message.answer("❌ Транскрипт не найден")
                    return
                # Получаем preview текста
                content = await transcript_service.get_transcript_content(str(user.id), transcript_id)
                if content:
                    try:
                        text = content.decode("utf-8")
                    except Exception:
                        text = None
                    if text:
                        transcript["preview"] = text[:300]
                # Используем функцию рендера карточки из processing handler
                from aisha_v2.app.handlers.transcript_processing import TranscriptProcessingHandler
                card_text = TranscriptProcessingHandler().render_transcript_card(transcript)
                keyboard = get_transcript_actions_keyboard(str(transcript["id"]))
                await message.answer(card_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.exception(f"Ошибка при открытии транскрипта: {e}")
            await message.answer("Произошла ошибка при открытии транскрипта.")

    async def _handle_transcript_callback(self, call: CallbackQuery, state: FSMContext):
        """
        Обработка callback-запросов для основного меню транскриптов
        """
        try:
            action = call.data.split("_")[1]
            
            if action == "audio":
                await state.set_state(TranscribeStates.waiting_audio)
                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(text="◀️ Назад в меню", callback_data="transcribe_back_to_menu"))
                
                await call.message.edit_text(
                    "🎤 Отправьте аудио или голосовое сообщение для транскрибации:",
                    reply_markup=builder.as_markup()
                )
                
            elif action == "text":
                await state.set_state(TranscribeStates.waiting_text)
                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(text="◀️ Назад в меню", callback_data="transcribe_back_to_menu"))
                
                await call.message.edit_text(
                    "📝 Отправьте текстовый файл (.txt) для обработки:",
                    reply_markup=builder.as_markup()
                )
                
            elif action == "history":
                async with self.get_session() as session:
                    user_service = get_user_service(session)
                    user = await user_service.get_user_by_telegram_id(call.from_user.id)
                    if not user:
                        await call.answer("❌ Ошибка: пользователь не найден", show_alert=True)
                        return
                    await self._send_history_page(call, str(user.id), page=0, edit=True)
                
            elif action == "back":
                await state.clear()
                await call.message.edit_text(
                    "🎙 <b>Транскрибация</b>\n\nВыберите действие:",
                    parse_mode="HTML",
                    reply_markup=get_transcript_menu_keyboard()
                )
            
            else:
                logger.warning(f"Неизвестное действие: {action}")
                await call.answer("Неизвестное действие")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке callback: {e}")
            await call.answer("Произошла ошибка")
