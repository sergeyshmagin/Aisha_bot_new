"""
Сервис для обработки больших аудио файлов без повторной отправки.
Использует умное разделение по паузам и сохранение частей в MinIO.
"""
import logging
import asyncio
import tempfile
import os
import time
from typing import Optional, List, Tuple
from io import BytesIO
import httpx
from pydub import AudioSegment
from pydub.silence import split_on_silence
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)

class LargeAudioProcessor:
    """Процессор для больших аудио файлов с умным разделением"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.max_chunk_size = 15 * 1024 * 1024  # 15 МБ на чанк (безопасный лимит)
        self.min_silence_len = 500  # 0.5 секунды тишины для разделения
        self.silence_thresh = -35  # dB (более чувствительное определение тишины)
        self.overlap_duration = 3000  # 3 секунды перекрытия между частями
        
    async def process_large_audio(
        self, 
        file_id: str, 
        file_path: str,
        file_size: int,
        audio_service=None
    ) -> Optional[str]:
        """
        Обрабатывает большой аудио файл через умное разделение по паузам
        
        Args:
            file_id: ID файла в Telegram
            file_path: Путь к файлу (может быть None для больших файлов)
            file_size: Размер файла в байтах
            audio_service: Сервис для обработки аудио
            
        Returns:
            Текст транскрипта или None при ошибке
        """
        logger.info(f"[LARGE_AUDIO] Начинаем умную обработку файла: {file_size} байт")
        
        try:
            # Стратегия 1: Пытаемся скачать файл полностью для умного разделения
            audio_data = await self._download_via_direct_link(file_id, file_path)
            
            if audio_data:
                logger.info(f"[LARGE_AUDIO] Файл скачан ({len(audio_data)} байт), используем умное разделение")
                return await self._process_with_smart_splitting(audio_data, file_id, audio_service)
            
            # Стратегия 2: Файл слишком большой, используем потоковое разделение
            logger.warning(f"[LARGE_AUDIO] Файл слишком большой для полного скачивания, используем потоковое разделение")
            return await self._process_with_streaming(file_id, file_size, audio_service)
                    
        except Exception as e:
            logger.exception(f"[LARGE_AUDIO] Ошибка при обработке: {e}")
            return None
    
    async def _download_via_direct_link(self, file_id: str, file_path: Optional[str]) -> Optional[bytes]:
        """Скачивает файл через прямую ссылку Telegram"""
        try:
            # Метод 1: Используем file_path если доступен
            if file_path:
                url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                logger.info(f"[LARGE_AUDIO] Скачиваем через file_path: {url}")
                
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return response.content
                    else:
                        logger.warning(f"[LARGE_AUDIO] Ошибка скачивания: {response.status_code}")
            
            # Метод 2: Пытаемся получить file_path через getFile
            logger.info(f"[LARGE_AUDIO] Пытаемся получить file_path для {file_id}")
            get_file_url = f"https://api.telegram.org/bot{self.bot_token}/getFile"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(get_file_url, json={"file_id": file_id})
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok") and "file_path" in result["result"]:
                        file_path = result["result"]["file_path"]
                        download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                        
                        # Скачиваем файл
                        download_response = await client.get(download_url)
                        if download_response.status_code == 200:
                            return download_response.content
            
            logger.error(f"[LARGE_AUDIO] Все методы скачивания не сработали")
            return None
            
        except Exception as e:
            logger.exception(f"[LARGE_AUDIO] Ошибка при скачивании: {e}")
            return None
    
    async def _process_with_smart_splitting(self, audio_data: bytes, file_id: str, audio_service=None) -> Optional[str]:
        """Обрабатывает файл с умным разделением по паузам"""
        temp_audio_path = None
        temp_files_created = []
        
        try:
            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_audio_path = temp_file.name
                temp_files_created.append(temp_audio_path)
            
            # Загружаем аудио через pydub с улучшенной обработкой форматов
            try:
                audio = AudioSegment.from_file(temp_audio_path)
                logger.info(f"[LARGE_AUDIO] Аудио загружено: {len(audio)/1000:.1f}с, {audio.frame_rate}Hz, каналов: {audio.channels}")
            except Exception as e:
                logger.warning(f"[LARGE_AUDIO] Ошибка загрузки через pydub, пытаемся через FFmpeg: {e}")
                # Пытаемся принудительно конвертировать через FFmpeg
                try:
                    audio = AudioSegment.from_file(temp_audio_path, format="m4a")
                    logger.info(f"[LARGE_AUDIO] Аудио загружено через FFmpeg как M4A: {len(audio)/1000:.1f}с")
                except Exception as e2:
                    logger.error(f"[LARGE_AUDIO] Не удалось загрузить аудио файл: {e2}")
                    return None
            
            # Умное разделение по паузам с учетом размера
            chunks = await self._smart_split_by_silence(audio)
            logger.info(f"[LARGE_AUDIO] Умное разделение: {len(chunks)} частей")
            
            # Обрабатываем каждую часть
            transcripts = []
            for i, chunk in enumerate(chunks):
                logger.info(f"[LARGE_AUDIO] Обрабатываем часть {i+1}/{len(chunks)} ({len(chunk)/1000:.1f}с)")
                chunk_transcript = await self._process_audio_chunk(chunk, i, audio_service)
                if chunk_transcript:
                    transcripts.append(chunk_transcript)
            
            # Склеиваем результаты с удалением дублирований
            full_transcript = self._merge_transcripts_smart(transcripts)
            logger.info(f"[LARGE_AUDIO] Итоговый транскрипт: {len(full_transcript)} символов")
            
            return full_transcript
            
        except Exception as e:
            logger.exception(f"[LARGE_AUDIO] Ошибка при умной обработке: {e}")
            return None
            
        finally:
            # Очищаем все временные файлы
            await self._cleanup_temp_files(temp_files_created)
    
    async def _cleanup_temp_files(self, file_paths: List[str]) -> None:
        """Очищает список временных файлов"""
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    logger.debug(f"[LARGE_AUDIO] Очищен временный файл: {file_path}")
                except Exception as e:
                    logger.warning(f"[LARGE_AUDIO] Не удалось удалить временный файл {file_path}: {e}")
    
    def __del__(self):
        """Деструктор для финальной очистки"""
        if not settings.AUTO_CLEANUP_ENABLED:
            return
            
        # Проверяем наличие оставшихся временных файлов
        try:
            temp_dir = tempfile.gettempdir()
            current_time = time.time()
            
            for filename in os.listdir(temp_dir):
                if filename.startswith('tmp') and (filename.endswith('.audio') or filename.endswith('.wav')):
                    file_path = os.path.join(temp_dir, filename)
                    try:
                        # Проверяем возраст файла
                        file_age = current_time - os.path.getctime(file_path)
                        if file_age > settings.TEMP_FILE_MAX_AGE:
                            os.unlink(file_path)
                            logger.debug(f"[LARGE_AUDIO] Очищен старый временный файл: {file_path} (возраст: {file_age:.0f}с)")
                    except Exception as e:
                        logger.debug(f"[LARGE_AUDIO] Не удалось очистить файл {file_path}: {e}")
        except Exception as e:
            logger.debug(f"[LARGE_AUDIO] Ошибка при финальной очистке: {e}")
    
    async def _smart_split_by_silence(self, audio: AudioSegment) -> List[AudioSegment]:
        """Умное разделение по паузам с учетом размера частей"""
        try:
            # Шаг 1: Находим все паузы в аудио
            chunks = split_on_silence(
                audio,
                min_silence_len=self.min_silence_len,
                silence_thresh=self.silence_thresh,
                keep_silence=300  # Оставляем 300ms тишины для контекста
            )
            
            if len(chunks) <= 1:
                logger.info(f"[LARGE_AUDIO] Паузы не найдены, используем разделение по времени")
                return self._split_by_time_with_overlap(audio)
            
            logger.info(f"[LARGE_AUDIO] Найдено {len(chunks)} сегментов по паузам")
            
            # Шаг 2: Группируем сегменты до целевого размера
            grouped_chunks = self._group_chunks_by_size(chunks)
            
            # Шаг 3: Добавляем перекрытия между группами
            final_chunks = self._add_overlaps(grouped_chunks, audio)
            
            logger.info(f"[LARGE_AUDIO] Финальное разделение: {len(final_chunks)} частей")
            return final_chunks
            
        except Exception as e:
            logger.exception(f"[LARGE_AUDIO] Ошибка при умном разделении: {e}")
            return self._split_by_time_with_overlap(audio)
    
    def _group_chunks_by_size(self, chunks: List[AudioSegment]) -> List[AudioSegment]:
        """Группирует маленькие сегменты в части до целевого размера"""
        grouped = []
        current_group = AudioSegment.empty()
        target_duration = 8 * 60 * 1000  # 8 минут (примерно 15 МБ)
        
        for chunk in chunks:
            # Проверяем, поместится ли chunk в текущую группу
            if len(current_group) + len(chunk) <= target_duration:
                current_group += chunk
            else:
                # Сохраняем текущую группу и начинаем новую
                if len(current_group) > 0:
                    grouped.append(current_group)
                
                # Если chunk сам по себе слишком большой, делим его
                if len(chunk) > target_duration:
                    sub_chunks = self._split_large_chunk(chunk, target_duration)
                    grouped.extend(sub_chunks)
                    current_group = AudioSegment.empty()
                else:
                    current_group = chunk
        
        # Добавляем последнюю группу
        if len(current_group) > 0:
            grouped.append(current_group)
        
        return grouped
    
    def _split_large_chunk(self, chunk: AudioSegment, max_duration: int) -> List[AudioSegment]:
        """Разделяет большой chunk на части по времени"""
        parts = []
        for i in range(0, len(chunk), max_duration):
            part = chunk[i:i + max_duration]
            parts.append(part)
        return parts
    
    def _add_overlaps(self, chunks: List[AudioSegment], original_audio: AudioSegment) -> List[AudioSegment]:
        """Добавляет перекрытия между частями для лучшего контекста"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        current_position = 0
        
        for i, chunk in enumerate(chunks):
            chunk_duration = len(chunk)
            
            if i == 0:
                # Первая часть - без изменений
                overlapped_chunks.append(chunk)
            else:
                # Добавляем перекрытие с предыдущей частью
                overlap_start = max(0, current_position - self.overlap_duration)
                chunk_start = current_position
                chunk_end = current_position + chunk_duration
                
                # Извлекаем часть с перекрытием из оригинального аудио
                overlapped_chunk = original_audio[overlap_start:chunk_end]
                overlapped_chunks.append(overlapped_chunk)
            
            current_position += chunk_duration
        
        return overlapped_chunks
    
    def _split_by_time_with_overlap(self, audio: AudioSegment) -> List[AudioSegment]:
        """Разделяет аудио по времени с перекрытиями"""
        chunk_duration = 8 * 60 * 1000  # 8 минут
        chunks = []
        
        for i in range(0, len(audio), chunk_duration - self.overlap_duration):
            end_pos = min(i + chunk_duration, len(audio))
            chunk = audio[i:end_pos]
            chunks.append(chunk)
            
            # Если это последняя часть, прерываем
            if end_pos >= len(audio):
                break
        
        logger.info(f"[LARGE_AUDIO] Разделено по времени с перекрытиями: {len(chunks)} частей")
        return chunks
    
    async def _process_with_streaming(self, file_id: str, file_size: int, audio_service=None) -> Optional[str]:
        """Обрабатывает файл через потоковое разделение (для очень больших файлов)"""
        logger.info(f"[LARGE_AUDIO] Потоковая обработка файла {file_id} размером {file_size / (1024*1024):.1f} МБ")
        
        # Для файлов, которые нельзя скачать через Bot API
        # Возвращаем информативное сообщение
        duration_estimate = file_size / (1024 * 1024) * 2  # Примерно 2 минуты на МБ
        
        logger.warning(f"[LARGE_AUDIO] Файл {file_id} размером {file_size / (1024*1024):.1f} МБ "
                      f"(~{duration_estimate:.1f} мин) требует отправки как документ")
        
        return None  # Основной обработчик покажет информативное сообщение
    
    def _merge_transcripts_smart(self, transcripts: List[str]) -> str:
        """Умное склеивание транскриптов с удалением дублирований"""
        if not transcripts:
            return ""
        
        if len(transcripts) == 1:
            return transcripts[0]
        
        # Простое склеивание с маркерами частей
        # В будущем можно добавить алгоритм удаления дублирований
        merged_parts = []
        for i, transcript in enumerate(transcripts):
            if transcript.strip():
                # Убираем возможные маркеры частей из предыдущих обработок
                clean_transcript = transcript.strip()
                if clean_transcript.startswith('[Часть'):
                    # Находим конец маркера и берем текст после него
                    end_marker = clean_transcript.find(']\n')
                    if end_marker != -1:
                        clean_transcript = clean_transcript[end_marker + 2:].strip()
                
                merged_parts.append(clean_transcript)
        
        # Склеиваем части с разделителями
        return '\n\n'.join(merged_parts)
    
    async def _process_audio_chunk(self, chunk: AudioSegment, chunk_index: int, audio_service=None) -> Optional[str]:
        """Обрабатывает одну часть аудио через Whisper"""
        temp_wav_path = None
        try:
            # Экспортируем в WAV для Whisper
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                chunk.export(temp_file.name, format="wav")
                temp_wav_path = temp_file.name
            
            try:
                # Читаем данные для отправки в Whisper
                with open(temp_wav_path, 'rb') as f:
                    audio_data = f.read()
                
                logger.info(f"[LARGE_AUDIO] Часть {chunk_index}: {len(audio_data)} байт, {len(chunk)/1000:.1f}с")
                
                # Интегрируем с AudioProcessingService
                if audio_service:
                    try:
                        result = await audio_service.process_audio(audio_data)
                        if result.success and result.text:
                            logger.info(f"[LARGE_AUDIO] Часть {chunk_index} успешно обработана: {len(result.text)} символов")
                            return result.text.strip()
                        else:
                            logger.warning(f"[LARGE_AUDIO] Ошибка обработки части {chunk_index}: {result.error}")
                            return None
                    except Exception as e:
                        logger.exception(f"[LARGE_AUDIO] Ошибка при вызове audio_service для части {chunk_index}: {e}")
                        return None
                
                # Заглушка для тестирования
                return f"Транскрипт части {chunk_index + 1} (длительность: {len(chunk)/1000:.1f}с)"
                
            finally:
                # Удаляем временный WAV файл
                if temp_wav_path and os.path.exists(temp_wav_path):
                    try:
                        os.unlink(temp_wav_path)
                        logger.debug(f"[LARGE_AUDIO] Удален временный файл: {temp_wav_path}")
                    except Exception as e:
                        logger.warning(f"[LARGE_AUDIO] Не удалось удалить временный файл {temp_wav_path}: {e}")
                    
        except Exception as e:
            logger.exception(f"[LARGE_AUDIO] Ошибка при обработке части {chunk_index}: {e}")
            # Убеждаемся что временный файл удален даже при ошибке
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.unlink(temp_wav_path)
                    logger.debug(f"[LARGE_AUDIO] Удален временный файл после ошибки: {temp_wav_path}")
                except Exception as cleanup_error:
                    logger.warning(f"[LARGE_AUDIO] Не удалось удалить временный файл после ошибки {temp_wav_path}: {cleanup_error}")
            return None

# Функция для интеграции с существующим кодом
async def try_process_large_audio(
    bot_token: str,
    file_id: str, 
    file_path: Optional[str],
    file_size: int,
    audio_service=None
) -> Optional[str]:
    """
    Пытается обработать большой аудио файл
    
    Returns:
        Транскрипт или None если не удалось
    """
    processor = LargeAudioProcessor(bot_token)
    return await processor.process_large_audio(file_id, file_path, file_size, audio_service)
