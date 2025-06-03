"""
Модуль для конвертации аудио файлов
"""
import asyncio
import logging
import tempfile
import shutil
import os
from typing import Optional
from pathlib import Path
from datetime import datetime

from pydub import AudioSegment
from app.core.temp_files import NamedTemporaryFile, mkdtemp
from app.core.config import settings
from app.services.audio_processing.types import AudioConverter, AudioMetadata
from app.core.exceptions.audio_exceptions import AudioProcessingError

logger = logging.getLogger(__name__)

async def convert_to_mp3_ffmpeg(input_path: str) -> str:
    """
    Конвертирует аудиофайл в mp3 через ffmpeg (асинхронно, через временные файлы).
    :param input_path: исходный путь
    :return: путь к mp3-файлу
    :raises RuntimeError: если ffmpeg не установлен или произошла ошибка конвертации
    """
    # Пробуем найти ffmpeg в разных местах
    ffmpeg_candidates = [
        settings.FFMPEG_PATH,
        '/usr/bin/ffmpeg',
        '/usr/local/bin/ffmpeg',
        '/bin/ffmpeg',
        shutil.which('ffmpeg')
    ]
    
    ffmpeg_path = None
    for candidate in ffmpeg_candidates:
        if candidate and os.path.exists(candidate):
            ffmpeg_path = candidate
            break
    
    if not ffmpeg_path:
        # Последняя попытка через which
        ffmpeg_path = shutil.which('ffmpeg')
    
    if not ffmpeg_path:
        raise AudioProcessingError(f"ffmpeg не найден. Проверьте установку: sudo apt install ffmpeg")
    
    temp_file_mp3 = input_path.rsplit('.', 1)[0] + '.mp3'
    
    try:
        # Улучшенные параметры FFmpeg для разных форматов, включая M4A
        proc = await asyncio.create_subprocess_exec(
            ffmpeg_path,
            '-y',  # Перезаписывать выходной файл
            '-i', input_path,
            '-vn',  # Отключить видео
            '-acodec', 'libmp3lame',  # Кодек MP3
            '-ab', '192k',  # Битрейт
            '-ar', '44100',  # Частота дискретизации
            '-ac', '2',  # Стерео
            '-f', 'mp3',  # Принудительно MP3 формат
            temp_file_mp3,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            error_msg = stderr.decode()
            logger.error(f"FFmpeg ошибка конвертации: {error_msg}")
            raise AudioProcessingError(f"ffmpeg error: {error_msg}")
        
        # Проверяем, что файл создался и не пустой
        if not os.path.exists(temp_file_mp3) or os.path.getsize(temp_file_mp3) == 0:
            raise AudioProcessingError(f"Конвертированный файл пуст или не создался: {temp_file_mp3}")
            
        return temp_file_mp3
    except FileNotFoundError:
        raise AudioProcessingError(f"ffmpeg не найден по пути: {ffmpeg_path}. Установите ffmpeg: sudo apt install ffmpeg")

class PydubAudioConverter(AudioConverter):
    """Конвертер аудио на основе pydub"""
    
    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path or settings.FFMPEG_PATH
        if self.ffmpeg_path:
            AudioSegment.converter = self.ffmpeg_path
    
    async def convert_to_mp3(self, audio_data: bytes, use_ffmpeg: bool = False, input_format: str = None) -> bytes:
        """
        Конвертирует аудио в MP3 формат (через pydub или ffmpeg)
        
        Args:
            audio_data: Исходные аудио данные
            use_ffmpeg: Использовать FFmpeg вместо pydub
            input_format: Формат входного файла (для правильного расширения)
        """
        if use_ffmpeg:
            # Определяем правильное расширение для временного файла
            if input_format:
                suffix = f'.{input_format}'
            else:
                # Пытаемся определить формат по заголовку файла
                suffix = self._detect_format_by_header(audio_data)
            
            # Сохраняем во временный файл с правильным расширением
            with NamedTemporaryFile(suffix=suffix, delete=False) as temp_in:
                temp_in.write(audio_data)
                temp_in_path = temp_in.name
            
            mp3_path = None
            try:
                mp3_path = await convert_to_mp3_ffmpeg(temp_in_path)
                with open(mp3_path, 'rb') as f:
                    result = f.read()
                logger.info(f"[CONVERTER] Успешно конвертирован {suffix} файл в MP3: {len(result)} байт")
                return result
            finally:
                Path(temp_in_path).unlink(missing_ok=True)
                if mp3_path:
                    Path(mp3_path).unlink(missing_ok=True)
        else:
            try:
                # Создаем временный файл для входных данных
                with NamedTemporaryFile(suffix='.wav', delete=False) as temp_in:
                    temp_in.write(audio_data)
                    temp_in_path = temp_in.name
                
                # Создаем временный файл для выходных данных
                with NamedTemporaryFile(suffix='.mp3', delete=False) as temp_out:
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
            with NamedTemporaryFile(suffix='.tmp', delete=False) as temp:
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
            elif 'Audio: m4a' in format_info or 'mov,mp4,m4a' in format_info:
                return 'm4a'
            elif 'Audio: ogg' in format_info:
                return 'ogg'
            elif 'Audio: flac' in format_info:
                return 'flac'
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
    
    def _detect_format_by_header(self, audio_data: bytes) -> str:
        """
        Определяет формат аудио по заголовку файла (magic bytes)
        
        Args:
            audio_data: Аудио данные
            
        Returns:
            str: Расширение файла с точкой (например, '.m4a', '.mp3')
        """
        if len(audio_data) < 12:
            return '.audio'  # Fallback для очень маленьких файлов
        
        # Проверяем magic bytes для разных форматов
        header = audio_data[:12]
        
        # MP3 - начинается с ID3 или синхронизационного слова
        if header.startswith(b'ID3') or (header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
            return '.mp3'
        
        # WAV - RIFF заголовок
        if header.startswith(b'RIFF') and b'WAVE' in audio_data[:20]:
            return '.wav'
        
        # M4A/MP4 - ftyp заголовок
        if b'ftyp' in header or header[4:8] == b'ftyp':
            # Проверяем подтип
            if b'M4A ' in audio_data[:32] or b'mp41' in audio_data[:32] or b'mp42' in audio_data[:32]:
                return '.m4a'
            return '.mp4'
        
        # OGG - OggS заголовок
        if header.startswith(b'OggS'):
            return '.ogg'
        
        # FLAC - fLaC заголовок
        if header.startswith(b'fLaC'):
            return '.flac'
        
        # AAC - ADTS заголовок
        if len(audio_data) >= 2 and header[0] == 0xFF and (header[1] & 0xF0) == 0xF0:
            return '.aac'
        
        # Fallback - используем общее расширение
        logger.warning(f"[CONVERTER] Не удалось определить формат по заголовку: {header.hex()}")
        return '.audio'
    
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
            with NamedTemporaryFile(suffix='.tmp', delete=False) as temp:
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