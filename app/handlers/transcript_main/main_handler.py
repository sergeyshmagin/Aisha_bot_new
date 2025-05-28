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

logger = logging.getLogger(__name__)


class TranscriptMainHandler(TranscriptBaseHandler):
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
        
        # Инициализируем специализированные модули
        self.user_manager = TranscriptUserManager(self.get_session)
        self.history_manager = TranscriptHistoryManager(self.get_session)
        self.transcript_viewer = TranscriptViewer(self.get_session)
        
        # Регистрируем базовые обработчики (как в Legacy)
        self._register_base_handlers()

    def _register_base_handlers(self):
        """Регистрация базовых обработчиков (как в Legacy __init__)"""
        # Команды
        self.router.message.register(self._handle_history_command, Command("history"))
        
        # Специфичные callback-обработчики (порядок важен!)
        self.router.callback_query.register(self._handle_history_page, F.data.startswith("transcribe_history_page_"))
        self.router.callback_query.register(self._handle_open_transcript_cb, F.data.startswith("transcribe_open_"))
        
        # Обработчик основных кнопок меню транскрибации (только transcribe_*)
        self.router.callback_query.register(
            self._handle_transcript_callback, 
            F.data.in_(["transcribe_audio", "transcribe_text", "transcribe_history"])
        )
        
        # Отдельный обработчик для возврата в меню транскрибации
        self.router.callback_query.register(
            self._handle_back_to_transcribe_menu,
            F.data == "transcribe_back_to_menu"
        )

    async def register_handlers(self):
        """Регистрация всех хендлеров (как в Legacy)"""
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
            builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
            
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
            builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
            
            await message.answer(
                "🎙 <b>Транскрибация</b>\n\nВыберите действие:",
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            logger.error(f"Ошибка при входе в меню транскрибации: {e}")
            await state.set_state(TranscribeStates.error)
            await message.answer("Произошла ошибка. Попробуйте позже.")

    async def _handle_history_command(self, message: Message, state: FSMContext):
        """
        История транскриптов с inline-кнопками и пагинацией
        """
        # Получаем или регистрируем пользователя
        user = await self.user_manager.get_or_register_user(message.from_user)
        if not user:
            await message.reply("❌ Ошибка регистрации пользователя")
            return
        
        # Отправляем первую страницу истории
        await self.history_manager.send_history_page(message, str(user.id), page=0)

    async def _handle_history_page(self, call: CallbackQuery, state: FSMContext):
        """
        Callback для смены страницы истории
        """
        try:
            page = int(call.data.rsplit("_", 1)[-1])
            user = await self.user_manager.get_or_register_user(call.from_user)
            if not user:
                await call.answer("❌ Ошибка регистрации пользователя", show_alert=True)
                return
            await self.history_manager.send_history_page(call, str(user.id), page=page, edit=True)
        except Exception as e:
            logger.exception(f"Ошибка пагинации истории: {e}")
            await call.answer("Ошибка пагинации", show_alert=True)

    async def _handle_open_transcript_cb(self, call: CallbackQuery, state: FSMContext):
        """
        Callback для открытия карточки транскрипта из истории
        """
        try:
            user = await self.user_manager.get_or_register_user(call.from_user)
            if not user:
                await call.answer("❌ Ошибка регистрации пользователя", show_alert=True)
                return
            
            # Открываем транскрипт через viewer
            await self.transcript_viewer.open_transcript_by_callback(call, str(user.id))
        except Exception as e:
            logger.exception(f"Ошибка при открытии транскрипта (callback): {e}")
            await call.answer("Ошибка при открытии транскрипта", show_alert=True)

    async def _handle_open_transcript(self, message: Message, state: FSMContext):
        """
        Открывает карточку транскрипта по команде /open_{id} из истории
        (Метод для совместимости с Legacy - не используется, так как команда не зарегистрирована)
        """
        try:
            user = await self.user_manager.get_or_register_user(message.from_user)
            if not user:
                await message.answer("❌ Ошибка регистрации пользователя")
                return
            
            # Открываем транскрипт через viewer
            await self.transcript_viewer.open_transcript_by_command(message, str(user.id))
        except Exception as e:
            logger.exception(f"Ошибка при открытии транскрипта: {e}")
            await message.answer("Произошла ошибка при открытии транскрипта.")

    async def _handle_transcript_callback(self, call: CallbackQuery, state: FSMContext):
        """
        Обработка callback-запросов для основного меню транскриптов
        """
        try:
            # Парсим action из callback_data
            parts = call.data.split("_")
            if len(parts) < 2:
                logger.warning(f"Неверный формат callback_data: {call.data}")
                await call.answer("Неверный формат данных")
                return
                
            action = parts[1]
            
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
                try:
                    user = await self.user_manager.get_or_register_user(call.from_user)
                    if not user:
                        await call.answer("❌ Ошибка регистрации пользователя", show_alert=True)
                        return
                    logger.info(f"[HISTORY] Начинаем отправку истории для user_id={user.id}")
                    await self.history_manager.send_history_page(call, str(user.id), page=0, edit=True)
                    logger.info(f"[HISTORY] История отправлена успешно")
                except Exception as e:
                    logger.exception(f"[HISTORY] Ошибка при обработке истории: {e}")
                    try:
                        await call.message.edit_text(
                            "📜 <b>История транскриптов</b>\n\nПроизошла ошибка при загрузке истории.\nПопробуйте позже.",
                            parse_mode="HTML",
                            reply_markup=get_back_to_menu_keyboard()
                        )
                    except:
                        await call.message.answer(
                            "📜 <b>История транскриптов</b>\n\nПроизошла ошибка при загрузке истории.\nПопробуйте позже.",
                            parse_mode="HTML",
                            reply_markup=get_back_to_menu_keyboard()
                        )
                
            else:
                logger.warning(f"Неизвестное действие: {action}, полный callback: {call.data}")
                await call.answer("Неизвестное действие")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке callback: {e}")
            await call.answer("Произошла ошибка")

    async def _handle_back_to_transcribe_menu(self, call: CallbackQuery, state: FSMContext):
        """
        Обработка callback-запроса для возврата в меню транскрибации
        """
        try:
            await state.clear()
            try:
                await call.message.edit_text(
                    "🎙 <b>Транскрибация</b>\n\nВыберите действие:",
                    parse_mode="HTML",
                    reply_markup=get_transcript_menu_keyboard()
                )
            except Exception as edit_error:
                # Если не удалось отредактировать (например, сообщение содержит документ)
                logger.warning(f"Не удалось отредактировать сообщение при возврате в меню: {edit_error}")
                await call.message.answer(
                    "🎙 <b>Транскрибация</b>\n\nВыберите действие:",
                    parse_mode="HTML",
                    reply_markup=get_transcript_menu_keyboard()
                )
        except Exception as e:
            logger.error(f"Ошибка при возврате в меню транскрибации: {e}")
            await call.answer("Ошибка при возврате в меню транскрибации")

    # Метод для обратной совместимости
    def _format_friendly_filename(self, transcript_data: dict) -> str:
        """
        Форматирует название файла для дружелюбного отображения пользователю
        (Метод для обратной совместимости - делегирует к TranscriptDisplayData)
        """
        from .models import TranscriptDisplayData
        display_data = TranscriptDisplayData(transcript_data)
        return display_data.get_friendly_filename()

    # Метод для обратной совместимости
    async def _send_history_page(self, message_or_call, user_id: int, page: int = 0, edit: bool = False):
        """
        Отправляет страницу истории транскриптов
        (Метод для обратной совместимости - делегирует к HistoryManager)
        """
        await self.history_manager.send_history_page(message_or_call, str(user_id), page, edit)