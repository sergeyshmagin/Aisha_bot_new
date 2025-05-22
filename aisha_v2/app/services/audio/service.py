"""
LEGACY: Устаревший сервис обработки аудио. Используйте audio_processing.service.AudioService.
"""
# LEGACY: Этот модуль помечен как устаревший и подлежит удалению после миграции на audio_processing
import asyncio
from pathlib import Path
from typing import Optional, Union

import aiofiles
from aiogram.types import Audio, Voice
from pydantic import BaseModel

from aisha_v2.app.core.config import settings
from aisha_v2.app.core.logger import get_logger
from aisha_v2.app.services.storage import StorageService

logger = get_logger(__name__)

class AudioResult(BaseModel):
    """Результат обработки аудио"""
    file_id: str
    duration: int
    file_size: int
    mime_type: str
    file_path: Optional[str] = None
    transcript: Optional[str] = None

class AudioProcessingService:
    """
    LEGACY: Устаревший сервис. Используйте audio_processing.service.AudioService.
    Сервис для обработки аудио:
    - Конвертация в MP3
    - Транскрибация через Whisper
    - Сохранение в MinIO
    """

    def __init__(self):
        self.temp_dir = Path(settings.TEMP_DIR) / "audio"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def process_audio(
        self,
        audio: Union[Audio, Voice],
        user_id: int,
        bot
    ) -> AudioResult:
        """
        Обрабатывает аудио:
        1. Скачивает файл
        2. Конвертирует в MP3
        3. Транскрибирует
        4. Сохраняет в MinIO
        
        Args:
            audio: Аудио или голосовое сообщение
            user_id: ID пользователя
            bot: Объект бота
            
        Returns:
            AudioResult: Результат обработки
        """
        file_path = None
        mp3_path = None
        try:
            # 1. Скачиваем файл
            file_path = await self._download_audio(audio, bot)
            
            # 2. Конвертируем в MP3
            mp3_path = await self._convert_to_mp3(file_path)
            
            # 3. Транскрибируем
            transcript = await self._transcribe_audio(mp3_path)
            
            # 4. Сохраняем в MinIO
            storage = StorageService()
            with open(mp3_path, "rb") as f:
                data = f.read()
            object_name = f"{user_id}/{mp3_path.name}"
            await storage.upload_file(
                "audio",
                object_name,
                data,
                content_type="audio/mpeg"
            )
            minio_path = object_name
            
            return AudioResult(
                file_id=audio.file_id,
                duration=audio.duration,
                file_size=getattr(audio, 'file_size', 0),
                mime_type=getattr(audio, 'mime_type', ''),
                file_path=minio_path,
                transcript=transcript
            )
            
        except Exception as e:
            logger.exception("Ошибка при обработке аудио")
            raise
        finally:
            # Очищаем временные файлы, если они определены
            await self._cleanup_temp_files(*(p for p in [file_path, mp3_path] if p))

    async def _download_audio(self, audio: Union[Audio, Voice], bot) -> Path:
        """Скачивает аудио во временную директорию"""
        file_path = self.temp_dir / f"{audio.file_id}.ogg"
        tg_file = await bot.get_file(audio.file_id)
        file_bytes = await bot.download_file(tg_file.file_path)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes.read())
        return file_path

    async def _convert_to_mp3(self, file_path: Path) -> Path:
        """Конвертирует аудио в MP3"""
        mp3_path = file_path.with_suffix(".mp3")
        
        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i", str(file_path),
            "-vn",
            "-ar", "44100",
            "-ac", "2",
            "-b:a", "192k",
            str(mp3_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        await process.communicate()
        return mp3_path

    async def _transcribe_audio(self, file_path: Path) -> str:
        """Транскрибирует аудио через Whisper"""
        # TODO: Реализовать транскрибацию через Whisper
        return "Транскрипт будет доступен позже"

    async def _cleanup_temp_files(self, *file_paths: Path):
        """Удаляет временные файлы"""
        for path in file_paths:
            if path and path.exists():
                try:
                    path.unlink()
                except Exception as e:
                    logger.error(f"Ошибка при удалении {path}: {e}") 