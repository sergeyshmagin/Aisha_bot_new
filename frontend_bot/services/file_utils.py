import os
from typing import Optional
import subprocess
import aiofiles
import aiofiles.os
import tempfile
import shutil
import asyncio

# Для корректной типизации рекомендуется установить stubs:
# pip install types-aiofiles


async def save_file(path: str, data: bytes) -> None:
    """Сохраняет данные в файл по указанному пути."""
    async with aiofiles.open(path, "wb") as f:
        await f.write(data)


async def async_exists(path: str) -> bool:
    """Асинхронно проверяет существование файла или директории."""
    try:
        await aiofiles.os.stat(path)
        return True
    except FileNotFoundError:
        return False


async def async_remove(path: str) -> None:
    """Асинхронно удаляет файл."""
    try:
        await aiofiles.os.remove(path)
    except FileNotFoundError:
        pass


async def async_getsize(path: str) -> int:
    """Асинхронно возвращает размер файла в байтах."""
    stat = await aiofiles.os.stat(path)
    return stat.st_size


async def async_makedirs(path: str, exist_ok: bool = True) -> None:
    """Асинхронно создаёт директорию (и родительские, если нужно)."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: os.makedirs(path, exist_ok=exist_ok))


async def async_rmtree(path: str) -> None:
    """Асинхронно удаляет директорию рекурсивно."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: shutil.rmtree(path, ignore_errors=True))


async def async_tempfile(
    suffix: str = "", mode: str = "w+b", encoding: Optional[str] = None
) -> str:
    """Асинхронно создаёт временный файл и возвращает путь к нему."""
    # Используем sync tempfile, но только для генерации имени и создания файла, без блокировки event loop
    loop = asyncio.get_running_loop()

    def _create():
        tf = tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix, mode=mode, encoding=encoding
        )
        tf.close()
        return tf.name

    return await loop.run_in_executor(None, _create)


def get_file_size(path: str) -> Optional[int]:
    """Возвращает размер файла в байтах, если файл существует."""
    if os.path.exists(path):
        return os.path.getsize(path)
    return None


def make_user_dir(base_dir: str, user_id: str) -> str:
    """Создаёт директорию пользователя и возвращает её путь."""
    user_dir = os.path.join(base_dir, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def is_audio_file_ffmpeg(path: str) -> bool:
    """
    Проверяет, что файл является аудиофайлом, который может быть обработан ffmpeg.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-of",
                "default=noprint_wrappers=1",
            ]
            + [path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        return b"codec_type=audio" in result.stdout
    except Exception:
        return False


async def is_valid_text_transcript(
    path: str, min_length: int = 1000, max_length: int = 100_000
) -> bool:
    """
    Проверяет, что файл является валидным текстовым транскриптом:
    - не пустой
    - содержит больше min_length символов
    - не содержит бинарных/нечитабельных символов
    """
    try:
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
        if not (min_length <= len(content) <= max_length):
            return False
        # Проверка на бинарные символы: если много не-ASCII, вероятно, файл не текстовый
        non_printable = sum(1 for c in content if ord(c) < 9 or (13 < ord(c) < 32))
        if non_printable > 0:
            return False
        return True
    except Exception:
        return False
