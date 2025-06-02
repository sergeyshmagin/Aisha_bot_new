"""
Управление историей транскриптов
Выделено из app/handlers/transcript_main.py для соблюдения правила ≤500 строк
"""
import logging
from typing import List, Dict, Any, Union
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.core.di import get_transcript_service
from app.keyboards.transcript import get_back_to_menu_keyboard
from .models import TranscriptMainConfig, TranscriptDisplayData

logger = logging.getLogger(__name__)class TranscriptHistoryManager:
    """
    Менеджер истории транскриптов
    
    Отвечает за:
    - Получение списка транскриптов с пагинацией
    - Форматирование истории для отображения
    - Создание клавиатур с навигацией
    - Отправку страниц истории
    """
    
    def __init__(self, get_session_func):
        """
        Инициализация менеджера истории
        
        Args:
            get_session_func: Функция получения сессии БД
        """
        self.get_session = get_session_func
        self.config = TranscriptMainConfig()
    
    async def get_transcripts_page(self, user_id: str, page: int = 0) -> List[Dict[str, Any]]:
        """
        Получает страницу транскриптов для пользователя
        
        Args:
            user_id: ID пользователя
            page: Номер страницы (начиная с 0)
            
        Returns:
            Список транскриптов для страницы
        """
        try:
            async with self.get_session() as session:
                transcript_service = get_transcript_service(session)
                # Преобразуем user_id в строку для совместимости с TranscriptService
                user_id_str = str(user_id) if not isinstance(user_id, str) else user_id
                transcripts = await transcript_service.list_transcripts(
                    user_id_str, 
                    limit=self.config.PAGE_SIZE, 
                    offset=page * self.config.PAGE_SIZE
                )
                logger.info(f"Получено {len(transcripts)} транскриптов для пользователя {user_id}, страница {page}")
                return transcripts
        except Exception as e:
            logger.error(f"Ошибка при получении транскриптов для пользователя {user_id}, страница {page}: {e}")
            return []
    
    def create_history_keyboard(self, transcripts: List[Dict[str, Any]], page: int) -> InlineKeyboardMarkup:
        """
        Создает клавиатуру для истории транскриптов
        
        Args:
            transcripts: Список транскриптов
            page: Текущая страница
            
        Returns:
            Inline клавиатура с кнопками транскриптов и навигацией
        """
        builder = InlineKeyboardBuilder()
        
        # Добавляем кнопки транскриптов
        for transcript in transcripts:
            display_data = TranscriptDisplayData(transcript)
            btn_text = display_data.get_friendly_filename()
            
            try:
                btn = InlineKeyboardButton(
                    text=btn_text, 
                    callback_data=f"transcribe_open_{display_data.id}"
                )
                logger.debug(f"Создана кнопка транскрипта: {display_data.id}")
                builder.row(btn)
            except Exception as e:
                logger.error(f"Ошибка создания кнопки транскрипта {display_data.id}: {e}")
                continue
        
        # Пагинация
        nav_buttons = []
        if page > 0:
            try:
                back_btn = InlineKeyboardButton(
                    text="⬅️ Назад", 
                    callback_data=f"transcribe_history_page_{page-1}"
                )
                nav_buttons.append(back_btn)
                logger.debug(f"Создана кнопка 'Назад' для страницы {page-1}")
            except Exception as e:
                logger.error(f"Ошибка создания кнопки 'Назад': {e}")
        
        if len(transcripts) == self.config.PAGE_SIZE:
            try:
                forward_btn = InlineKeyboardButton(
                    text="Вперёд ➡️", 
                    callback_data=f"transcribe_history_page_{page+1}"
                )
                nav_buttons.append(forward_btn)
                logger.debug(f"Создана кнопка 'Вперёд' для страницы {page+1}")
            except Exception as e:
                logger.error(f"Ошибка создания кнопки 'Вперёд': {e}")
        
        if nav_buttons:
            builder.row(*nav_buttons)
        
        # Кнопка возврата в меню
        try:
            menu_btn = InlineKeyboardButton(
                text="◀️ Назад в меню", 
                callback_data="transcribe_back_to_menu"
            )
            builder.row(menu_btn)
            logger.debug("Создана кнопка 'Назад в меню'")
        except Exception as e:
            logger.error(f"Ошибка создания кнопки 'Назад в меню': {e}")
        
        return builder.as_markup()
    
    def format_history_text(self, page: int, has_transcripts: bool) -> str:
        """
        Форматирует текст для страницы истории
        
        Args:
            page: Номер страницы
            has_transcripts: Есть ли транскрипты на странице
            
        Returns:
            Отформатированный текст
        """
        if not has_transcripts:
            return "📜 История транскриптов:\n\nПока пусто"
        
        return f"📜 <b>История транскриптов</b> (стр. {page+1}):\n\n"
    
    async def send_history_page(
        self, 
        message_or_call: Union[Message, CallbackQuery], 
        user_id: str, 
        page: int = 0, 
        edit: bool = False
    ) -> None:
        """
        Отправляет страницу истории транскриптов с inline-кнопками и пагинацией
        
        Args:
            message_or_call: Объект сообщения или callback
            user_id: ID пользователя
            page: Номер страницы
            edit: Редактировать существующее сообщение или отправить новое
        """
        logger.info(f"Начало отправки истории: user_id={user_id}, page={page}, edit={edit}")
        
        try:
            # Получаем транскрипты для страницы
            transcripts = await self.get_transcripts_page(user_id, page)
            
            # Форматируем текст
            text = self.format_history_text(page, bool(transcripts))
            
            # Создаем клавиатуру
            if transcripts:
                keyboard = self.create_history_keyboard(transcripts, page)
            else:
                keyboard = get_back_to_menu_keyboard()
            
            # Отправляем сообщение
            await self._send_message(message_or_call, text, keyboard, edit)
            
            logger.info(f"История успешно отправлена для пользователя {user_id}, страница {page}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке истории для пользователя {user_id}, страница {page}: {e}")
            # Отправляем сообщение об ошибке
            error_text = "📜 <b>История транскриптов</b>\n\nПроизошла ошибка при загрузке истории.\nПопробуйте позже."
            error_keyboard = get_back_to_menu_keyboard()
            await self._send_message(message_or_call, error_text, error_keyboard, edit)
    
    async def _send_message(
        self, 
        message_or_call: Union[Message, CallbackQuery], 
        text: str, 
        keyboard: InlineKeyboardMarkup, 
        edit: bool
    ) -> None:
        """
        Отправляет или редактирует сообщение
        
        Args:
            message_or_call: Объект сообщения или callback
            text: Текст сообщения
            keyboard: Клавиатура
            edit: Редактировать или отправить новое
        """
        try:
            if edit and hasattr(message_or_call, 'message') and message_or_call.message.text:
                # Пытаемся отредактировать существующее сообщение
                try:
                    await message_or_call.message.edit_text(
                        text, 
                        reply_markup=keyboard, 
                        parse_mode="HTML"
                    )
                    return
                except Exception as edit_error:
                    logger.warning(f"Не удалось отредактировать сообщение: {edit_error}")
                    # Если не удалось отредактировать, отправляем новое
                    await message_or_call.message.answer(
                        text, 
                        reply_markup=keyboard, 
                        parse_mode="HTML"
                    )
            else:
                # Отправляем новое сообщение
                await message_or_call.answer(
                    text, 
                    reply_markup=keyboard, 
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            raise
