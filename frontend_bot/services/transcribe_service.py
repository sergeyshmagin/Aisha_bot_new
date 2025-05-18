"""
Сервис для обработки транскрипций, аудиофайлов и генерации документов.
"""

import os
import aiohttp
import asyncio
from datetime import datetime
from typing import List, NamedTuple, Optional
from frontend_bot.utils.logger import get_logger
from frontend_bot.services.file_utils import (
    is_audio_file_ffmpeg,
    async_remove,
    async_getsize,
    async_rmtree,
)
from uuid import uuid4
from frontend_bot.shared.file_operations import AsyncFileManager
from frontend_bot.config import settings
import logging
from pathlib import Path
import glob
from frontend_bot.services.transcript_service import TranscriptService
from minio import Minio
from database.models import UserTranscript
from shared_storage.storage_utils import upload_file, download_file, delete_file
import aiofiles
import async_timeout

logger = logging.getLogger(__name__)

# Инициализация MinIO клиента и сервиса транскриптов
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)
transcript_service = TranscriptService(minio_client)

async def ensure_transcribe_dirs(storage_dir: Path = settings.STORAGE_DIR) -> None:
    """Создает необходимые директории для транскрипций."""
    transcribe_dir = storage_dir / settings.TRANSCRIPTS_PATH
    await AsyncFileManager.ensure_dir(storage_dir)
    await AsyncFileManager.ensure_dir(transcribe_dir)

async def save_audio_file(file_id: str, ext: str, bot, storage_dir: str) -> str:
    """
    Сохраняет аудиофайл, загруженный пользователем, во временную директорию.
    :param file_id: file_id из Telegram
    :param ext: расширение файла
    :param bot: экземпляр бота
    :param storage_dir: директория для хранения
    :return: путь к сохранённому файлу
    """
    logger = get_logger("transcribe_service")
    logger.info(
        f"[save_audio_file] file_id={file_id}, ext={ext}, storage_dir={storage_dir}"
    )
    temp_file = os.path.join(storage_dir, f"{datetime.now().timestamp()}{ext}")
    try:
        file_info = await bot.get_file(file_id)
        logger.info(f"[save_audio_file] file_info: {file_info}")
        downloaded_file = await bot.download_file(file_info.file_path)
        logger.info(f"[save_audio_file] downloaded_file: {len(downloaded_file)} bytes")
        
        # Сохраняем во временную директорию для обработки
        async with aiofiles.open(temp_file, "wb") as f:
            await f.write(downloaded_file)
        logger.info(f"[save_audio_file] Файл сохранён: {temp_file}")
        
        # Загружаем в MinIO
        object_name = f"temp/{os.path.basename(temp_file)}"
        await upload_file(
            bucket=settings.MINIO_BUCKETS["temp"],
            object_name=object_name,
            data=downloaded_file,
            content_type="audio/ogg"
        )
        logger.info(f"[save_audio_file] Файл загружен в MinIO: {object_name}")
        
    except Exception as e:
        logger.exception(f"[save_audio_file] Ошибка: {e}")
        raise
    return temp_file


