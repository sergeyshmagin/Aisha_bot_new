"""
Сервис для обработки транскрипций, аудиофайлов и генерации документов.
"""

import os
import aiofiles
import aiohttp
import asyncio
from datetime import datetime
from typing import List, NamedTuple, Optional
from frontend_bot.services.history import add_history_entry
from frontend_bot.utils.logger import get_logger
from frontend_bot.services.file_utils import (
    is_audio_file_ffmpeg,
    async_remove,
    async_getsize,
    async_makedirs,
    async_rmtree,
)
from uuid import uuid4
from frontend_bot.services import user_transcripts_store
from frontend_bot.shared.file_operations import AsyncFileManager
from frontend_bot.config import STORAGE_DIR, TRANSCRIBE_DIR
import logging
from pathlib import Path
import glob

logger = logging.getLogger(__name__)

async def ensure_transcribe_dirs(storage_dir: Path = STORAGE_DIR) -> None:
    """Создает необходимые директории для транскрипций."""
    transcribe_dir = storage_dir / TRANSCRIBE_DIR
    await AsyncFileManager.ensure_dir(storage_dir)
    await AsyncFileManager.ensure_dir(transcribe_dir)

async def save_transcribe_file(user_id: str, file_data: bytes, file_name: str, storage_dir: Path) -> Path:
    """Сохраняет файл для транскрибации."""
    await ensure_transcribe_dirs(storage_dir)
    user_dir = storage_dir / TRANSCRIBE_DIR / str(user_id)
    if not await AsyncFileManager.exists(user_dir):
        await AsyncFileManager.ensure_dir(user_dir)
    file_path = user_dir / file_name
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_data)
    await add_history_entry(user_id, file_name, str(file_path), storage_dir)
    return file_path

async def get_user_transcribe_files(user_id: str, storage_dir: Path) -> list[Path]:
    """Получает список файлов пользователя."""
    transcribe_dir = storage_dir / TRANSCRIBE_DIR
    user_dir = transcribe_dir / str(user_id)
    if not await AsyncFileManager.exists(user_dir):
        return []
    files = await AsyncFileManager.list_dir(user_dir)
    return [user_dir / f for f in files]

async def delete_transcribe_file(user_id: str, file_name: str, storage_dir: Path) -> bool:
    """Удаляет файл пользователя."""
    transcribe_dir = storage_dir / TRANSCRIBE_DIR
    file_path = transcribe_dir / str(user_id) / file_name
    if not await AsyncFileManager.exists(file_path):
        return False
    await AsyncFileManager.safe_remove(file_path)
    return True

async def cleanup_user_transcribe_files(user_id: str, storage_dir: Path) -> None:
    """Очищает все файлы пользователя."""
    transcribe_dir = storage_dir / TRANSCRIBE_DIR
    user_dir = transcribe_dir / str(user_id)
    if await AsyncFileManager.exists(user_dir):
        await AsyncFileManager.safe_rmtree(user_dir)

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
        async with aiofiles.open(temp_file, "wb") as f:
            await f.write(downloaded_file)
        logger.info(f"[save_audio_file] Файл сохранён: {temp_file}")
    except Exception as e:
        logger.exception(f"[save_audio_file] Ошибка: {e}")
        raise
    return temp_file


async def convert_to_mp3(input_path: str) -> str:
    """
    Конвертирует аудиофайл в mp3 через ffmpeg.
    :param input_path: исходный путь
    :return: путь к mp3-файлу
    """
    temp_file_mp3 = input_path.rsplit(".", 1)[0] + ".mp3"
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        temp_file_mp3,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Ошибка ffmpeg: {stderr.decode()}")
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
        text=True,
    )
    stdout, _ = await proc.communicate()
    duration = float(stdout.strip())

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
    for i, (start, end) in enumerate(segments):
        out_path = os.path.join(output_dir, f"chunk_{i+1}.ogg")
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-ss",
            str(start),
            "-to",
            str(end),
            "-c",
            "copy",
            out_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        chunk_paths.append(out_path)
    return chunk_paths


async def whisper_transcribe(audio_path: str, openai_api_key: str) -> str:
    """
    Транскрибирует аудиофайл через OpenAI Whisper API.
    :param audio_path: путь к аудиофайлу
    :param openai_api_key: ключ OpenAI
    :return: текст транскрипта
    """
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {openai_api_key}"}
    async with aiohttp.ClientSession() as session:
        async with aiofiles.open(audio_path, "rb") as f:
            form = aiohttp.FormData()
            data = await f.read()
            form.add_field("file", data, filename=os.path.basename(audio_path))
            form.add_field("model", "whisper-1")
            async with session.post(url, data=form, headers=headers) as resp:
                resp.raise_for_status()
                response = await resp.json()
                return response["text"]


