"""
Модуль для конвертации аудио файлов
"""
import asyncio
import logging
import tempfile
import shutil
from typing import Optional
from pathlib import Path
from datetime import datetime

from pydub import AudioSegment
from app.core.config import settings
from app.services.audio_processing.types import AudioConverter, AudioMetadata
from app.core.exceptions import AudioProcessingError

logger = logging.getLogger(__name__)

async def convert_to_mp3_ffmpeg(input_path: str) -> str:
    """
    Конвертирует аудиофайл в mp3 через ffmpeg (асинхронно, через временные файлы).
    :param input_path: исходный путь
    :return: путь к mp3-файлу
    :raises RuntimeError: если ffmpeg не установлен или произошла ошибка конвертации
    """
    ffmpeg_path = shutil.which('ffmpeg') or settings.FFMPEG_PATH or 'ffmpeg'
    temp_file_mp3 = input_path.rsplit('.', 1)[0] + '.mp3'
    proc = await asyncio.create_subprocess_exec(
        ffmpeg_path,
        '-y',
        '-i', input_path,
        '-acodec', 'libmp3lame',
        '-ab', '192k',
        temp_file_mp3,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise AudioProcessingError(f"ffmpeg error: {stderr.decode()}")
    return temp_file_mp3

class PydubAudioConverter(AudioConverter):
    """Конвертер аудио на основе pydub"""
    
    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path or settings.FFMPEG_PATH
        if self.ffmpeg_path:
            AudioSegment.converter = self.ffmpeg_path
    
    async def convert_to_mp3(self, audio_data: bytes, use_ffmpeg: bool = False) -> bytes:
        """
        Конвертирует аудио в MP3 формат (через pydub или ffmpeg)
        """
        if use_ffmpeg:
            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_in:
                temp_in.write(audio_data)
                temp_in_path = temp_in.name
            try:
                mp3_path = await convert_to_mp3_ffmpeg(temp_in_path)
                with open(mp3_path, 'rb') as f:
                    result = f.read()
                return result
            finally:
                Path(temp_in_path).unlink(missing_ok=True)
                Path(mp3_path).unlink(missing_ok=True)
        else:
            try:
                # Создаем временный файл для входных данных
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_in:
                    temp_in.write(audio_data)
                    temp_in_path = temp_in.name
                
                # Создаем временный файл для выходных данных
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_out:
                    temp_out_path = temp_out.name
                
                # Конвертируем в отдельном процессе
                proc = await asyncio.create_subprocess_exec(
                    self.ffmpeg_path or 'ffmpeg',
                    '-i', temp_in_path,
                    '-acodec', 'libmp3lame',
                    '-ab', '192k',
                    temp_out_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await proc.communicate()
                
                if proc.returncode != 0:
                    raise AudioProcessingError(f"Ошибка конвертации: {stderr.decode()}")
                
                # Читаем результат
                with open(temp_out_path, 'rb') as f:
                    result = f.read()
                # Проверка валидности mp3
                try:
                    test_audio = AudioSegment.from_file(temp_out_path)
                    if len(result) < 10_000:
                        raise Exception('Файл слишком маленький, возможно битый')
                except Exception as e:
                    logger.error(f"Конвертированный mp3 невалиден: {e}")
                    raise AudioProcessingError(f"Конвертированный mp3 невалиден: {e}")
                return result
                
            except Exception as e:
                logger.error(f"Ошибка при конвертации аудио: {e}")
                raise AudioProcessingError(f"Ошибка конвертации: {str(e)}")
            
            finally:
                # Удаляем временные файлы
                for path in [temp_in_path, temp_out_path]:
                    try:
                        Path(path).unlink()
                    except Exception as e:
                        logger.warning(f"Не удалось удалить временный файл {path}: {e}")
    
    async def detect_format(self, audio_data: bytes) -> str:
        """
        Определяет формат аудио файла
        
        Args:
            audio_data: Аудио данные
            
        Returns:
            str: Формат аудио (например, 'mp3', 'wav')
            
        Raises:
            AudioProcessingError: При ошибке определения формата
        """
        try:
            with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as temp:
                temp.write(audio_data)
                temp_path = temp.name
            
            proc = await asyncio.create_subprocess_exec(
                self.ffmpeg_path or 'ffmpeg',
                '-i', temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            _, stderr = await proc.communicate()
            
            # ffmpeg выводит информацию о формате в stderr
            format_info = stderr.decode()
            
            # Парсим формат из вывода
            if 'Audio: mp3' in format_info:
                return 'mp3'
            elif 'Audio: wav' in format_info:
                return 'wav'
            elif 'Audio: aac' in format_info:
                return 'aac'
            else:
                return 'unknown'
                
        except Exception as e:
            logger.error(f"Ошибка при определении формата: {e}")
            raise AudioProcessingError(f"Ошибка определения формата: {str(e)}")
            
        finally:
            try:
                Path(temp_path).unlink()
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {temp_path}: {e}")
    
    async def get_metadata(self, audio_data: bytes) -> AudioMetadata:
        """
        Получает метаданные аудио файла
        
        Args:
            audio_data: Аудио данные
            
        Returns:
            AudioMetadata: Метаданные аудио
            
        Raises:
            AudioProcessingError: При ошибке получения метаданных
        """
        try:
            with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as temp:
                temp.write(audio_data)
                temp_path = temp.name
            
            proc = await asyncio.create_subprocess_exec(
                self.ffmpeg_path or 'ffmpeg',
                '-i', temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            _, stderr = await proc.communicate()
            
            # Парсим метаданные из вывода ffmpeg
            info = stderr.decode()
            
            # Извлекаем длительность
            duration = 0.0
            if 'Duration:' in info:
                duration_str = info.split('Duration:')[1].split(',')[0].strip()
                h, m, s = duration_str.split(':')
                duration = float(h) * 3600 + float(m) * 60 + float(s)
            
            # Извлекаем другие параметры
            sample_rate = 44100  # По умолчанию
            channels = 2  # По умолчанию
            bitrate = 192000  # По умолчанию
            
            if 'Audio:' in info:
                audio_info = info.split('Audio:')[1].split('\n')[0]
                if 'Hz' in audio_info:
                    sample_rate = int(audio_info.split('Hz')[0].strip().split()[-1])
                if 'stereo' in audio_info:
                    channels = 2
                elif 'mono' in audio_info:
                    channels = 1
                if 'kb/s' in audio_info:
                    bitrate = int(audio_info.split('kb/s')[0].strip().split()[-1]) * 1000
            
            return AudioMetadata(
                duration=duration,
                format=await self.detect_format(audio_data),
                sample_rate=sample_rate,
                channels=channels,
                bitrate=bitrate,
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Ошибка при получении метаданных: {e}")
            raise AudioProcessingError(f"Ошибка получения метаданных: {str(e)}")
            
        finally:
            try:
                Path(temp_path).unlink()
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {temp_path}: {e}") 