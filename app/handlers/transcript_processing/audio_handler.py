"""
Обработчик аудио для транскриптов
Выделен из app/handlers/transcript_processing.py для соблюдения правила ≤500 строк
"""
import logging
from typing import Optional
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.core.config import settings
from app.handlers.state import TranscribeStates
from app.core.di import (
    get_audio_processing_service,
    get_user_service_with_session,
    get_transcript_service
)

logger = logging.getLogger(__name__)

class AudioHandler:
    """Обработчик аудио файлов для транскрипции"""
    
    def __init__(self, get_session_func):
        """
        Args:
            get_session_func: Функция для получения сессии БД
        """
        self.get_session = get_session_func
    
    async def handle_audio_universal(self, message: Message, state: FSMContext) -> None:
        """
        Универсальный обработчик аудио и голосовых сообщений.
        Работает в любом состоянии и автоматически начинает обработку.
        
        Args:
            message: Входящее сообщение с аудио
            state: Контекст состояния FSM
        """
        current_state = await state.get_state()
        logger.info(f"[AUDIO_UNIVERSAL] Получено аудио/voice от user_id={message.from_user.id}, current_state={current_state}")
        
        # Если уже в процессе обработки, пропускаем
        if current_state in [TranscribeStates.processing, TranscribeStates.result]:
            logger.info(f"[AUDIO_UNIVERSAL] Пользователь уже в процессе обработки, пропускаем")
            return
            
        # Начинаем обработку
        logger.info(f"[AUDIO_UNIVERSAL] Начинаем обработку аудио")
        
        # Выполняем обработку аудио напрямую
        try:
            processing_msg = await message.answer("🎵 Начинаю обработку аудио...")
            await state.set_state(TranscribeStates.processing)

            # Извлекаем информацию о файле
            file_info = self._extract_file_info(message)
            
            # Проверяем размер файла
            if not await self._validate_file_size(message, file_info, processing_msg, state):
                return
            
            # Обрабатываем файл
            transcript_text = await self._process_audio_file(message, file_info, processing_msg)
            
            if transcript_text:
                # Сохраняем результат
                transcript = await self._save_transcript(message, transcript_text, file_info)
                
                if transcript and transcript.get("transcript_key"):
                    from .main_handler import TranscriptProcessingHandler
                    handler = TranscriptProcessingHandler()
                    await handler._send_transcript_result(message, transcript, processing_msg)
                    await state.set_state(TranscribeStates.result)
                    return
            
            # Если что-то пошло не так
            await message.reply("❌ Не удалось обработать аудио файл")
            await state.set_state(TranscribeStates.error)
                
        except Exception as e:
            logger.exception(f"[AUDIO_UNIVERSAL] Ошибка обработки аудио: {e}")
            await message.reply("❌ Произошла ошибка при обработке аудио")
            await state.set_state(TranscribeStates.error)

    def _extract_file_info(self, message: Message) -> dict:
        """Извлекает информацию о файле из сообщения"""
        if message.voice:
            return {
                "file_id": message.voice.file_id,
                "duration": message.voice.duration,
                "file_name": f"voice_{message.message_id}.ogg",
                "file_size": message.voice.file_size,
                "file_format": "ogg",
                "source_type": "voice"
            }
        else:
            return {
                "file_id": message.audio.file_id,
                "duration": message.audio.duration,
                "file_name": message.audio.file_name or f"audio_{message.message_id}.mp3",
                "file_size": message.audio.file_size,
                "file_format": self._extract_audio_format(message.audio.file_name, message.audio.mime_type),
                "source_type": "audio"
            }

    async def _validate_file_size(self, message: Message, file_info: dict, processing_msg: Message, state: FSMContext) -> bool:
        """Проверяет размер файла и возвращает True если файл можно обработать"""
        file_size = file_info.get("file_size")
        max_file_size = settings.MAX_AUDIO_SIZE  # 1GB
        
        if file_size and file_size > max_file_size:
            logger.warning(f"[AUDIO_UNIVERSAL] Файл слишком большой: {file_size} байт (лимит: {max_file_size})")
            await message.reply(
                f"❌ **Файл слишком большой**\n\n"
                f"Размер файла: {file_size / (1024*1024):.1f} МБ\n"
                f"Максимальный размер: {max_file_size / (1024*1024*1024)} ГБ\n\n"
                f"Пожалуйста, отправьте файл меньшего размера.",
                parse_mode="Markdown"
            )
            await state.set_state(TranscribeStates.error)
            return False
        
        return True

    async def _process_audio_file(self, message: Message, file_info: dict, processing_msg: Message) -> Optional[str]:
        """Обрабатывает аудио файл и возвращает транскрипт"""
        file_size = file_info.get("file_size")
        telegram_api_limit = settings.TELEGRAM_API_LIMIT  # 20MB
        
        if file_size and file_size > telegram_api_limit:
            return await self._process_large_audio(message, file_info, processing_msg)
        else:
            return await self._process_regular_audio(message, file_info)

    async def _process_large_audio(self, message: Message, file_info: dict, processing_msg: Message) -> Optional[str]:
        """Обрабатывает большие аудио файлы через специальный алгоритм"""
        file_size = file_info["file_size"]
        telegram_api_limit = settings.TELEGRAM_API_LIMIT
        
        logger.info(f"[AUDIO_UNIVERSAL] Большой файл ({file_size} байт), пытаемся обработать автоматически")
        
        # Обновляем сообщение о попытке обработки
        await processing_msg.edit_text(
            f"📁 **Большой файл обнаружен**\n\n"
            f"📊 Размер: {file_size / (1024*1024):.1f} МБ\n"
            f"📏 Лимит Bot API: {telegram_api_limit / (1024*1024):.0f} МБ\n\n"
            f"🧠 **Умная обработка:**\n"
            f"• Анализирую паузы в аудио\n"
            f"• Разделяю на оптимальные части\n"
            f"• Добавляю перекрытия для контекста\n"
            f"⏳ Это займет несколько минут...",
            parse_mode="Markdown"
        )
        
        try:
            from app.services.large_audio_processor import try_process_large_audio
            
            # Получаем токен бота
            bot_token = message.bot.token
            
            # Пытаемся получить file_path
            file_path = None
            try:
                file = await message.bot.get_file(file_info["file_id"])
                file_path = file.file_path
                logger.info(f"[AUDIO_UNIVERSAL] Получен file_path для большого файла")
            except Exception as e:
                logger.warning(f"[AUDIO_UNIVERSAL] Не удалось получить file_path: {e}")
            
            # Обновляем прогресс
            await processing_msg.edit_text(
                f"📁 **Большой файл обнаружен**\n\n"
                f"📊 Размер: {file_size / (1024*1024):.1f} МБ\n"
                f"🤖 **Запускаю умный алгоритм обработки...**\n"
                f"🔄 Скачиваю и анализирую структуру аудио\n"
                f"⚡ Разбиваю на части по естественным паузам",
                parse_mode="Markdown"
            )
            
            # Получаем audio_service
            async with self.get_session() as session:
                audio_service = get_audio_processing_service(session)
                
                # Обрабатываем через специальный сервис
                transcript_text = await try_process_large_audio(
                    bot_token=bot_token,
                    file_id=file_info["file_id"],
                    file_path=file_path,
                    file_size=file_size,
                    audio_service=audio_service
                )
            
            if transcript_text:
                logger.info(f"[AUDIO_UNIVERSAL] Большой файл успешно обработан: {len(transcript_text)} символов")
                
                # Обновляем сообщение о завершении
                await processing_msg.edit_text(
                    f"✅ **Большой файл успешно обработан!**\n\n"
                    f"📊 Размер: {file_size / (1024*1024):.1f} МБ\n"
                    f"📝 Получен транскрипт: {len(transcript_text)} символов\n"
                    f"🧹 Временные файлы очищены\n"
                    f"💾 Сохраняю результат...",
                    parse_mode="Markdown"
                )
                
                return transcript_text
            
        except Exception as e:
            logger.exception(f"[AUDIO_UNIVERSAL] Ошибка при специальной обработке большого файла: {e}")
        
        # Если не удалось обработать
        await processing_msg.edit_text(
            f"❌ **Не удалось обработать большой файл автоматически**\n\n"
            f"📊 **Размер файла:** {file_size / (1024*1024):.1f} МБ\n"
            f"📏 **Лимит Bot API:** {telegram_api_limit / (1024*1024):.0f} МБ\n\n"
            f"🔧 **Возможные решения:**\n"
            f"• Сохраните файл на устройство и отправьте как документ (📎 → Файл)\n"
            f"• Разделите файл на части меньше {telegram_api_limit / (1024*1024):.0f} МБ\n"
            f"• Сожмите аудио до меньшего размера\n\n"
            f"💡 **Для пересланных файлов:** скачайте файл и отправьте заново как документ",
            parse_mode="Markdown"
        )
        
        return None

    async def _process_regular_audio(self, message: Message, file_info: dict) -> Optional[str]:
        """Обрабатывает обычные аудио файлы (≤20MB)"""
        try:
            # Обычное скачивание для файлов <= 20MB
            file = await message.bot.get_file(file_info["file_id"])
            downloaded_file = await message.bot.download_file(file.file_path)

            # Транскрибируем
            async with self.get_session() as session:
                audio_service = get_audio_processing_service(session)
                logger.info(f"[AUDIO_UNIVERSAL] Обрабатываем {file_info['file_format']} файл: {file_info['file_name']}")
                result = await audio_service.process_audio(downloaded_file.getvalue())
                
                if not result.success:
                    logger.error(f"[AUDIO_UNIVERSAL] Ошибка транскрибации: {result.error}")
                    return None
                
                text = result.text
                logger.info(f"[AUDIO_UNIVERSAL] Получен текст транскрипта, длина: {len(text)}")
                return text
                
        except Exception as e:
            logger.exception(f"[AUDIO_UNIVERSAL] Ошибка обработки обычного аудио: {e}")
            return None

    async def _save_transcript(self, message: Message, transcript_text: str, file_info: dict) -> Optional[dict]:
        """Сохраняет транскрипт в БД"""
        try:
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
                        logger.error(f"[AUDIO_UNIVERSAL] Не удалось зарегистрировать пользователя: {message.from_user.id}")
                        return None

                transcript_service = get_transcript_service(session)
                transcript = await transcript_service.save_transcript(
                    user_id=user.id,
                    transcript_data=transcript_text.encode('utf-8'),
                    metadata={
                        "source": file_info["source_type"],
                        "duration": file_info.get("duration"),
                        "file_id": file_info["file_id"],
                        "file_name": file_info["file_name"],
                        "file_size": file_info.get("file_size"),
                        "word_count": len(transcript_text.split()) if transcript_text else 0,
                        "processing_method": "large_file" if file_info.get("file_size", 0) > settings.TELEGRAM_API_LIMIT else "regular"
                    }
                )
                
                return transcript
                
        except Exception as e:
            logger.exception(f"[AUDIO_UNIVERSAL] Ошибка сохранения транскрипта: {e}")
            return None

    def _extract_audio_format(self, file_name: Optional[str], mime_type: Optional[str]) -> str:
        """Определяет формат аудио файла по имени или MIME типу"""
        if file_name:
            # Извлекаем расширение из имени файла
            if '.' in file_name:
                extension = file_name.split('.')[-1].lower()
                if extension in settings.AUDIO_FORMATS:
                    return extension
        
        if mime_type:
            # Определяем по MIME типу
            mime_to_format = {
                "audio/mpeg": "mp3",
                "audio/mp3": "mp3", 
                "audio/wav": "wav",
                "audio/wave": "wav",
                "audio/x-wav": "wav",
                "audio/ogg": "ogg",
                "audio/opus": "opus",
                "audio/mp4": "m4a",
                "audio/x-m4a": "m4a",
                "audio/aac": "aac",
                "audio/flac": "flac",
                "audio/x-flac": "flac"
            }
            return mime_to_format.get(mime_type, "mp3")
        
        # По умолчанию MP3
        return "mp3"

    async def handle_audio_document(self, message: Message, state: FSMContext) -> None:
        """
        Обработчик аудио файлов, отправленных как документы.
        Проверяет формат и перенаправляет на обработку аудио.
        """
        current_state = await state.get_state()
        logger.info(f"[AUDIO_DOCUMENT] Получен документ от user_id={message.from_user.id}, current_state={current_state}")
        
        # Если уже в процессе обработки, пропускаем
        if current_state in [TranscribeStates.processing, TranscribeStates.result]:
            logger.info(f"[AUDIO_DOCUMENT] Пользователь уже в процессе обработки, пропускаем")
            return
        
        # Если ожидаем текстовый файл, пропускаем (обработает text_handler)
        if current_state == TranscribeStates.waiting_text:
            logger.info(f"[AUDIO_DOCUMENT] Ожидается текстовый файл, пропускаем аудио документ")
            return
        
        # Проверяем, является ли документ аудио файлом
        file_name = message.document.file_name or ""
        mime_type = message.document.mime_type or ""
        
        # Определяем формат файла
        file_format = self._extract_audio_format(file_name, mime_type)
        
        # Проверяем, поддерживается ли формат
        if file_format not in settings.AUDIO_FORMATS and not mime_type.startswith("audio/"):
            logger.info(f"[AUDIO_DOCUMENT] Документ не является аудио файлом: {file_name}, mime: {mime_type}")
            return
        
        logger.info(f"[AUDIO_DOCUMENT] Обнаружен аудио документ: {file_name} ({file_format})")
        
        # Создаем псевдо-аудио объект для совместимости с handle_audio_universal
        class AudioDocument:
            def __init__(self, document):
                self.file_id = document.file_id
                self.duration = None  # Документы не содержат информацию о длительности
                self.file_name = document.file_name
                self.file_size = document.file_size
                self.mime_type = document.mime_type
        
        # Временно заменяем message.audio на наш объект
        original_audio = getattr(message, 'audio', None)
        message.audio = AudioDocument(message.document)
        
        try:
            # Обрабатываем как обычное аудио
            await self.handle_audio_universal(message, state)
        finally:
            # Восстанавливаем оригинальное значение
            if original_audio:
                message.audio = original_audio
            else:
                delattr(message, 'audio') 