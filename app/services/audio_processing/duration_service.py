"""
Сервис для определения длительности аудио файлов
"""
import asyncio
import subprocess
import tempfile
import os
from typing import Optional

from app.core.logger import get_logger
from app.core.exceptions.audio_exceptions import AudioProcessingError

logger = get_logger(__name__)


class AudioDurationService:
    """Сервис для определения длительности аудио через ffmpeg"""
    
    def __init__(self):
        self.ffmpeg_path = "ffmpeg"  # Можно настроить в конфигурации
        
    async def get_audio_duration(self, audio_data: bytes) -> float:
        """
        Определяет длительность аудио в секундах
        
        Args:
            audio_data: Аудио данные в байтах
            
        Returns:
            float: Длительность в секундах
            
        Raises:
            AudioProcessingError: При ошибке обработки
        """
        temp_file = None
        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as f:
                f.write(audio_data)
                temp_file = f.name
            
            # Получаем длительность через ffprobe
            duration = await self._get_duration_with_ffprobe(temp_file)
            
            if duration is None:
                raise AudioProcessingError("Не удалось определить длительность аудио")
            
            logger.info(f"Определена длительность аудио: {duration:.2f} секунд")
            return duration
            
        except Exception as e:
            logger.exception(f"Ошибка определения длительности: {e}")
            raise AudioProcessingError(f"Ошибка определения длительности: {str(e)}")
        finally:
            # Удаляем временный файл
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный файл {temp_file}: {e}")
    
    async def _get_duration_with_ffprobe(self, file_path: str) -> Optional[float]:
        """
        Получает длительность файла через ffprobe
        
        Args:
            file_path: Путь к аудио файлу
            
        Returns:
            Optional[float]: Длительность в секундах или None при ошибке
        """
        try:
            # Команда ffprobe для получения длительности
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                file_path
            ]
            
            # Выполняем команду асинхронно
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"ffprobe error: {stderr.decode('utf-8')}")
                return None
            
            # Парсим результат
            duration_str = stdout.decode('utf-8').strip()
            if duration_str:
                return float(duration_str)
            
            return None
            
        except Exception as e:
            logger.exception(f"Ошибка выполнения ffprobe: {e}")
            return None
    
    async def get_audio_info(self, audio_data: bytes) -> dict:
        """
        Получает полную информацию об аудио файле
        
        Args:
            audio_data: Аудио данные в байтах
            
        Returns:
            dict: Информация об аудио (duration, format, etc.)
        """
        temp_file = None
        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as f:
                f.write(audio_data)
                temp_file = f.name
            
            # Получаем информацию через ffprobe
            info = await self._get_audio_info_with_ffprobe(temp_file)
            
            return info
            
        except Exception as e:
            logger.exception(f"Ошибка получения информации об аудио: {e}")
            return {
                "duration": 0.0,
                "format": "unknown",
                "bitrate": 0,
                "sample_rate": 0,
                "channels": 0
            }
        finally:
            # Удаляем временный файл
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Не удалось удалить временный файл {temp_file}: {e}")
    
    async def _get_audio_info_with_ffprobe(self, file_path: str) -> dict:
        """
        Получает подробную информацию об аудио через ffprobe
        
        Args:
            file_path: Путь к аудио файлу
            
        Returns:
            dict: Информация об аудио
        """
        try:
            # Команда ffprobe для получения полной информации
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-show_format",
                file_path
            ]
            
            # Выполняем команду асинхронно
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"ffprobe error: {stderr.decode('utf-8')}")
                return self._get_default_audio_info()
            
            # Парсим JSON результат
            import json
            probe_data = json.loads(stdout.decode('utf-8'))
            
            # Извлекаем информацию
            format_info = probe_data.get('format', {})
            streams = probe_data.get('streams', [])
            
            # Ищем аудио поток
            audio_stream = None
            for stream in streams:
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            duration = float(format_info.get('duration', 0))
            format_name = format_info.get('format_name', 'unknown')
            bitrate = int(format_info.get('bit_rate', 0))
            
            sample_rate = 0
            channels = 0
            
            if audio_stream:
                sample_rate = int(audio_stream.get('sample_rate', 0))
                channels = int(audio_stream.get('channels', 0))
            
            return {
                "duration": duration,
                "format": format_name,
                "bitrate": bitrate,
                "sample_rate": sample_rate,
                "channels": channels
            }
            
        except Exception as e:
            logger.exception(f"Ошибка парсинга ffprobe output: {e}")
            return self._get_default_audio_info()
    
    def _get_default_audio_info(self) -> dict:
        """Возвращает дефолтную информацию об аудио"""
        return {
            "duration": 0.0,
            "format": "unknown",
            "bitrate": 0,
            "sample_rate": 0,
            "channels": 0
        }
    
    async def is_ffmpeg_available(self) -> bool:
        """
        Проверяет доступность ffmpeg/ffprobe в системе
        
        Returns:
            bool: True если ffmpeg доступен
        """
        try:
            # Проверяем ffprobe
            process = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            return process.returncode == 0
            
        except Exception as e:
            logger.warning(f"ffprobe недоступен: {e}")
            return False
    
    def calculate_transcription_cost(self, duration_seconds: float, cost_per_minute: float) -> float:
        """
        Рассчитывает стоимость транскрибации
        
        Args:
            duration_seconds: Длительность в секундах
            cost_per_minute: Стоимость за минуту
            
        Returns:
            float: Общая стоимость
        """
        duration_minutes = duration_seconds / 60.0
        # Округляем до целых минут в большую сторону
        full_minutes = int(duration_minutes) if duration_minutes == int(duration_minutes) else int(duration_minutes) + 1
        return full_minutes * cost_per_minute 