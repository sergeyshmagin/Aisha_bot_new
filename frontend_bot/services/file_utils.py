"""
Утилиты для работы с файлами.
"""

import logging
from pathlib import Path
from typing import Optional, List
import mimetypes
import uuid
import aiofiles.os

from frontend_bot.shared.file_operations import AsyncFileManager
from frontend_bot.config import settings

logger = logging.getLogger(__name__)

async def async_exists(path: Path) -> bool:
    """
    Проверяет существование файла или директории.
    
    Args:
        path: Путь к файлу или директории
        
    Returns:
        bool: True если файл или директория существует
    """
    return await AsyncFileManager.exists(path)

async def async_makedirs(path: Path, exist_ok: bool = True) -> None:
    """
    Создает директорию и все необходимые родительские директории.
    
    Args:
        path: Путь к директории
        exist_ok: Если True, не вызывает исключение если директория уже существует
    """
    await AsyncFileManager.ensure_dir(path)

async def async_remove(path: Path) -> None:
    """
    Удаляет файл.
    
    Args:
        path: Путь к файлу
    """
    await AsyncFileManager.safe_remove(path)

async def async_rmtree(path: Path) -> None:
    """
    Рекурсивно удаляет директорию и все её содержимое.
    
    Args:
        path: Путь к директории
    """
    await AsyncFileManager.safe_rmtree(path)

async def async_getsize(path: Path) -> Optional[int]:
    """
    Получает размер файла.
    
    Args:
        path: Путь к файлу
        
    Returns:
        Optional[int]: Размер файла в байтах или None если файл не существует
    """
    return await AsyncFileManager.get_size(path)

class FileUtils:
    """Утилиты для работы с файлами."""
    
    def __init__(self, storage_dir: Path = settings.STORAGE_DIR):
        """
        Инициализация утилит для работы с файлами.
        
        Args:
            storage_dir: Директория для хранения файлов
        """
        self.storage_dir = storage_dir
    
    async def _ensure_storage_dir(self) -> None:
        """Создает директорию для хранения, если она не существует."""
        await AsyncFileManager.ensure_dir(self.storage_dir)
    
    async def save_file(self, file_data: bytes, file_name: str) -> Path:
        """
        Сохраняет файл в хранилище.
        
        Args:
            file_data: Бинарные данные файла
            file_name: Имя файла
            
        Returns:
            Path: Путь к сохраненному файлу
        """
        await self._ensure_storage_dir()
        
        # Генерируем уникальное имя файла
        file_id = str(uuid.uuid4())
        file_ext = Path(file_name).suffix
        new_file_name = f"{file_id}{file_ext}"
        
        file_path = self.storage_dir / new_file_name
        await AsyncFileManager.write_binary(file_path, file_data)
        
        return file_path
    
    async def get_file_size(self, file_path: Path) -> Optional[int]:
        """
        Получает размер файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Optional[int]: Размер файла в байтах или None если файл не существует
        """
        return await AsyncFileManager.get_size(file_path)
    
    async def is_file_too_large(self, file_path: Path) -> bool:
        """
        Проверяет, превышает ли файл максимальный размер.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            bool: True если файл превышает максимальный размер
        """
        size = await self.get_file_size(file_path)
        if size is None:
            return False
        return size > settings.MAX_FILE_SIZE
    
    async def get_file_type(self, file_path: Path) -> str:
        """
        Определяет тип файла по расширению.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            str: MIME-тип файла
        """
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"
    
    async def is_valid_file_type(self, file_path: Path, allowed_types: List[str]) -> bool:
        """
        Проверяет, является ли тип файла допустимым.
        
        Args:
            file_path: Путь к файлу
            allowed_types: Список допустимых MIME-типов
            
        Returns:
            bool: True если тип файла допустим
        """
        file_type = await self.get_file_type(file_path)
        return file_type in allowed_types
    
    async def delete_file(self, file_path: Path) -> None:
        """
        Удаляет файл.
        
        Args:
            file_path: Путь к файлу
        """
        await AsyncFileManager.safe_remove(file_path)
    
    async def list_files(self, pattern: str = "*") -> List[Path]:
        """
        Получает список файлов в хранилище.
        
        Args:
            pattern: Шаблон для поиска файлов
            
        Returns:
            List[Path]: Список путей к файлам
        """
        await self._ensure_storage_dir()
        files = await AsyncFileManager.list_dir(self.storage_dir)
        return [self.storage_dir / f for f in files if Path(f).match(pattern)]

async def is_audio_file_ffmpeg(file_path: Path) -> bool:
    """
    Проверяет, является ли файл аудиофайлом (по расширению).
    """
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type is not None and mime_type.startswith("audio")
