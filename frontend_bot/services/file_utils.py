import os
from typing import Optional
import subprocess


def save_file(path: str, data: bytes) -> None:
    """Сохраняет данные в файл по указанному пути."""
    with open(path, 'wb') as f:
        f.write(data)


def remove_file(path: str) -> None:
    """Удаляет файл, если он существует."""
    if os.path.exists(path):
        os.remove(path)


def file_exists(path: str) -> bool:
    """Проверяет существование файла."""
    return os.path.exists(path)


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
                "ffprobe", "-v", "error",
                "-show_streams",
                "-of", "default=noprint_wrappers=1"
            ] + [path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return b"codec_type=audio" in result.stdout
    except Exception:
        return False


def is_valid_text_transcript(path: str, min_length: int = 1000, max_length: int = 100_000) -> bool:
    """
    Проверяет, что файл является валидным текстовым транскриптом:
    - не пустой
    - содержит больше min_length символов
    - не содержит бинарных/нечитабельных символов
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if not (min_length <= len(content) <= max_length):
            return False
        # Проверка на бинарные символы: если много не-ASCII, вероятно, файл не текстовый
        non_printable = sum(
            1 for c in content if ord(c) < 9 or (13 < ord(c) < 32)
        )
        if non_printable > 0:
            return False
        return True
    except Exception:
        return False 