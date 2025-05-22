from typing import Optional
from aiogram import Bot, Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aisha_v2.app.core.logger import logger
from aisha_v2.app.services.audio.service import AudioProcessingService
from aisha_v2.app.texts.audio_errors import (
    AUDIO_PROCESSING_ERROR,
    AUDIO_PROCESSING_START,
    AUDIO_PROCESSING_DONE
)
from aisha_v2.app.services.storage.minio import MinioStorage

# Определяем состояния FSM
class AudioStates(StatesGroup):
    waiting_for_audio = State()

# Создаем роутер
router = Router()

class AudioHandler:
    def __init__(
        self,
        bot: Bot,
        audio_service: AudioProcessingService,
        minio_storage: MinioStorage
    ):
        self.bot = bot
        self.audio_service = audio_service
        self.minio_storage = minio_storage

    async def handle_audio_start(self, message: Message, state: FSMContext) -> None:
        """Включает режим ожидания аудиофайла."""
        try:
            await state.set_state(AudioStates.waiting_for_audio)
            await message.answer(
                "Пожалуйста, отправьте аудиофайл (mp3/ogg) для расшифровки."
            )
        except Exception as e:
            logger.exception(f"[handle_audio_start] Ошибка: {e}")
            await message.answer(
                "Ошибка при переходе в режим аудио. Пожалуйста, попробуйте ещё раз."
            )

    async def handle_audio(self, message: Message, state: FSMContext) -> None:
        """Обрабатывает аудиофайлы и голосовые сообщения."""
        # Проверяем состояние
        current_state = await state.get_state()
        if current_state != AudioStates.waiting_for_audio:
            await message.answer(
                "Пожалуйста, сначала выберите режим 'Аудио' в меню (кнопка 🎤 Аудио)."
            )
            return

        # Проверяем тип сообщения
        if not (message.voice or message.audio):
            await message.answer(
                "Пожалуйста, отправьте голосовое сообщение или аудиофайл."
            )
            return

        # Отправляем сообщение о начале обработки
        status_message = await message.answer(AUDIO_PROCESSING_START)

        try:
            # Обрабатываем аудио
            success, error, transcript_path = await self.audio_service.process_audio(
                message=message,
                bot=self.bot,
                user_id=str(message.from_user.id)
            )

            if not success:
                error_msg = AUDIO_PROCESSING_ERROR
                if error == "file_too_large":
                    error_msg = "❌ Файл слишком большой. Максимальный размер: 20 МБ."
                elif error == "ffmpeg_not_found":
                    error_msg = "❌ Ошибка: ffmpeg не установлен или недоступен."
                elif error == "unsupported_format":
                    error_msg = "❌ Неподдерживаемый формат аудио."
                
                await status_message.edit_text(error_msg)
                return

            # Отправляем транскрипт
            if transcript_path:
                with open(transcript_path, "r", encoding="utf-8") as f:
                    transcript_text = f.read()
                
                # Отправляем файл
                await message.answer_document(
                    document=FSInputFile(transcript_path),
                    caption=AUDIO_PROCESSING_DONE.format(
                        snippet=transcript_text[:200]
                    )
                )

        except Exception as e:
            logger.exception(f"[handle_audio] Ошибка: {e}")
            await status_message.edit_text(AUDIO_PROCESSING_ERROR)
            
        finally:
            # Сбрасываем состояние
            await state.clear()

# Регистрируем хендлеры
def register_handlers(handler: AudioHandler):
    router.message.register(
        handler.handle_audio_start,
        Command("audio")
    )
    router.message.register(
        handler.handle_audio,
        StateFilter(AudioStates.waiting_for_audio),
        F.voice | F.audio
    ) 