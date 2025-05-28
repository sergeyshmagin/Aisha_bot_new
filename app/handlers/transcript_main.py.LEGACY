"""
Основной обработчик транскриптов - история, меню транскрибации
Современные сценарии обработки используют TranscriptProcessingHandler
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton  # Явный импорт для предотвращения конфликтов
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from app.handlers.transcript_base import TranscriptBaseHandler
from app.core.di import (
    get_audio_processing_service,
    get_text_processing_service,
    get_transcript_service,
    get_user_service_with_session,
)
from app.utils.uuid_utils import safe_uuid
from app.keyboards.transcript import get_transcript_menu_keyboard, get_back_to_menu_keyboard, get_transcript_actions_keyboard
from app.handlers.state import TranscribeStates

logger = logging.getLogger(__name__)


class TranscriptMainHandler(TranscriptBaseHandler):
    """
    Основной обработчик команд для работы с транскриптами (FSM).
    """

    PAGE_SIZE = 5

    def __init__(self):
        self.router = Router()
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

    async def _send_history_page(self, message_or_call, user_id: int, page: int = 0, edit: bool = False):
        """
        Отправляет страницу истории транскриптов с inline-кнопками и пагинацией
        """
        logger.info(f"[SEND_HISTORY] Начало: user_id={user_id}, page={page}, edit={edit}")
        logger.info(f"[SEND_HISTORY] InlineKeyboardButton type: {type(InlineKeyboardButton)}")
        
        async with self.get_session() as session:
            transcript_service = get_transcript_service(session)
            # Преобразуем user_id в строку для совместимости с TranscriptService
            user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
            transcripts = await transcript_service.list_transcripts(user_id_str, limit=self.PAGE_SIZE, offset=page * self.PAGE_SIZE)
            total = len(transcripts)
            logger.info(f"[SEND_HISTORY] Получено {total} транскриптов")
            
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
            
            # Добавляем кнопки транскриптов
            for t in transcripts:
                # Используем новую функцию для дружелюбного отображения
                btn_text = self._format_friendly_filename(t)
                
                # Явное создание кнопки с проверкой типа
                try:
                    btn = InlineKeyboardButton(text=btn_text, callback_data=f"transcribe_open_{t['id']}")
                    logger.info(f"[SEND_HISTORY] Создана кнопка транскрипта: {type(btn)}")
                    builder.row(btn)
                except Exception as e:
                    logger.error(f"[SEND_HISTORY] Ошибка создания кнопки транскрипта: {e}")
                    raise
                    
            # Пагинация
            nav_buttons = []
            if page > 0:
                try:
                    back_btn = InlineKeyboardButton(text="⬅️ Назад", callback_data=f"transcribe_history_page_{page-1}")
                    logger.info(f"[SEND_HISTORY] Создана кнопка 'Назад': {type(back_btn)}")
                    nav_buttons.append(back_btn)
                except Exception as e:
                    logger.error(f"[SEND_HISTORY] Ошибка создания кнопки 'Назад': {e}")
                    raise
                    
            if total == self.PAGE_SIZE:
                try:
                    forward_btn = InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"transcribe_history_page_{page+1}")
                    logger.info(f"[SEND_HISTORY] Создана кнопка 'Вперёд': {type(forward_btn)}")
                    nav_buttons.append(forward_btn)
                except Exception as e:
                    logger.error(f"[SEND_HISTORY] Ошибка создания кнопки 'Вперёд': {e}")
                    raise
                    
            if nav_buttons:
                builder.row(*nav_buttons)
                
            # Кнопка возврата в меню
            try:
                menu_btn = InlineKeyboardButton(text="◀️ Назад в меню", callback_data="transcribe_back_to_menu")
                logger.info(f"[SEND_HISTORY] Создана кнопка 'Назад в меню': {type(menu_btn)}")
                builder.row(menu_btn)
            except Exception as e:
                logger.error(f"[SEND_HISTORY] Ошибка создания кнопки 'Назад в меню': {e}")
                raise
                
            # Отправка сообщения
            if edit and hasattr(message_or_call, 'message') and message_or_call.message.text:
                try:
                    await message_or_call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
                except Exception:
                    # Если не удалось отредактировать, отправляем новое сообщение
                    await message_or_call.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            else:
                await message_or_call.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
                
        logger.info(f"[SEND_HISTORY] Завершено успешно")

    async def _handle_history_command(self, message: Message, state: FSMContext):
        """
        История транскриптов с inline-кнопками и пагинацией
        """
        async with self.get_session() as session:
            user_service = get_user_service_with_session(session)
            user = await user_service.get_user_by_telegram_id(message.from_user.id)
            if not user:
                # Автоматически регистрируем пользователя
                user_data = {
                    "id": message.from_user.id,
                    "username": message.from_user.username,
                    "first_name": message.from_user.first_name,
                    "last_name": message.from_user.last_name,
                    "language_code": message.from_user.language_code or "ru",
                    "is_bot": message.from_user.is_bot,
                    "is_premium": getattr(message.from_user, "is_premium", False)
                }
                user = await user_service.register_user(user_data)
                if not user:
                    await message.reply("❌ Ошибка регистрации пользователя")
                    return
            await self._send_history_page(message, str(user.id), page=0)

    async def _handle_history_page(self, call: CallbackQuery, state: FSMContext):
        """
        Callback для смены страницы истории
        """
        try:
            page = int(call.data.rsplit("_", 1)[-1])
            async with self.get_session() as session:
                user_service = get_user_service_with_session(session)
                user = await user_service.get_user_by_telegram_id(call.from_user.id)
                if not user:
                    # Автоматически регистрируем пользователя
                    user_data = {
                        "id": call.from_user.id,
                        "username": call.from_user.username,
                        "first_name": call.from_user.first_name,
                        "last_name": call.from_user.last_name,
                        "language_code": call.from_user.language_code or "ru",
                        "is_bot": call.from_user.is_bot,
                        "is_premium": getattr(call.from_user, "is_premium", False)
                    }
                    user = await user_service.register_user(user_data)
                    if not user:
                        await call.answer("❌ Ошибка регистрации пользователя", show_alert=True)
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
                user_service = get_user_service_with_session(session)
                user = await user_service.get_user_by_telegram_id(call.from_user.id)
                if not user:
                    # Автоматически регистрируем пользователя
                    user_data = {
                        "id": call.from_user.id,
                        "username": call.from_user.username,
                        "first_name": call.from_user.first_name,
                        "last_name": call.from_user.last_name,
                        "language_code": call.from_user.language_code or "ru",
                        "is_bot": call.from_user.is_bot,
                        "is_premium": getattr(call.from_user, "is_premium", False)
                    }
                    user = await user_service.register_user(user_data)
                    if not user:
                        await call.answer("❌ Ошибка регистрации пользователя", show_alert=True)
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
                from app.handlers.transcript_processing import TranscriptProcessingHandler
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
                user_service = get_user_service_with_session(session)
                user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not user:
                    # Автоматически регистрируем пользователя
                    user_data = {
                        "id": message.from_user.id,
                        "username": message.from_user.username,
                        "first_name": message.from_user.first_name,
                        "last_name": message.from_user.last_name,
                        "language_code": message.from_user.language_code or "ru",
                        "is_bot": message.from_user.is_bot,
                        "is_premium": getattr(message.from_user, "is_premium", False)
                    }
                    user = await user_service.register_user(user_data)
                    if not user:
                        await message.answer("❌ Ошибка регистрации пользователя")
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
                from app.handlers.transcript_processing import TranscriptProcessingHandler
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
                    async with self.get_session() as session:
                        user_service = get_user_service_with_session(session)
                        user = await user_service.get_user_by_telegram_id(call.from_user.id)
                        if not user:
                            # Автоматически регистрируем пользователя
                            user_data = {
                                "id": call.from_user.id,
                                "username": call.from_user.username,
                                "first_name": call.from_user.first_name,
                                "last_name": call.from_user.last_name,
                                "language_code": call.from_user.language_code or "ru",
                                "is_bot": call.from_user.is_bot,
                                "is_premium": getattr(call.from_user, "is_premium", False)
                            }
                            user = await user_service.register_user(user_data)
                            if not user:
                                await call.answer("❌ Ошибка регистрации пользователя", show_alert=True)
                                return
                        logger.info(f"[HISTORY] Начинаем отправку истории для user_id={user.id}")
                        await self._send_history_page(call, str(user.id), page=0, edit=True)
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

    def _format_friendly_filename(self, transcript_data: dict) -> str:
        """
        Форматирует название файла для дружелюбного отображения пользователю
        
        Args:
            transcript_data: Данные транскрипта с метаданными
            
        Returns:
            Дружелюбное название файла
        """
        metadata = transcript_data.get("metadata", {})
        source = metadata.get("source", "unknown")
        created_at = transcript_data.get("created_at", "")
        
        # Получаем исходное название файла
        original_filename = metadata.get("file_name", "")
        
        # Парсим дату создания
        try:
            if isinstance(created_at, str):
                # Убираем микросекунды и временную зону для упрощения
                clean_date = created_at.split('.')[0].replace('T', ' ')
                dt = datetime.fromisoformat(clean_date)
                date_str = dt.strftime("%d.%m %H:%M")
            else:
                date_str = "—"
        except Exception:
            date_str = "—"
        
        # Определяем тип и иконку
        if source == "audio":
            type_icon = "🎵"
            type_name = "Аудио"
        else:
            type_icon = "📝"
            type_name = "Текст"
        
        # Пытаемся извлечь осмысленное название из оригинального файла
        if original_filename:
            # Убираем расширение
            name_without_ext = original_filename.rsplit('.', 1)[0]
            
            # Если это техническое название вроде "2025-05-21_10-01_file_362"
            if '_file_' in name_without_ext or name_without_ext.count('_') >= 2:
                # Используем просто тип и дату
                friendly_name = f"{type_icon} {type_name}"
            else:
                # Используем оригинальное название, но сокращаем если длинное
                if len(name_without_ext) > 20:
                    friendly_name = f"{type_icon} {name_without_ext[:17]}..."
                else:
                    friendly_name = f"{type_icon} {name_without_ext}"
        else:
            # Fallback к типу файла
            friendly_name = f"{type_icon} {type_name}"
        
        # Добавляем количество слов для текстовых файлов
        word_count = metadata.get("word_count")
        if word_count and source == "text":
            friendly_name += f" ({word_count} сл.)"
        
        return f"{friendly_name} • {date_str}"
