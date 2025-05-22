"""
Модуль для распознавания речи
"""
import asyncio
import logging
import tempfile
from typing import Optional
from pathlib import Path

import aiohttp
from aisha_v2.app.core.config import settings
from aisha_v2.app.services.audio_processing.types import AudioRecognizer, TranscribeResult, AudioMetadata
from aisha_v2.app.core.exceptions import AudioProcessingError

logger = logging.getLogger(__name__)

class WhisperRecognizer(AudioRecognizer):
    """Распознаватель речи на основе OpenAI Whisper"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.api_url = "https://api.openai.com/v1/audio/transcriptions"
        self.max_retries = 3
        self.retry_delay = 1.0
    
    async def transcribe(self, audio_data: bytes, language: str = "ru") -> TranscribeResult:
        """
        Транскрибирует аудио в текст
        
        Args:
            audio_data: Аудио данные
            language: Язык аудио
            
        Returns:
            TranscribeResult: Результат транскрибации
            
        Raises:
            AudioProcessingError: При ошибке транскрибации
        """
        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp:
                temp.write(audio_data)
                temp_path = temp.name
            
            # Получаем метаданные
            metadata = await self._get_metadata(audio_data)
            
            # Если файл слишком большой, разбиваем на части
            if metadata.duration > 300:  # 5 минут
                logger.info(f"Аудио слишком длинное ({metadata.duration} сек), разбиваем на части")
                return await self._transcribe_large_file(temp_path, language)
            
            # Транскрибируем файл
            async with aiohttp.ClientSession() as session:
                for attempt in range(self.max_retries):
                    try:
                        async with session.post(
                            self.api_url,
                            headers={
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "multipart/form-data"
                            },
                            data={
                                "file": open(temp_path, "rb"),
                                "model": "whisper-1",
                                "language": language,
                                "response_format": "json"
                            }
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                return TranscribeResult(
                                    success=True,
                                    text=result["text"],
                                    metadata=metadata
                                )
                            elif response.status == 429:  # Rate limit
                                if attempt < self.max_retries - 1:
                                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                                    continue
                            else:
                                error_text = await response.text()
                                raise AudioProcessingError(
                                    f"Ошибка API: {response.status} - {error_text}"
                                )
                    except aiohttp.ClientError as e:
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue
                        raise AudioProcessingError(f"Ошибка сети: {str(e)}")
            
            return TranscribeResult(
                success=False,
                error="max_retries_exceeded"
            )
            
        except Exception as e:
            logger.error(f"Ошибка при транскрибации: {e}")
            return TranscribeResult(
                success=False,
                error=str(e)
            )
            
        finally:
            try:
                Path(temp_path).unlink()
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {temp_path}: {e}")
    
    async def transcribe_chunk(self, audio_data: bytes, language: str = "ru") -> TranscribeResult:
        """
        Транскрибирует часть аудио
        
        Args:
            audio_data: Аудио данные
            language: Язык аудио
            
        Returns:
            TranscribeResult: Результат транскрибации
            
        Raises:
            AudioProcessingError: При ошибке транскрибации
        """
        return await self.transcribe(audio_data, language)
    
    async def _get_metadata(self, audio_data: bytes) -> AudioMetadata:
        """
        Получает метаданные аудио
        
        Args:
            audio_data: Аудио данные
            
        Returns:
            AudioMetadata: Метаданные аудио
        """
        # TODO: Реализовать получение метаданных
        return AudioMetadata(
            duration=0.0,
            format="mp3",
            sample_rate=44100,
            channels=2,
            bitrate=192000,
            created_at=datetime.now()
        )
    
    async def _transcribe_large_file(self, file_path: str, language: str) -> TranscribeResult:
        """
        Транскрибирует большой файл по частям
        
        Args:
            file_path: Путь к файлу
            language: Язык аудио
            
        Returns:
            TranscribeResult: Результат транскрибации
        """
        # TODO: Реализовать разбиение на части и транскрибацию
        raise NotImplementedError("Метод не реализован") 