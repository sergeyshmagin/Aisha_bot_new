"""
Модуль для обработки аудио
"""
import asyncio
import logging
import tempfile
import shutil
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
    
    async def split_audio(self, audio_data: bytes, use_ffmpeg: bool = False) -> list:
        """
        Разбивает аудио на части по тишине (через pydub или ffmpeg)
        """
        if use_ffmpeg:
            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_in:
                temp_in.write(audio_data)
                temp_in_path = temp_in.name
            output_dir = tempfile.mkdtemp()
            try:
                chunk_paths = await self.split_audio_by_silence_ffmpeg(temp_in_path, output_dir)
                # Читаем чанки в память
                result = []
                for path in chunk_paths:
                    with open(path, 'rb') as f:
                        result.append(f.read())
                return result
            finally:
                Path(temp_in_path).unlink(missing_ok=True)
                shutil.rmtree(output_dir, ignore_errors=True)
        else:
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
                        try:
                            test_audio = AudioSegment.from_file(temp_chunk.name)
                            with open(temp_chunk.name, 'rb') as f:
                                chunk_bytes = f.read()
                            if not chunk_bytes or len(chunk_bytes) < 10_000:
                                logger.warning(f"Пропущен пустой/маленький chunk {i+1}")
                                continue
                            result.append(chunk_bytes)
                        except Exception as e:
                            logger.warning(f"Битый chunk {i+1}: {e}")
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

    async def split_audio_by_silence_ffmpeg(self, input_path: str, output_dir: str, min_silence_len: float = 0.7, silence_thresh: int = -30) -> list:
        """
        Нарезает аудиофайл на части по паузам с помощью ffmpeg.
        :param input_path: путь к исходному аудиофайлу
        :param output_dir: директория для сохранения кусков
        :param min_silence_len: минимальная длина тишины (секунды)
        :param silence_thresh: уровень тишины в dB (относительно 0)
        :return: список путей к кускам
        """
        import os
        ffmpeg_path = shutil.which('ffmpeg') or self.ffmpeg_path or 'ffmpeg'
        ffprobe_path = shutil.which('ffprobe') or 'ffprobe'
        # Получаем длительность файла
        proc = await asyncio.create_subprocess_exec(
            ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
            input_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise AudioProcessingError(f"ffprobe error: {stderr.decode()}")
        duration = float(stdout.decode().strip())
        # Запускаем ffmpeg для поиска пауз
        command = [
            ffmpeg_path, '-i', input_path, '-af', f'silencedetect=noise={silence_thresh}dB:d={min_silence_len}', '-f', 'null', '-'
        ]
        proc = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
        _, stderr = await proc.communicate()
        stderr_str = stderr.decode()
        if proc.returncode != 0:
            raise AudioProcessingError(f"ffmpeg silencedetect error: {stderr_str}")
        silence_starts = []
        silence_ends = []
        for line in stderr_str.splitlines():
            if "silence_start" in line:
                silence_starts.append(float(line.split("silence_start: ")[-1]))
            if "silence_end" in line:
                silence_ends.append(float(line.split("silence_end: ")[-1].split(" |")[0]))
        # Формируем интервалы для нарезки
        segments = []
        prev_end = 0.0
        for start in silence_starts:
            segments.append((prev_end, start))
            prev_end = start
        if prev_end < duration:
            segments.append((prev_end, duration))
        chunk_paths = []
        os.makedirs(output_dir, exist_ok=True)
        for i, (start, end) in enumerate(segments):
            out_path = os.path.join(output_dir, f"chunk_{i+1}.mp3")
            proc = await asyncio.create_subprocess_exec(
                ffmpeg_path, '-y', '-i', input_path, '-ss', str(start), '-to', str(end),
                '-acodec', 'libmp3lame', '-ab', '192k', out_path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _, chunk_stderr = await proc.communicate()
            if proc.returncode != 0:
                raise AudioProcessingError(f"ffmpeg chunk error: {chunk_stderr.decode()}")
            if os.path.exists(out_path) and os.path.getsize(out_path) > 10_000:
                chunk_paths.append(out_path)
        return chunk_paths 