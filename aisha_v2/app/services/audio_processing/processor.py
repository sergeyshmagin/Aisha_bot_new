"""
Модуль для обработки аудио
"""
import asyncio
import logging
import tempfile
from typing import List, Optional
from pathlib import Path

from pydub import AudioSegment
from pydub.silence import split_on_silence
from aisha_v2.app.core.config import settings
from aisha_v2.app.services.audio_processing.types import AudioProcessor
from aisha_v2.app.core.exceptions import AudioProcessingError

logger = logging.getLogger(__name__)

class AudioProcessor(AudioProcessor):
    """Процессор аудио для обработки и нормализации"""
    
    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path or settings.FFMPEG_PATH
        if self.ffmpeg_path:
            AudioSegment.converter = self.ffmpeg_path
    
    async def split_audio(self, audio_data: bytes) -> List[bytes]:
        """
        Разбивает аудио на части по тишине
        
        Args:
            audio_data: Аудио данные
            
        Returns:
            List[bytes]: Список частей аудио
            
        Raises:
            AudioProcessingError: При ошибке разбиения
        """
        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp:
                temp.write(audio_data)
                temp_path = temp.name
            
            # Загружаем аудио
            audio = AudioSegment.from_file(temp_path)
            
            # Разбиваем на части по тишине
            chunks = split_on_silence(
                audio,
                min_silence_len=700,  # 700 мс
                silence_thresh=-30,  # -30 dB
                keep_silence=300  # 300 мс тишины в начале и конце
            )
            
            # Конвертируем части обратно в байты
            result = []
            for i, chunk in enumerate(chunks):
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_chunk:
                    chunk.export(temp_chunk.name, format="mp3")
                    with open(temp_chunk.name, 'rb') as f:
                        result.append(f.read())
                    Path(temp_chunk.name).unlink()
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при разбиении аудио: {e}")
            raise AudioProcessingError(f"Ошибка разбиения: {str(e)}")
            
        finally:
            try:
                Path(temp_path).unlink()
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {temp_path}: {e}")
    
    async def normalize_audio(self, audio_data: bytes) -> bytes:
        """
        Нормализует громкость аудио
        
        Args:
            audio_data: Аудио данные
            
        Returns:
            bytes: Нормализованные аудио данные
            
        Raises:
            AudioProcessingError: При ошибке нормализации
        """
        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp:
                temp.write(audio_data)
                temp_path = temp.name
            
            # Загружаем аудио
            audio = AudioSegment.from_file(temp_path)
            
            # Нормализуем громкость
            normalized = audio.normalize()
            
            # Экспортируем результат
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_out:
                normalized.export(temp_out.name, format="mp3")
                with open(temp_out.name, 'rb') as f:
                    result = f.read()
                Path(temp_out.name).unlink()
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при нормализации аудио: {e}")
            raise AudioProcessingError(f"Ошибка нормализации: {str(e)}")
            
        finally:
            try:
                Path(temp_path).unlink()
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {temp_path}: {e}")
    
    async def remove_silence(self, audio_data: bytes) -> bytes:
        """
        Удаляет тишину из начала и конца аудио
        
        Args:
            audio_data: Аудио данные
            
        Returns:
            bytes: Обработанные аудио данные
            
        Raises:
            AudioProcessingError: При ошибке обработки
        """
        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp:
                temp.write(audio_data)
                temp_path = temp.name
            
            # Загружаем аудио
            audio = AudioSegment.from_file(temp_path)
            
            # Находим начало и конец звука
            start = 0
            end = len(audio)
            
            # Ищем начало звука
            for i in range(0, len(audio), 100):
                if audio[i:i+100].dBFS > -50:
                    start = i
                    break
            
            # Ищем конец звука
            for i in range(len(audio), 0, -100):
                if audio[i-100:i].dBFS > -50:
                    end = i
                    break
            
            # Обрезаем тишину
            trimmed = audio[start:end]
            
            # Экспортируем результат
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_out:
                trimmed.export(temp_out.name, format="mp3")
                with open(temp_out.name, 'rb') as f:
                    result = f.read()
                Path(temp_out.name).unlink()
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при удалении тишины: {e}")
            raise AudioProcessingError(f"Ошибка обработки: {str(e)}")
            
        finally:
            try:
                Path(temp_path).unlink()
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {temp_path}: {e}") 