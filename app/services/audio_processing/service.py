"""
Основной сервис обработки аудио
"""
import logging
from typing import Optional
import tempfile
import os
import uuid

from app.core.config import settings
from app.services.audio_processing.types import (
    AudioConverter,
    AudioRecognizer,
    AudioProcessor,
    AudioStorage,
    TranscribeResult
)
from app.core.exceptions import AudioProcessingError

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
            temp_dir = os.path.join(os.getcwd(), "storage", "temp")
            os.makedirs(temp_dir, exist_ok=True)
            ogg_path = os.path.join(temp_dir, f"{uuid.uuid4()}.ogg")
            mp3_path = os.path.join(temp_dir, f"{uuid.uuid4()}.mp3")
            # 1. Сохраняем исходный файл в storage/temp
            with open(ogg_path, "wb") as f:
                f.write(audio_data)
            try:
                # 2. Конвертируем в mp3 через ffmpeg
                logger.info(f"[AudioService] Конвертация {ogg_path} в mp3 через ffmpeg")
                mp3_bytes = await self.converter.convert_to_mp3(audio_data, use_ffmpeg=True)
                with open(mp3_path, "wb") as f:
                    f.write(mp3_bytes)
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
                logger.info(f"[AudioService] Итоговая транскрибация: success={success}, чанков={len(chunks)}")
                return TranscribeResult(success=success, text=final_text, error=None if success else "transcribe_error")
            finally:
                if os.path.exists(ogg_path):
                    os.unlink(ogg_path)
                if os.path.exists(mp3_path):
                    os.unlink(mp3_path)
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