"""
AI форматирование транскриптов
Выделен из app/handlers/transcript_processing.py для соблюдения правила ≤500 строк
"""
import logging
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from app.handlers.state import TranscribeStates
from app.core.di import (
    get_text_processing_service,
    get_transcript_service,
    get_user_service_with_session
)
from app.keyboards.transcript import get_back_to_transcript_keyboard, get_back_to_menu_keyboard
from app.utils.uuid_utils import safe_uuid

logger = logging.getLogger(__name__)

class AIFormatter:
    """Обработчик AI форматирования транскриптов"""
    
    def __init__(self, get_session_func):
        """
        Args:
            get_session_func: Функция для получения сессии БД
        """
        self.get_session = get_session_func
    
    async def handle_transcript_actions(self, call: CallbackQuery, state: FSMContext) -> None:
        """
        Обработка действий с транскриптом: summary, todo, protocol
        """
        try:
            # Разбираем callback data: transcript_summary_<id>, transcript_todo_<id>, etc.
            parts = call.data.split("_", 2)
            if len(parts) < 3:
                await call.answer("❌ Неверный формат данных")
                return
            
            action = parts[1]  # summary, todo, protocol
            transcript_id = safe_uuid(parts[2])
            
            if not transcript_id:
                await call.answer("❌ Неверный ID транскрипта")
                return
            
            # Валидация действия
            if action not in ["summary", "todo", "protocol"]:
                await call.answer("❌ Неизвестное действие")
                return
            
            # Обработка форматирования через GPT
            await state.set_state(TranscribeStates.format_selection)
            processing_msg = await call.message.answer("⏳ Обрабатываю транскрипт с помощью GPT...")

            # Получаем и форматируем текст
            formatted_text, format_name, file_prefix = await self._process_transcript_formatting(
                call.from_user.id, transcript_id, action
            )
            
            if not formatted_text:
                await processing_msg.edit_text("❌ Не удалось обработать транскрипт")
                return

            # Отправляем результат как файл
            await self._send_formatted_result(
                call.message, processing_msg, formatted_text, 
                format_name, file_prefix, transcript_id
            )
            
            await state.set_state(TranscribeStates.result)

        except Exception as e:
            logger.exception(f"[ACTIONS] Ошибка при обработке действий транскрипта: {e}")
            await state.set_state(TranscribeStates.error)
            await call.message.answer(
                "❌ Произошла ошибка при обработке.\nПожалуйста, попробуйте еще раз.",
                reply_markup=get_back_to_menu_keyboard()
            )

    async def handle_transcript_format(self, call: CallbackQuery, state: FSMContext) -> None:
        """
        Обработка форматирования транскрипта (legacy метод)
        
        Args:
            call: CallbackQuery с данными о форматировании
            state: Контекст состояния FSM
        """
        try:
            # Получаем данные из callback
            data = call.data.split("_")
            if len(data) < 4:
                await call.answer("❌ Неверный формат данных")
                return

            transcript_id = safe_uuid(data[2])
            if not transcript_id:
                await call.answer("❌ Неверный ID транскрипта")
                return

            format_type = data[3]
            await state.set_state(TranscribeStates.format_selection)

            # Получаем и форматируем текст
            formatted_text, _, _ = await self._process_transcript_formatting(
                call.from_user.id, transcript_id, format_type
            )
            
            if not formatted_text:
                await call.answer("❌ Не удалось обработать транскрипт")
                return

            # Сохраняем отформатированный текст как новый транскрипт
            transcript = await self._save_formatted_transcript(
                call.from_user.id, formatted_text, transcript_id, format_type
            )

            if transcript:
                from .main_handler import TranscriptProcessingHandler
                handler = TranscriptProcessingHandler()
                await handler._send_transcript_result(call.message, transcript, None)
                await state.set_state(TranscribeStates.result)
            else:
                await call.message.reply(
                    "❌ Не удалось сохранить отформатированный транскрипт",
                    reply_markup=get_back_to_menu_keyboard()
                )

        except Exception as e:
            logger.exception(f"[FORMAT] Ошибка при форматировании транскрипта: {e}")
            await state.set_state(TranscribeStates.error)
            await call.message.reply(
                "❌ Произошла ошибка при форматировании.\n"
                "Пожалуйста, попробуйте еще раз.",
                reply_markup=get_back_to_menu_keyboard()
            )

    async def _process_transcript_formatting(self, user_telegram_id: int, transcript_id: str, action: str) -> tuple[str, str, str]:
        """
        Обрабатывает форматирование транскрипта через AI
        
        Returns:
            tuple: (formatted_text, format_name, file_prefix)
        """
        try:
            async with self.get_session() as session:
                # Получаем пользователя и транскрипт
                transcript_service = get_transcript_service(session)
                user_service = get_user_service_with_session(session)
                user = await user_service.get_user_by_telegram_id(user_telegram_id)
                
                if not user:
                    logger.error(f"[AI_FORMAT] Пользователь не найден: {user_telegram_id}")
                    return "", "", ""
                    
                content = await transcript_service.get_transcript_content(user.id, transcript_id)
                if not content:
                    logger.error(f"[AI_FORMAT] Не удалось получить текст транскрипта: {transcript_id}")
                    return "", "", ""

                text = content.decode('utf-8')
                text_service = get_text_processing_service(session)
                
                # Форматируем текст через AI
                if action == "summary":
                    formatted_text = await text_service.format_summary(text)
                    format_name = "Краткое содержание"
                    file_prefix = "summary"
                elif action == "todo":
                    formatted_text = await text_service.format_todo(text)
                    format_name = "Список задач"
                    file_prefix = "todo"
                elif action == "protocol":
                    formatted_text = await text_service.format_protocol(text)
                    format_name = "Протокол"
                    file_prefix = "protocol"
                else:
                    logger.error(f"[AI_FORMAT] Неизвестный формат: {action}")
                    return "", "", ""

                return formatted_text, format_name, file_prefix
                
        except Exception as e:
            logger.exception(f"[AI_FORMAT] Ошибка при обработке форматирования: {e}")
            return "", "", ""

    async def _send_formatted_result(self, message, processing_msg, formatted_text: str, 
                                   format_name: str, file_prefix: str, transcript_id: str) -> None:
        """Отправляет отформатированный результат как файл"""
        try:
            file_data = formatted_text.encode('utf-8')
            input_file = BufferedInputFile(file_data, filename=f"{file_prefix}_{transcript_id}.txt")
            
            await processing_msg.delete()
            await message.answer_document(
                document=input_file,
                caption=f"📄 {format_name}",
                reply_markup=get_back_to_transcript_keyboard(transcript_id)
            )
            
        except Exception as e:
            logger.exception(f"[AI_FORMAT] Ошибка при отправке результата: {e}")
            await processing_msg.edit_text("❌ Ошибка при отправке результата")

    async def _save_formatted_transcript(self, user_telegram_id: int, formatted_text: str, 
                                       original_transcript_id: str, format_type: str) -> dict:
        """Сохраняет отформатированный транскрипт как новый"""
        try:
            async with self.get_session() as session:
                transcript_service = get_transcript_service(session)
                
                formatted_transcript = await transcript_service.save_transcript(
                    user_id=user_telegram_id,
                    transcript_data=formatted_text.encode('utf-8'),
                    metadata={
                        "source": "format",
                        "original_id": str(original_transcript_id),
                        "format_type": format_type,
                        "word_count": len(formatted_text.split()) if formatted_text else 0,
                        "processing_method": "ai_formatting"
                    }
                )
                
                return formatted_transcript
                
        except Exception as e:
            logger.exception(f"[AI_FORMAT] Ошибка при сохранении отформатированного транскрипта: {e}")
            return None

    def get_format_display_name(self, format_type: str) -> str:
        """Возвращает отображаемое имя для типа форматирования"""
        format_names = {
            "summary": "Краткое содержание",
            "todo": "Список задач", 
            "protocol": "Протокол"
        }
        return format_names.get(format_type, format_type.title())

    def get_format_file_prefix(self, format_type: str) -> str:
        """Возвращает префикс файла для типа форматирования"""
        prefixes = {
            "summary": "summary",
            "todo": "todo",
            "protocol": "protocol"
        }
        return prefixes.get(format_type, format_type)
