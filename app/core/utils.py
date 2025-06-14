"""
Утилиты для работы с аудио и файлами
"""
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.exceptions.audio_exceptions import AudioProcessingError
from app.core.constants import MAX_AUDIO_SIZE

logger = logging.getLogger(__name__)

def setup_logging() -> None:
    """Настройка логирования"""
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        filename=settings.LOG_FILE,
    )

def get_file_size(file_path: Path) -> int:
    """Получить размер файла в байтах"""
    try:
        return os.path.getsize(file_path)
    except OSError as e:
        raise AudioProcessingError(f"Ошибка при получении размера файла: {e}")

def validate_audio_file(file_path: Path) -> None:
    """Проверка аудио файла"""
    if not file_path.exists():
        raise AudioProcessingError(f"Файл не найден: {file_path}")
    
    if not file_path.is_file():
        raise AudioProcessingError(f"Путь не является файлом: {file_path}")
    
    size = get_file_size(file_path)
    if size > MAX_AUDIO_SIZE:
        raise AudioProcessingError(
            f"Размер файла превышает максимально допустимый: {size} > {MAX_AUDIO_SIZE}"
        )
    
    extension = file_path.suffix.lower().lstrip(".")
    if extension not in settings.AUDIO_FORMATS:
        raise AudioProcessingError(
            f"Неподдерживаемый формат файла: {extension}. "
            f"Поддерживаемые форматы: {', '.join(settings.AUDIO_FORMATS)}"
        )

def get_storage_path(filename: str) -> Path:
    """Получить путь для сохранения файла"""
    return settings.AUDIO_STORAGE_PATH / filename



def format_duration(seconds: float) -> str:
    """Форматирование длительности в читаемый вид"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def format_size(size_bytes: int) -> str:
    """Форматирование размера в читаемый вид"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB" 