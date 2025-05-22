"""
Основной сервис обработки аудио
"""
import logging
from typing import Optional

from aisha_v2.app.core.config import settings
from aisha_v2.app.services.audio_processing.types import (
    AudioConverter,
    AudioRecognizer,
    AudioProcessor,
    AudioStorage,
    TranscribeResult
)
from aisha_v2.app.core.exceptions import AudioProcessingError

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
        Обрабатывает аудио и транскрибирует его
        
        Args:
            audio_data: Аудио данные
            language: Язык аудио
            save_original: Сохранять ли оригинальный файл
            normalize: Нормализовать ли громкость
            remove_silence: Удалять ли тишину
            
        Returns:
            TranscribeResult: Результат транскрибации
            
        Raises:
            AudioProcessingError: При ошибке обработки
        """
        try:
            # Сохраняем оригинальный файл, если нужно
            original_path = None
            if save_original:
                original_path = await self.storage.save(audio_data)
                logger.info(f"Оригинальный файл сохранен: {original_path}")
            
            # Конвертируем в MP3
            audio_data = await self.converter.convert_to_mp3(audio_data)
            logger.info("Аудио конвертировано в MP3")
            
            # Нормализуем громкость, если нужно
            if normalize:
                audio_data = await self.processor.normalize_audio(audio_data)
                logger.info("Громкость нормализована")
            
            # Удаляем тишину, если нужно
            if remove_silence:
                audio_data = await self.processor.remove_silence(audio_data)
                logger.info("Тишина удалена")
            
            # Транскрибируем
            result = await self.recognizer.transcribe(audio_data, language)
            
            # Если транскрибация успешна, сохраняем обработанный файл
            if result.success:
                processed_path = await self.storage.save(audio_data)
                logger.info(f"Обработанный файл сохранен: {processed_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при обработке аудио: {e}")
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