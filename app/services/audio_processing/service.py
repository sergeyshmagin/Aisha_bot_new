"""
Основной сервис обработки аудио
"""
import logging
from typing import Optional
import tempfile
import os
import uuid
import asyncio

import aiofiles

from app.core.config import settings
from app.services.audio_processing.types import (
    AudioConverter,
    AudioRecognizer,
    AudioProcessor,
    AudioStorage,
    TranscribeResult
)
from app.core.exceptions.audio_exceptions import AudioProcessingError

logger = logging.getLogger(__name__)

class AudioService:
    """Основной сервис обработки аудио"""
    
    def __init__(
        self,
        converter: AudioConverter,
        recognizer: AudioRecognizer,
        processor: AudioProcessor,
        storage: AudioStorage
    ):
        self.converter = converter
        self.recognizer = recognizer
        self.processor = processor
        self.storage = storage
    
    async def process_audio(
        self,
        audio_data: bytes,
        language: str = "ru",
        save_original: bool = True,
        normalize: bool = True,
        remove_silence: bool = True
    ) -> TranscribeResult:
        """
        Обрабатывает аудио и транскрибирует его (через ffmpeg, как в v1)
        """
        try:
            logger.info("[AudioService] Начало process_audio (ffmpeg pipeline)")
            
            # Диагностика входных данных
            logger.info(f"[AudioService] Размер входных данных: {len(audio_data)} байт")
            if len(audio_data) >= 12:
                header = audio_data[:12]
                logger.info(f"[AudioService] Заголовок файла: {header.hex()}")
                
                # Попытка определить формат
                if header.startswith(b'ID3') or (header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
                    detected_format = "MP3"
                elif header.startswith(b'RIFF'):
                    detected_format = "WAV"
                elif b'ftyp' in header or header[4:8] == b'ftyp':
                    detected_format = "M4A/MP4"
                elif header.startswith(b'OggS'):
                    detected_format = "OGG"
                elif header.startswith(b'fLaC'):
                    detected_format = "FLAC"
                else:
                    detected_format = "UNKNOWN"
                
                logger.info(f"[AudioService] Определен формат: {detected_format}")
            
            # Используем правильный путь для контейнера
            temp_dir = "/app/storage/temp"
            await asyncio.get_event_loop().run_in_executor(None, os.makedirs, temp_dir, True)
            ogg_path = os.path.join(temp_dir, f"{uuid.uuid4()}.ogg")
            mp3_path = os.path.join(temp_dir, f"{uuid.uuid4()}.mp3")
            
            # 1. Сохраняем исходный файл в storage/temp асинхронно
            async with aiofiles.open(ogg_path, "wb") as f:
                await f.write(audio_data)
            
            try:
                # 2. Конвертируем в mp3 через ffmpeg
                logger.info(f"[AudioService] Конвертация {ogg_path} в mp3 через ffmpeg")
                mp3_bytes = await self.converter.convert_to_mp3(audio_data, use_ffmpeg=True)
                async with aiofiles.open(mp3_path, "wb") as f:
                    await f.write(mp3_bytes)
                logger.info(f"[AudioService] mp3-файл создан: {mp3_path}")
                
                # 3. Разбиваем mp3 на чанки через ffmpeg
                logger.info(f"[AudioService] Нарезка {mp3_path} на чанки через ffmpeg")
                chunks = await self.processor.split_audio(mp3_bytes, use_ffmpeg=True)
                logger.info(f"[AudioService] Получено чанков: {len(chunks)}")
                
                if not chunks:
                    logger.error(f"[AudioService] Не удалось нарезать аудио на чанки. mp3_path={mp3_path}")
                    raise AudioProcessingError(f"Не удалось нарезать аудио на чанки. mp3_path={mp3_path}")
                
                # 4. Транскрибируем каждый chunk
                texts = []
                for idx, chunk in enumerate(chunks):
                    logger.info(f"[AudioService] Транскрибация чанка {idx+1}/{len(chunks)}")
                    result = await self.recognizer.transcribe_chunk(chunk, language)
                    if result.success:
                        texts.append(result.text)
                    else:
                        logger.warning(f"[AudioService] Ошибка транскрибации чанка {idx+1}: {result.error}")
                
                final_text = "\n".join(texts)
                success = bool(texts)
                
                if success:
                    logger.info(f"[AudioService] ✅ Транскрибация успешна: {len(texts)} чанков, общая длина текста: {len(final_text)} символов")
                    return TranscribeResult(success=True, text=final_text, error=None)
                else:
                    error_msg = f"Не удалось транскрибировать ни одного чанка из {len(chunks)}"
                    logger.error(f"[AudioService] ❌ {error_msg}")
                    return TranscribeResult(success=False, text="", error=error_msg)
            finally:
                # Асинхронное удаление временных файлов
                if await asyncio.get_event_loop().run_in_executor(None, os.path.exists, ogg_path):
                    await asyncio.get_event_loop().run_in_executor(None, os.unlink, ogg_path)
                if await asyncio.get_event_loop().run_in_executor(None, os.path.exists, mp3_path):
                    await asyncio.get_event_loop().run_in_executor(None, os.unlink, mp3_path)
                    
        except Exception as e:
            logger.error(f"[AudioService] Ошибка при обработке аудио (ffmpeg pipeline): {e}", exc_info=True)
            raise AudioProcessingError(f"Ошибка обработки: {str(e)}")
    
    async def transcribe_file(
        self,
        filename: str,
        language: str = "ru",
        normalize: bool = True,
        remove_silence: bool = True
    ) -> TranscribeResult:
        """
        Транскрибирует аудио файл
        
        Args:
            filename: Имя файла
            language: Язык аудио
            normalize: Нормализовать ли громкость
            remove_silence: Удалять ли тишину
            
        Returns:
            TranscribeResult: Результат транскрибации
            
        Raises:
            AudioProcessingError: При ошибке транскрибации
        """
        try:
            # Загружаем файл
            audio_data = await self.storage.load(filename)
            logger.info(f"Файл загружен: {filename}")
            
            # Обрабатываем и транскрибируем
            return await self.process_audio(
                audio_data,
                language,
                save_original=False,
                normalize=normalize,
                remove_silence=remove_silence
            )
            
        except Exception as e:
            logger.error(f"Ошибка при транскрибации файла: {e}")
            raise AudioProcessingError(f"Ошибка транскрибации: {str(e)}")
    
    async def cleanup(self, max_age_days: int = 7):
        """
        Очищает старые файлы
        
        Args:
            max_age_days: Максимальный возраст файлов в днях
            
        Raises:
            AudioProcessingError: При ошибке очистки
        """
        try:
            await self.storage.cleanup_old_files(max_age_days)
            logger.info(f"Очистка старых файлов завершена (max_age_days={max_age_days})")
        except Exception as e:
            logger.error(f"Ошибка при очистке старых файлов: {e}")
            raise AudioProcessingError(f"Ошибка очистки: {str(e)}")

    async def summarize_text(self, text: str) -> str:
        """Генерирует краткое содержание транскрипта (summary)."""
        # TODO: Интеграция с ML/AI-сервисом для саммари
        return "[Краткое содержание будет доступно позже]"

    async def create_bullet_points(self, text: str) -> str:
        """Генерирует список задач/ключевых моментов (todo)."""
        # TODO: Интеграция с ML/AI-сервисом для bullet points
        return "[Список задач будет доступен позже]"

    async def generate_protocol(self, text: str) -> str:
        """Генерирует протокол встречи/разговора."""
        # TODO: Интеграция с ML/AI-сервисом для протокола
        return "[Протокол будет доступен позже]" 