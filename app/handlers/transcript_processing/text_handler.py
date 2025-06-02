"""
Обработчик текстовых файлов для транскриптов
Выделен из app/handlers/transcript_processing.py для соблюдения правила ≤500 строк
"""
import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.handlers.state import TranscribeStates
from app.core.di import (
    get_text_processing_service,
    get_transcript_service,
    get_user_service_with_session
)
from app.keyboards.transcript import get_back_to_menu_keyboard

logger = logging.getLogger(__name__)

class TextHandler:
    """Обработчик текстовых файлов для транскрипции"""
    
    def __init__(self, get_session_func):
        """
        Args:
            get_session_func: Функция для получения сессии БД
        """
        self.get_session = get_session_func
    
    async def handle_text_processing(self, message: Message, state: FSMContext) -> None:
        """
        Обработка текста из файла .txt
        
        Args:
            message: Входящее сообщение с текстовым файлом
            state: Контекст состояния FSM
        """
        logger.info(f"[TEXT] Получен файл от user_id={message.from_user.id}, state={await state.get_state()}")
        
        try:
            if not message.document:
                await message.reply(
                    "❌ Пожалуйста, отправьте текстовый файл",
                    reply_markup=get_back_to_menu_keyboard()
                )
                return
                
            # Валидация файла
            if not await self._validate_text_file(message):
                return
                
            processing_msg = await message.answer("📝 Обрабатываю текстовый файл...")
            await state.set_state(TranscribeStates.processing)

            # Скачиваем и читаем файл
            text, file_name = await self._download_and_read_file(message)
            
            if not text:
                await message.reply(
                    "❌ Не удалось прочитать содержимое файла",
                    reply_markup=get_back_to_menu_keyboard()
                )
                return

            # Обрабатываем текст
            processed_text = await self._process_text_content(text)
            
            # Сохраняем транскрипт
            transcript = await self._save_text_transcript(message, processed_text, text, file_name)
            
            if transcript:
                from .main_handler import TranscriptProcessingHandler
                handler = TranscriptProcessingHandler()
                await handler._send_transcript_result(message, transcript, processing_msg)
                await state.set_state(TranscribeStates.result)
            else:
                await message.reply(
                    "❌ Не удалось сохранить транскрипт",
                    reply_markup=get_back_to_menu_keyboard()
                )

        except Exception as e:
            logger.exception(f"[TEXT] Ошибка при обработке текста: {e}")
            await state.set_state(TranscribeStates.error)
            await message.reply(
                "❌ Произошла ошибка при обработке текста.\nПожалуйста, попробуйте еще раз.",
                reply_markup=get_back_to_menu_keyboard()
            )

    async def _validate_text_file(self, message: Message) -> bool:
        """Валидирует текстовый файл"""
        file_name = message.document.file_name or ""
        mime_type = message.document.mime_type or ""
        
        # Проверяем, что это текстовый файл
        if not (mime_type == "text/plain" or file_name.lower().endswith(".txt")):
            await message.reply(
                f"❌ **Неподдерживаемый формат текстового файла**\n\n"
                f"📁 Файл: {file_name}\n"
                f"🏷️ MIME тип: {mime_type}\n\n"
                f"✅ **Поддерживаемые форматы:**\n"
                f"📝 .txt файлы (text/plain)\n\n"
                f"💡 Отправьте файл с расширением .txt",
                parse_mode="Markdown",
                reply_markup=get_back_to_menu_keyboard()
            )
            return False
        
        return True

    async def _download_and_read_file(self, message: Message) -> tuple[str, str]:
        """Скачивает и читает содержимое текстового файла"""
        try:
            file = await message.bot.get_file(message.document.file_id)
            file_bytes_io = await message.bot.download_file(file.file_path)
            
            # Пытаемся прочитать как UTF-8
            try:
                text = file_bytes_io.read().decode("utf-8")
            except UnicodeDecodeError:
                # Если не получилось, пробуем другие кодировки
                file_bytes_io.seek(0)
                try:
                    text = file_bytes_io.read().decode("cp1251")
                except UnicodeDecodeError:
                    file_bytes_io.seek(0)
                    text = file_bytes_io.read().decode("latin-1")
            
            file_name = message.document.file_name or "text_file.txt"
            return text, file_name
            
        except Exception as e:
            logger.exception(f"[TEXT] Ошибка при скачивании файла: {e}")
            return "", ""

    async def _process_text_content(self, text: str) -> str:
        """Обрабатывает содержимое текста через text_service"""
        try:
            async with self.get_session() as session:
                text_service = get_text_processing_service(session)
                processed_text = await text_service.process_text(text)
                return processed_text
        except Exception as e:
            logger.exception(f"[TEXT] Ошибка при обработке текста: {e}")
            # Возвращаем оригинальный текст если обработка не удалась
            return text

    async def _save_text_transcript(self, message: Message, processed_text: str, original_text: str, file_name: str) -> dict:
        """Сохраняет текстовый транскрипт в БД"""
        try:
            async with self.get_session() as session:
                # Получаем или создаем пользователя
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
                        logger.error(f"[TEXT] Не удалось зарегистрировать пользователя: {message.from_user.id}")
                        return None

                # Сохраняем транскрипт
                transcript_service = get_transcript_service(session)
                transcript = await transcript_service.save_transcript(
                    user_id=user.id,
                    transcript_data=processed_text.encode('utf-8'),
                    metadata={
                        "source": "text",
                        "length": len(original_text),
                        "file_name": file_name,
                        "word_count": len(processed_text.split()) if processed_text else 0,
                        "file_size": len(original_text.encode('utf-8')),
                        "processing_method": "text_file"
                    }
                )
                
                return transcript
                
        except Exception as e:
            logger.exception(f"[TEXT] Ошибка при сохранении транскрипта: {e}")
            return None
