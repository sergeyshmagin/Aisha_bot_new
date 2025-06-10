"""
Модуль для распознавания речи
"""
import asyncio
import logging
import tempfile
from typing import Optional
from pathlib import Path
from datetime import datetime
import io

import aiohttp
from app.core.temp_files import NamedTemporaryFile
from app.core.config import settings
from app.services.audio_processing.types import AudioRecognizer, TranscribeResult, AudioMetadata
from app.core.exceptions.audio_exceptions import AudioProcessingError

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
            with NamedTemporaryFile(suffix='.mp3', delete=False) as temp:
                temp.write(audio_data)
                temp_path = temp.name
            
            # Получаем метаданные
            metadata = await self._get_metadata(audio_data)
            
            # Если файл слишком большой, разбиваем на части
            if metadata.duration > 300:  # 5 минут
                logger.info(f"Аудио слишком длинное ({metadata.duration} сек), разбиваем на части")
                return await self._transcribe_large_file(temp_path, language)
            
            # Транскрибируем файл
            timeout = aiohttp.ClientTimeout(total=60.0)  # 60 секунд общий таймаут
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for attempt in range(self.max_retries):
                    try:
                        form = aiohttp.FormData()
                        form.add_field(
                            "file",
                            io.BytesIO(audio_data),
                            filename="audio.mp3",
                            content_type="audio/mpeg"
                        )
                        form.add_field("model", "whisper-1")
                        form.add_field("language", language)
                        form.add_field("response_format", "json")
                        
                        logger.info(f"[Whisper] Отправка запроса к OpenAI API (попытка {attempt + 1}/{self.max_retries})")
                        
                        async with session.post(
                            self.api_url,
                            headers={"Authorization": f"Bearer {self.api_key}"},
                            data=form
                        ) as response:
                            logger.info(f"[Whisper] Получен ответ от OpenAI API: status={response.status}")
                            
                            if response.status == 200:
                                result = await response.json()
                                logger.info(f"[Whisper] Успешная транскрибация, длина текста: {len(result['text'])} символов")
                                return TranscribeResult(
                                    success=True,
                                    text=result["text"],
                                    metadata=metadata
                                )
                            elif response.status == 429:  # Rate limit
                                logger.warning(f"[Whisper] Rate limit (429), ждем {self.retry_delay * (attempt + 1)} секунд")
                                if attempt < self.max_retries - 1:
                                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                                    continue
                            else:
                                error_text = await response.text()
                                logger.error(f"[Whisper] Ошибка API: {response.status} - {error_text}")
                                raise AudioProcessingError(
                                    f"Ошибка API: {response.status} - {error_text}"
                                )
                    except asyncio.TimeoutError:
                        logger.error(f"[Whisper] Таймаут при запросе к OpenAI API (попытка {attempt + 1})")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue
                        raise AudioProcessingError("Таймаут при запросе к OpenAI API")
                    except aiohttp.ClientError as e:
                        logger.error(f"[Whisper] Ошибка сети (попытка {attempt + 1}): {e}")
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
        """
        from app.services.audio_processing.processor import AudioProcessor
        import aiofiles
        logger.info(f"[WhisperRecognizer] Начинаю разбиение большого файла: {file_path}")
        # Читаем байты файла
        async with aiofiles.open(file_path, 'rb') as f:
            audio_data = await f.read()
        processor = AudioProcessor()
        try:
            chunks = await processor.split_audio(audio_data)
            logger.info(f"[WhisperRecognizer] Файл разбит на {len(chunks)} частей")
        except Exception as e:
            logger.error(f"[WhisperRecognizer] Ошибка при разбиении: {e}")
            return TranscribeResult(success=False, text="", error=str(e))
        texts = []
        errors = []
        for idx, chunk in enumerate(chunks):
            try:
                logger.info(f"[WhisperRecognizer] Транскрибация части {idx+1}/{len(chunks)}")
                result = await self.transcribe_chunk(chunk, language)
                if result.success:
                    texts.append(result.text)
                else:
                    errors.append(result.error or "Unknown error")
            except Exception as e:
                logger.error(f"[WhisperRecognizer] Ошибка транскрибации части {idx+1}: {e}")
                errors.append(str(e))
        final_text = "\n".join(texts)
        success = bool(texts)
        error_msg = "; ".join(errors) if errors else None
        logger.info(f"[WhisperRecognizer] Итоговая транскрибация: success={success}, ошибок={len(errors)}")
        return TranscribeResult(success=success, text=final_text, error=error_msg) 