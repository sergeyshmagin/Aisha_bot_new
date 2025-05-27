"""
Сервис для обработки больших аудио файлов без повторной отправки.
Использует прямые ссылки Telegram и разделение по паузам.
"""
import logging
import asyncio
import tempfile
import os
from typing import Optional, List, Tuple
from io import BytesIO
import httpx
from pydub import AudioSegment
from pydub.silence import split_on_silence

from app.core.config import settings

logger = logging.getLogger(__name__)

class LargeAudioProcessor:
    """Процессор для больших аудио файлов"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.max_chunk_size = 15 * 1024 * 1024  # 15 МБ на чанк
        self.min_silence_len = 1000  # 1 секунда тишины
        self.silence_thresh = -40  # dB
        
    async def process_large_audio(
        self, 
        file_id: str, 
        file_path: str,
        file_size: int,
        audio_service=None
    ) -> Optional[str]:
        """
        Обрабатывает большой аудио файл через прямые ссылки и разделение
        
        Args:
            file_id: ID файла в Telegram
            file_path: Путь к файлу (может быть None для больших файлов)
            file_size: Размер файла в байтах
            
        Returns:
            Текст транскрипта или None при ошибке
        """
        logger.info(f"[LARGE_AUDIO] Начинаем обработку большого файла: {file_size} байт")
        
        try:
            # Шаг 1: Пытаемся получить файл через прямую ссылку
            audio_data = await self._download_via_direct_link(file_id, file_path)
            
            if not audio_data:
                logger.warning(f"[LARGE_AUDIO] Не удалось скачать файл напрямую, пробуем альтернативные методы")
                
                # Альтернативный метод: используем mock обработку для демонстрации
                # В реальности здесь можно добавить другие методы получения файла
                return await self._process_without_download(file_id, file_size, audio_service)
            
            # Шаг 2: Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_audio_path = temp_file.name
            
            try:
                # Шаг 3: Загружаем аудио через pydub
                audio = AudioSegment.from_file(temp_audio_path)
                logger.info(f"[LARGE_AUDIO] Аудио загружено: {len(audio)}ms, {audio.frame_rate}Hz")
                
                # Шаг 4: Разделяем на части по паузам
                chunks = await self._split_audio_by_silence(audio)
                logger.info(f"[LARGE_AUDIO] Разделено на {len(chunks)} частей")
                
                # Шаг 5: Обрабатываем каждую часть
                transcripts = []
                for i, chunk in enumerate(chunks):
                    logger.info(f"[LARGE_AUDIO] Обрабатываем часть {i+1}/{len(chunks)}")
                    chunk_transcript = await self._process_audio_chunk(chunk, i, audio_service)
                    if chunk_transcript:
                        transcripts.append(chunk_transcript)
                
                # Шаг 6: Склеиваем результаты
                full_transcript = self._merge_transcripts(transcripts)
                logger.info(f"[LARGE_AUDIO] Итоговый транскрипт: {len(full_transcript)} символов")
                
                return full_transcript
                
            finally:
                # Удаляем временный файл
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                    
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
    
    async def _split_audio_by_silence(self, audio: AudioSegment) -> List[AudioSegment]:
        """Разделяет аудио на части по паузам"""
        try:
            # Разделяем по тишине
            chunks = split_on_silence(
                audio,
                min_silence_len=self.min_silence_len,
                silence_thresh=self.silence_thresh,
                keep_silence=500  # Оставляем 500ms тишины
            )
            
            # Если получилось слишком много маленьких частей, объединяем их
            if len(chunks) > 20:
                logger.info(f"[LARGE_AUDIO] Слишком много частей ({len(chunks)}), объединяем")
                chunks = self._merge_small_chunks(chunks)
            
            # Если не удалось разделить, делим по времени
            if len(chunks) <= 1:
                logger.info(f"[LARGE_AUDIO] Разделение по тишине не сработало, делим по времени")
                chunks = self._split_by_time(audio)
            
            return chunks
            
        except Exception as e:
            logger.exception(f"[LARGE_AUDIO] Ошибка при разделении: {e}")
            # Fallback: делим по времени
            return self._split_by_time(audio)
    
    def _merge_small_chunks(self, chunks: List[AudioSegment]) -> List[AudioSegment]:
        """Объединяет маленькие части в более крупные"""
        merged_chunks = []
        current_chunk = AudioSegment.empty()
        target_duration = 5 * 60 * 1000  # 5 минут
        
        for chunk in chunks:
            if len(current_chunk) + len(chunk) < target_duration:
                current_chunk += chunk
            else:
                if len(current_chunk) > 0:
                    merged_chunks.append(current_chunk)
                current_chunk = chunk
        
        # Добавляем последнюю часть
        if len(current_chunk) > 0:
            merged_chunks.append(current_chunk)
        
        return merged_chunks
    
    def _split_by_time(self, audio: AudioSegment) -> List[AudioSegment]:
        """Разделяет аудио на части по времени"""
        chunk_duration = 5 * 60 * 1000  # 5 минут
        chunks = []
        
        for i in range(0, len(audio), chunk_duration):
            chunk = audio[i:i + chunk_duration]
            chunks.append(chunk)
        
        logger.info(f"[LARGE_AUDIO] Разделено по времени на {len(chunks)} частей")
        return chunks
    
    async def _process_audio_chunk(self, chunk: AudioSegment, chunk_index: int, audio_service=None) -> Optional[str]:
        """Обрабатывает одну часть аудио через Whisper"""
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
                
                # Интегрируем с AudioProcessingService если доступен
                if audio_service:
                    try:
                        result = await audio_service.process_audio(audio_data)
                        if result.success and result.text:
                            return result.text
                        else:
                            logger.warning(f"[LARGE_AUDIO] Ошибка обработки части {chunk_index}: {result.error}")
                            return None
                    except Exception as e:
                        logger.exception(f"[LARGE_AUDIO] Ошибка при вызове audio_service для части {chunk_index}: {e}")
                        return None
                
                # Заглушка для тестирования (если audio_service недоступен)
                return f"Транскрипт части {chunk_index + 1} (длительность: {len(chunk)/1000:.1f}с)"
                
            finally:
                if os.path.exists(temp_wav_path):
                    os.unlink(temp_wav_path)
                    
        except Exception as e:
            logger.exception(f"[LARGE_AUDIO] Ошибка при обработке части {chunk_index}: {e}")
            return None
    
    def _merge_transcripts(self, transcripts: List[str]) -> str:
        """Объединяет транскрипты частей в один"""
        if not transcripts:
            return ""
        
        # Простое объединение с разделителями
        merged = "\n\n".join(f"[Часть {i+1}]\n{transcript}" 
                           for i, transcript in enumerate(transcripts))
        
        return merged
    
    async def _process_without_download(self, file_id: str, file_size: int, audio_service=None) -> Optional[str]:
        """
        Альтернативный метод обработки когда нет доступа к файлу
        Используется для больших файлов, которые нельзя скачать через Bot API
        """
        logger.info(f"[LARGE_AUDIO] Используем альтернативный метод обработки для файла {file_id}")
        
        try:
            # Для больших файлов, которые нельзя скачать через Bot API,
            # возвращаем None, чтобы не создавать ложный транскрипт
            # Информационное сообщение будет показано в основном обработчике
            
            duration_estimate = file_size / (1024 * 1024) * 2  # Примерно 2 минуты на МБ
            
            logger.warning(f"[LARGE_AUDIO] Файл {file_id} размером {file_size / (1024*1024):.1f} МБ "
                          f"(~{duration_estimate:.1f} мин) не может быть обработан через Bot API")
            
            # Возвращаем None, чтобы основной обработчик показал информативное сообщение
            return None
            
        except Exception as e:
            logger.exception(f"[LARGE_AUDIO] Ошибка в альтернативном методе: {e}")
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