async def check_ffmpeg() -> bool:
    """
    Проверяет наличие и работоспособность ffmpeg.
    :return: True если ffmpeg доступен и работает
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0
    except FileNotFoundError:
        return False

async def convert_to_mp3(input_path: str) -> str:
    """
    Конвертирует аудиофайл в mp3 через ffmpeg.
    :param input_path: исходный путь
    :return: путь к mp3-файлу
    :raises RuntimeError: если ffmpeg не установлен или произошла ошибка конвертации
    """
    if not await check_ffmpeg():
        raise RuntimeError("ffmpeg не установлен или недоступен")

    temp_file_mp3 = input_path.rsplit(".", 1)[0] + ".mp3"
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-acodec", "libmp3lame",  # Явно указываем кодек
        "-ab", "192k",  # Битрейт
        temp_file_mp3,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Ошибка ffmpeg при конвертации: {stderr.decode()}")
    return temp_file_mp3


async def split_audio_by_silence_ffmpeg(
    input_path: str,
    output_dir: str,
    min_silence_len: float = 0.7,
    silence_thresh: int = -30,
) -> List[str]:
    """
    Нарезает аудиофайл на части по паузам с помощью ffmpeg.
    :param input_path: путь к исходному аудиофайлу
    :param output_dir: директория для сохранения кусков
    :param min_silence_len: минимальная длина тишины (секунды)
    :param silence_thresh: уровень тишины в dB (относительно 0)
    :return: список путей к кускам
    """
    logger = get_logger("transcribe_service")
    # Получаем длительность файла
    proc = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        input_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error(f"[split_audio_by_silence_ffmpeg] ffprobe error: {stderr.decode()}")
        raise RuntimeError(f"ffprobe error: {stderr.decode()}")
    duration = float(stdout.decode().strip())
    # Запускаем ffmpeg для поиска пауз
    command = [
        "ffmpeg",
        "-i",
        input_path,
        "-af",
        f"silencedetect=noise={silence_thresh}dB:d={min_silence_len}",
        "-f",
        "null",
        "-",
    ]
    proc = await asyncio.create_subprocess_exec(
        *command, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    stderr_str = stderr.decode()
    if proc.returncode != 0:
        logger.error(f"[split_audio_by_silence_ffmpeg] ffmpeg silencedetect error: {stderr_str}")
        raise RuntimeError(f"ffmpeg silencedetect error: {stderr_str}")
    silence_starts = []
    silence_ends = []
    for line in stderr_str.splitlines():
        if "silence_start" in line:
            silence_starts.append(float(line.split("silence_start: ")[-1]))
        if "silence_end" in line:
            silence_ends.append(float(line.split("silence_end: ")[-1].split(" |") [0]))
    # Формируем интервалы для нарезки
    segments = []
    prev_end = 0.0
    for start in silence_starts:
        segments.append((prev_end, start))
        prev_end = start
    if prev_end < duration:
        segments.append((prev_end, duration))
    chunk_paths = []
    for i, (start, end) in enumerate(segments):
        out_path = os.path.join(output_dir, f"chunk_{i+1}.mp3")
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-ss",
            str(start),
            "-to",
            str(end),
            "-acodec", "libmp3lame",  # Явно указываем кодек
            "-ab", "192k",  # Битрейт
            out_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, chunk_stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error(f"[split_audio_by_silence_ffmpeg] ffmpeg chunk error: {chunk_stderr.decode()}")
            raise RuntimeError(f"ffmpeg chunk error: {chunk_stderr.decode()}")
        chunk_paths.append(out_path)
    logger.info(f"[split_audio_by_silence_ffmpeg] Сформировано чанков: {len(chunk_paths)} | {chunk_paths}")
    return chunk_paths


async def whisper_transcribe(audio_path: str, openai_api_key: str = settings.OPENAI_API_KEY) -> str:
    """
    Транскрибирует аудиофайл через OpenAI Whisper API с retry-механикой.
    :param audio_path: путь к аудиофайлу
    :param openai_api_key: ключ OpenAI
    :return: текст транскрипта
    """
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Accept": "application/json"
    }
    max_retries = 3
    delay = 1
    for attempt in range(1, max_retries + 1):
        try:
            if not os.path.exists(audio_path):
                raise RuntimeError(f"Файл {audio_path} не существует")
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                raise RuntimeError(f"Файл {audio_path} пустой")
            logger.info(f"[whisper_transcribe] Попытка {attempt}: отправка файла {audio_path} размером {file_size} байт")
            async with aiohttp.ClientSession() as session:
                async with aiofiles.open(audio_path, "rb") as f:
                    form = aiohttp.FormData()
                    data = await f.read()
                    form.add_field(
                        "file",
                        data,
                        filename=os.path.basename(audio_path),
                        content_type="audio/mpeg"
                    )
                    form.add_field("model", "whisper-1")
                    form.add_field("language", "ru")
                    form.add_field("response_format", "json")
                    logger.info("[whisper_transcribe] Отправка запроса к API")
                    async with async_timeout.timeout(60):
                        async with session.post(url, data=form, headers=headers) as resp:
                            logger.info(f"[whisper_transcribe] status={resp.status}, headers={dict(resp.headers)}")
                            try:
                                response = await resp.json()
                                logger.info(f"[whisper_transcribe] Получен ответ: {response}")
                            except Exception as json_exc:
                                text_body = await resp.text()
                                logger.error(f"[whisper_transcribe] Ошибка декодирования JSON: {json_exc}. Тело ответа: {text_body[:500]}")
                                # Retry только для 502/504 и сетевых ошибок
                                if resp.status in (502, 504) or "502 Bad Gateway" in text_body or "504 Gateway" in text_body:
                                    if attempt < max_retries:
                                        logger.warning(f"[whisper_transcribe] Попытка {attempt} неудачна (502/504). Жду {delay} сек и повторяю...")
                                        await asyncio.sleep(delay)
                                        delay *= 2
                                        continue
                                raise RuntimeError(f"Ошибка декодирования JSON: {json_exc}. Тело ответа: {text_body[:500]}")
                            if resp.status != 200:
                                logger.error(f"[whisper_transcribe] Ошибка API Whisper: {response}")
                                # Retry только для 502/504
                                if resp.status in (502, 504):
                                    if attempt < max_retries:
                                        logger.warning(f"[whisper_transcribe] Попытка {attempt} неудачна (502/504). Жду {delay} сек и повторяю...")
                                        await asyncio.sleep(delay)
                                        delay *= 2
                                        continue
                                raise RuntimeError(f"Ошибка API Whisper: {response}")
                            if "text" not in response:
                                logger.error(f"[whisper_transcribe] Неожиданный ответ API: {response}")
                                raise RuntimeError("Неожиданный формат ответа от API")
                            return response["text"]
        except (aiohttp.ClientError, asyncio.TimeoutError) as net_exc:
            logger.error(f"[whisper_transcribe] Сетевая ошибка: {net_exc}")
            if attempt < max_retries:
                logger.warning(f"[whisper_transcribe] Попытка {attempt} неудачна (сетевая ошибка). Жду {delay} сек и повторяю...")
                await asyncio.sleep(delay)
                delay *= 2
                continue
            raise RuntimeError(f"Сетевая ошибка при транскрибации: {net_exc}")
        except Exception as e:
            logger.error(f"[whisper_transcribe] Ошибка при транскрибации аудио: {str(e)}")
            raise RuntimeError(f"Ошибка транскрибации: {str(e)}")
    raise RuntimeError("Не удалось получить транскрипт после нескольких попыток (502/504/сеть)")


class TranscribeResult(NamedTuple):
    success: bool
    transcript_path: Optional[str]
    error: Optional[str]


async def process_audio(
    message, bot, openai_api_key, storage_dir, transcripts_dir, user_uuid
) -> TranscribeResult:
    """
    Обрабатывает аудиофайл:
    1. Сохраняет файл
    2. Проверяет ffmpeg
    3. Конвертирует в mp3
    4. Разбивает на части
    5. Транскрибирует каждую часть
    6. Объединяет результаты
    7. Очищает временные файлы
    """
    temp_files = []  # Список для отслеживания временных файлов
    try:
        # Получаем информацию о файле
        file_info = await bot.get_file(message.voice.file_id)
        file_size = file_info.file_size
        # Проверяем размер файла
        if file_size > settings.MAX_FILE_SIZE:
            return TranscribeResult(
                success=False,
                error="file_too_large",
                transcript_path=""
            )
        # Создаем директорию для пользователя
        user_dir = os.path.join(transcripts_dir, str(message.from_user.id))
        os.makedirs(user_dir, exist_ok=True)
        # Сохраняем файл
        file_path = await save_audio_file(
            message.voice.file_id,
            ".ogg",
            bot,
            storage_dir
        )
        temp_files.append(file_path)
        try:
            # Проверяем ffmpeg
            if not await check_ffmpeg():
                return TranscribeResult(
                    success=False,
                    error="ffmpeg_not_found",
                    transcript_path=""
                )
            logger.info(f"[process_audio] Конвертация {file_path} в mp3...")
            # Конвертируем в mp3
            mp3_path = await convert_to_mp3(file_path)
            logger.info(f"[process_audio] mp3-файл создан: {mp3_path}")
            temp_files.append(mp3_path)
            logger.info(f"[process_audio] Нарезка {mp3_path} на чанки...")
            # Разбиваем на части
            chunks = await split_audio_by_silence_ffmpeg(
                mp3_path,
                user_dir,  # Сохраняем чанки в директорию пользователя
                min_silence_len=0.7,
                silence_thresh=-30
            )
            logger.info(f"[process_audio] Получено чанков: {len(chunks)} | {chunks}")
            if not chunks:
                logger.error(f"[process_audio] Не удалось нарезать аудио на чанки. Список пуст. mp3_path={mp3_path}")
                raise RuntimeError(f"Не удалось нарезать аудио на чанки. mp3_path={mp3_path}")
            # Проверяем, что все чанки существуют и не пустые
            for chunk in chunks:
                if not os.path.exists(chunk):
                    logger.error(f"[process_audio] Чанк не найден: {chunk}")
                    raise RuntimeError(f"Чанк не найден: {chunk}")
                if os.path.getsize(chunk) == 0:
                    logger.error(f"[process_audio] Чанк пустой: {chunk}")
                    raise RuntimeError(f"Чанк пустой: {chunk}")
            temp_files.extend(chunks)  # Добавляем чанки в список для удаления
            # Транскрибируем каждую часть
            transcripts = []
            for chunk in chunks:
                logger.info(f"[process_audio] Транскрибация чанка: {chunk}")
                transcript = await whisper_transcribe(chunk, openai_api_key)
                transcripts.append(transcript)
            # Объединяем результаты
            full_transcript = " ".join(transcripts)
            # Сохраняем транскрипт в MinIO
            transcript_filename = f"transcript_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
            object_name = f"{user_uuid}/{transcript_filename}"
            # Сначала сохраняем локально
            local_path = os.path.join(user_dir, transcript_filename)
            async with aiofiles.open(local_path, "w", encoding="utf-8") as f:
                await f.write(full_transcript)
            # Затем загружаем в MinIO
            async with aiofiles.open(local_path, "rb") as f:
                data = await f.read()
            await upload_file(
                bucket=settings.MINIO_BUCKETS["transcripts"],
                object_name=object_name,
                data=data,
                content_type="text/plain"
            )
            return TranscribeResult(
                success=True,
                error="",
                transcript_path=local_path
            )
        except RuntimeError as e:
            logger.error(f"[process_audio] RuntimeError: {str(e)}")
            return TranscribeResult(
                success=False,
                error=str(e),
                transcript_path=""
            )
    except Exception as e:
        logger.error(f"Ошибка при обработке аудио: {str(e)}")
        return TranscribeResult(
            success=False,
            error="processing_error",
            transcript_path=""
        )
    finally:
        # Очищаем временные файлы
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    await async_remove(temp_file)
                    # Также удаляем из MinIO
                    object_name = f"temp/{os.path.basename(temp_file)}"
                    await delete_file(
                        bucket=settings.MINIO_BUCKETS["temp"],
                        object_name=object_name
                    )
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла {temp_file}: {str(e)}")

async def cleanup_old_transcripts(user_id: str, max_age_days: int = 7) -> None:
    """
    Удаляет старые транскрипты пользователя.
    :param user_id: ID пользователя
    :param max_age_days: максимальный возраст файлов в днях
    """
    user_dir = os.path.join(settings.TRANSCRIPTS_PATH, str(user_id))
    if not os.path.exists(user_dir):
        return
        
    current_time = datetime.now()
    for filename in os.listdir(user_dir):
        file_path = os.path.join(user_dir, filename)
        if not filename.startswith("transcript_"):
            continue
            
        try:
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
            age_days = (current_time - file_time).days
            if age_days > max_age_days:
                # Удаляем локальный файл
                await async_remove(file_path)
                # Удаляем из MinIO
                object_name = f"{user_id}/{filename}"
                await delete_file(
                    bucket=settings.MINIO_BUCKETS["transcripts"],
                    object_name=object_name
                )
        except Exception as e:
            logger.error(f"Ошибка при удалении старого транскрипта {file_path}: {str(e)}")

async def delete_user_transcripts(user_id: str, storage_dir: Path = settings.STORAGE_DIR) -> None:
    """Удаляет все транскрипты пользователя."""
    transcribe_dir = storage_dir / settings.TRANSCRIPTS_PATH
    user_dir = transcribe_dir / str(user_id)
    if user_dir.exists():
        await async_rmtree(user_dir)