class TranscribeResult(NamedTuple):
    success: bool
    transcript_path: Optional[str]
    error: Optional[str]


async def process_audio(
    message, bot, openai_api_key, storage_dir, transcripts_dir
) -> TranscribeResult:
    """
    Обрабатывает аудиосообщение: сохраняет, проверяет, транскрибирует, возвращает результат.
    :param message: объект сообщения Telegram
    :param bot: экземпляр бота
    :param openai_api_key: ключ OpenAI
    :param storage_dir: директория для хранения
    :param transcripts_dir: директория для транскриптов
    :return: TranscribeResult
    """
    try:
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        ext = ".ogg" if message.voice else ".mp3"
        temp_file = await save_audio_file(file_id, ext, bot, storage_dir)
        is_audio = await is_audio_file_ffmpeg(temp_file)
        if not is_audio:
            await async_remove(temp_file)
            return TranscribeResult(False, None, "unsupported_format")
        temp_file_mp3 = await convert_to_mp3(temp_file)
        # Удаляем исходный файл сразу после конвертации
        await async_remove(temp_file)
        file_size = await async_getsize(temp_file_mp3)
        user_id = message.from_user.id
        user_dir = os.path.join(transcripts_dir, str(user_id))
        await async_makedirs(user_dir, exist_ok=True)
        if file_size <= 25 * 1024 * 1024:
            transcription = await whisper_transcribe(temp_file_mp3, openai_api_key)
            filename = f"transcript_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
            transcript_path = os.path.join(user_dir, filename)
            async with aiofiles.open(transcript_path, "w", encoding="utf-8") as f:
                await f.write(transcription)
            await add_history_entry(
                str(user_id), os.path.basename(transcript_path), transcript_path
            )
            await user_transcripts_store.set(user_id, transcript_path)
            await async_remove(temp_file_mp3)
            return TranscribeResult(True, transcript_path, None)
        else:
            # Нарезка и обработка кусков (упрощённо)
            chunk_dir = os.path.join(storage_dir, f"chunks_{uuid4()}")
            await async_makedirs(chunk_dir, exist_ok=True)
            chunk_paths = await split_audio_by_silence_ffmpeg(temp_file, chunk_dir)
            await async_remove(temp_file)
            await async_remove(temp_file_mp3)
            transcribed_text = ""
            for i, part_path in enumerate(chunk_paths):
                try:
                    part_mp3 = await convert_to_mp3(part_path)
                    part_text = await whisper_transcribe(part_mp3, openai_api_key)
                    transcribed_text += f"\n--- Часть {i+1} ---\n{part_text}\n"
                except Exception:
                    transcribed_text += (
                        f"\n--- Часть {i+1} ---\nОшибка при расшифровке.\n"
                    )
                finally:
                    await async_remove(part_path)
                    await async_remove(part_mp3)
            await async_rmtree(chunk_dir)
            filename = f"transcript_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
            transcript_path = os.path.join(user_dir, filename)
            async with aiofiles.open(transcript_path, "w", encoding="utf-8") as f:
                await f.write(transcribed_text)
            await add_history_entry(
                str(user_id), os.path.basename(transcript_path), transcript_path
            )
            await user_transcripts_store.set(user_id, transcript_path)
            return TranscribeResult(True, transcript_path, None)
    except Exception as e:
        return TranscribeResult(False, None, str(e))

async def delete_user_transcripts(user_id: str, storage_dir: Path = STORAGE_DIR) -> None:
    """
    Удаляет все файлы пользователя из transcripts/{user_id} и все chunk-папки пользователя.
    """
    # Удаляем папку с транскриптами пользователя
    transcripts_dir = storage_dir / "transcripts" / str(user_id)
    if await AsyncFileManager.exists(transcripts_dir):
        await AsyncFileManager.safe_rmtree(transcripts_dir)
    # Удаляем все chunk-папки пользователя
    chunk_glob = str(storage_dir / f"chunks_*")
    for chunk_path in glob.glob(chunk_glob):
        if os.path.isdir(chunk_path) and str(user_id) in chunk_path:
            await AsyncFileManager.safe_rmtree(Path(chunk_path))
