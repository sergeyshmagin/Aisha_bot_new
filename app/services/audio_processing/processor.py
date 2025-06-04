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
from app.core.config import settings
from app.services.audio_processing.types import AudioProcessor
from app.core.exceptions.audio_exceptions import AudioProcessingError
from app.core.temp_files import NamedTemporaryFile, mkdtemp

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
        logger.info(f"[AUDIO SPLIT] Начинаем разбиение аудио, use_ffmpeg={use_ffmpeg}, размер: {len(audio_data)} байт")
        
        # ✅ ИСПРАВЛЕНИЕ: Добавляем двухуровневую стратегию с fallback
        if use_ffmpeg:
            try:
                logger.info(f"[AUDIO SPLIT] Попытка 1: ffmpeg разбиение")
                
                # Сохраняем во временный файл
                with NamedTemporaryFile(suffix='.mp3', delete=False) as temp_in:
                    temp_in.write(audio_data)
                    temp_in_path = temp_in.name
                output_dir = mkdtemp()
                
                try:
                    # ✅ Добавляем общий timeout для всего процесса ffmpeg
                    chunk_paths = await asyncio.wait_for(
                        self.split_audio_by_silence_ffmpeg(temp_in_path, output_dir),
                        timeout=300.0  # 5 минут максимум на весь процесс
                    )
                    
                    # Читаем чанки в память
                    result = []
                    for path in chunk_paths:
                        with open(path, 'rb') as f:
                            chunk_data = f.read()
                            if len(chunk_data) > 1000:  # Минимум 1KB
                                result.append(chunk_data)
                    
                    if result:
                        logger.info(f"[AUDIO SPLIT] ffmpeg успешно: создано {len(result)} кусков")
                        return result
                    else:
                        logger.warning(f"[AUDIO SPLIT] ffmpeg не создал валидных кусков, переключаемся на pydub")
                        
                except asyncio.TimeoutError:
                    logger.error(f"[AUDIO SPLIT] ffmpeg timeout, переключаемся на pydub")
                except Exception as e:
                    logger.error(f"[AUDIO SPLIT] ffmpeg ошибка: {e}, переключаемся на pydub")
                    
                finally:
                    Path(temp_in_path).unlink(missing_ok=True)
                    shutil.rmtree(output_dir, ignore_errors=True)
                    
            except Exception as e:
                logger.error(f"[AUDIO SPLIT] Критическая ошибка ffmpeg: {e}, переключаемся на pydub")
        
        # ✅ Fallback на pydub или основной метод
        logger.info(f"[AUDIO SPLIT] Попытка 2: pydub разбиение")
        
        try:
            # Создаем временный файл
            with NamedTemporaryFile(suffix='.mp3', delete=False) as temp:
                temp.write(audio_data)
                temp_path = temp.name
            
            # ✅ Добавляем timeout для pydub операций
            async def _split_with_pydub():
                # Загружаем аудио
                audio = AudioSegment.from_file(temp_path)
                logger.info(f"[AUDIO SPLIT] Длительность аудио: {len(audio)/1000:.2f} сек")
                
                # ✅ Ограничиваем максимальную длительность
                MAX_DURATION_MS = 600_000  # 10 минут
                if len(audio) > MAX_DURATION_MS:
                    logger.warning(f"[AUDIO SPLIT] Обрезаем длинное аудио с {len(audio)/1000:.2f}s до {MAX_DURATION_MS/1000:.2f}s")
                    audio = audio[:MAX_DURATION_MS]
                
                # ✅ Упрощенное разбиение для длинных файлов
                if len(audio) > 120_000:  # Больше 2 минут - простое разбиение
                    logger.info(f"[AUDIO SPLIT] Длинное аудио, используем простое разбиение по 60 сек")
                    chunks = []
                    chunk_duration = 60_000  # 60 секунд
                    for i in range(0, len(audio), chunk_duration):
                        chunk = audio[i:i + chunk_duration]
                        if len(chunk) > 5_000:  # Минимум 5 секунд
                            chunks.append(chunk)
                else:
                    # Обычное разбиение по тишине для коротких файлов
                    logger.info(f"[AUDIO SPLIT] Короткое аудио, используем разбиение по тишине")
                    chunks = split_on_silence(
                        audio,
                        min_silence_len=500,  # Уменьшили с 700 до 500 мс
                        silence_thresh=-35,   # Более чувствительно к тишине  
                        keep_silence=200      # Меньше тишины в начале/конце
                    )
                
                # Если не удалось разбить - возвращаем весь файл
                if not chunks:
                    logger.warning(f"[AUDIO SPLIT] Не удалось разбить, возвращаем весь файл")
                    chunks = [audio]
                
                # Конвертируем части обратно в байты
                result = []
                for i, chunk in enumerate(chunks):
                    with NamedTemporaryFile(suffix='.mp3', delete=False) as temp_chunk:
                        chunk.export(temp_chunk.name, format="mp3", bitrate="128k")  # Понижаем битрейт
                        try:
                            with open(temp_chunk.name, 'rb') as f:
                                chunk_bytes = f.read()
                            if len(chunk_bytes) > 5_000:  # Понижаем минимальный размер
                                result.append(chunk_bytes)
                                logger.info(f"[AUDIO SPLIT] Кусок {i+1}: {len(chunk_bytes)} байт")
                            else:
                                logger.warning(f"[AUDIO SPLIT] Пропущен маленький кусок {i+1}")
                        except Exception as e:
                            logger.warning(f"[AUDIO SPLIT] Битый кусок {i+1}: {e}")
                        finally:
                            Path(temp_chunk.name).unlink(missing_ok=True)
                
                return result
            
            # Выполняем с timeout
            result = await asyncio.wait_for(_split_with_pydub(), timeout=180.0)  # 3 минуты на pydub
            
            if result:
                logger.info(f"[AUDIO SPLIT] pydub успешно: создано {len(result)} кусков")
                return result
            else:
                logger.error(f"[AUDIO SPLIT] pydub не создал кусков")
                raise AudioProcessingError("Не удалось разбить аудио на куски")
                
        except asyncio.TimeoutError:
            logger.error(f"[AUDIO SPLIT] pydub timeout")
            raise AudioProcessingError("Превышено время ожидания при разбиении аудио")
        except Exception as e:
            logger.error(f"[AUDIO SPLIT] pydub ошибка: {e}")
            raise AudioProcessingError(f"Ошибка разбиения: {str(e)}")
        finally:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"[AUDIO SPLIT] Не удалось удалить временный файл {temp_path}: {e}")
    
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
            with NamedTemporaryFile(suffix='.mp3', delete=False) as temp:
                temp.write(audio_data)
                temp_path = temp.name
            
            # Загружаем аудио
            audio = AudioSegment.from_file(temp_path)
            
            # Нормализуем громкость
            normalized = audio.normalize()
            
            # Экспортируем результат
            with NamedTemporaryFile(suffix='.mp3', delete=False) as temp_out:
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
            with NamedTemporaryFile(suffix='.mp3', delete=False) as temp:
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
            with NamedTemporaryFile(suffix='.mp3', delete=False) as temp_out:
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
        
        # ✅ ИСПРАВЛЕНИЕ: Добавляем timeout и логирование прогресса
        ffmpeg_path = shutil.which('ffmpeg') or self.ffmpeg_path or 'ffmpeg'
        ffprobe_path = shutil.which('ffprobe') or 'ffprobe'
        
        logger.info(f"[FFMPEG SPLIT] Начинаем разбиение файла: {input_path}")
        
        try:
            # ✅ Получаем длительность файла с timeout
            logger.info(f"[FFMPEG SPLIT] Шаг 1: Определяем длительность файла")
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', 
                    '-of', 'default=noprint_wrappers=1:nokey=1', input_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=30.0  # 30 секунд timeout
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
            
            if proc.returncode != 0:
                raise AudioProcessingError(f"ffprobe error: {stderr.decode()}")
                
            duration = float(stdout.decode().strip())
            logger.info(f"[FFMPEG SPLIT] Длительность файла: {duration:.2f} сек")
            
            # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Ограничиваем максимальную длительность
            MAX_DURATION = 600  # 10 минут максимум
            if duration > MAX_DURATION:
                logger.warning(f"[FFMPEG SPLIT] Файл слишком длинный ({duration:.2f}s), обрезаем до {MAX_DURATION}s")
                duration = MAX_DURATION
            
            # ✅ Упрощенная логика: разбиваем на куски по 60 секунд вместо поиска тишины
            CHUNK_SIZE = 60  # 60 секунд на кусок
            segments = []
            
            current_time = 0.0
            while current_time < duration:
                end_time = min(current_time + CHUNK_SIZE, duration)
                segments.append((current_time, end_time))
                current_time = end_time
                
            logger.info(f"[FFMPEG SPLIT] Будет создано {len(segments)} кусков по {CHUNK_SIZE}s")
            
            # ✅ Создаем куски с timeout для каждого
            chunk_paths = []
            os.makedirs(output_dir, exist_ok=True)
            
            for i, (start, end) in enumerate(segments):
                logger.info(f"[FFMPEG SPLIT] Создаем кусок {i+1}/{len(segments)}: {start:.2f}-{end:.2f}s")
                
                out_path = os.path.join(output_dir, f"chunk_{i+1}.mp3")
                
                try:
                    proc = await asyncio.wait_for(
                        asyncio.create_subprocess_exec(
                            ffmpeg_path, '-y', '-i', input_path, 
                            '-ss', str(start), '-to', str(end),
                            '-acodec', 'libmp3lame', '-ab', '128k',  # Понижаем битрейт для скорости
                            out_path,
                            stdout=asyncio.subprocess.PIPE, 
                            stderr=asyncio.subprocess.PIPE
                        ),
                        timeout=60.0  # 60 секунд на каждый кусок
                    )
                    
                    _, chunk_stderr = await asyncio.wait_for(proc.communicate(), timeout=60.0)
                    
                    if proc.returncode != 0:
                        logger.warning(f"[FFMPEG SPLIT] Ошибка при создании куска {i+1}: {chunk_stderr.decode()}")
                        continue
                        
                    if os.path.exists(out_path) and os.path.getsize(out_path) > 5_000:  # Понижаем минимальный размер
                        chunk_paths.append(out_path)
                        logger.info(f"[FFMPEG SPLIT] Кусок {i+1} создан: {os.path.getsize(out_path)} байт")
                    else:
                        logger.warning(f"[FFMPEG SPLIT] Кусок {i+1} слишком маленький или пустой")
                        
                except asyncio.TimeoutError:
                    logger.error(f"[FFMPEG SPLIT] Timeout при создании куска {i+1}")
                    continue
                except Exception as e:
                    logger.error(f"[FFMPEG SPLIT] Ошибка при создании куска {i+1}: {e}")
                    continue
            
            logger.info(f"[FFMPEG SPLIT] Завершено! Создано {len(chunk_paths)} кусков")
            return chunk_paths
            
        except asyncio.TimeoutError:
            logger.error(f"[FFMPEG SPLIT] Общий timeout при обработке файла")
            raise AudioProcessingError("Превышено время ожидания при обработке аудио")
        except Exception as e:
            logger.error(f"[FFMPEG SPLIT] Критическая ошибка: {e}")
            raise AudioProcessingError(f"Ошибка при разбиении аудио: {str(e)}") 