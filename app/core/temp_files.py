"""
Утилиты для работы с временными файлами
"""
import os
import tempfile
import uuid
from typing import Optional
from pathlib import Path

# Базовая директория для временных файлов
TEMP_BASE_DIR = "/app/storage/temp"

def ensure_temp_dir():
    """Создает директорию для временных файлов если её нет"""
    os.makedirs(TEMP_BASE_DIR, exist_ok=True)

def get_temp_file_path(suffix: str = "", prefix: str = "") -> str:
    """
    Создает путь для временного файла в нашей директории
    
    Args:
        suffix: Расширение файла (например, '.mp3')
        prefix: Префикс имени файла
        
    Returns:
        str: Полный путь к временному файлу
    """
    ensure_temp_dir()
    filename = f"{prefix}{uuid.uuid4()}{suffix}"
    return os.path.join(TEMP_BASE_DIR, filename)

class NamedTemporaryFile:
    """
    Замена для tempfile.NamedTemporaryFile, которая создает файлы в нашей директории
    """
    
    def __init__(self, suffix: str = "", prefix: str = "", delete: bool = True):
        self.suffix = suffix
        self.prefix = prefix
        self.delete = delete
        self.name = get_temp_file_path(suffix, prefix)
        self._file = None
    
    def __enter__(self):
        self._file = open(self.name, 'wb')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file:
            self._file.close()
        if self.delete and os.path.exists(self.name):
            try:
                os.unlink(self.name)
            except OSError:
                pass
    
    def write(self, data: bytes):
        """Записывает данные в файл"""
        if self._file:
            self._file.write(data)
    
    def flush(self):
        """Сбрасывает буфер"""
        if self._file:
            self._file.flush()

def mkdtemp(prefix: str = "") -> str:
    """
    Создает временную директорию в нашей базовой директории
    
    Args:
        prefix: Префикс имени директории
        
    Returns:
        str: Путь к созданной директории
    """
    ensure_temp_dir()
    dir_name = f"{prefix}{uuid.uuid4()}"
    dir_path = os.path.join(TEMP_BASE_DIR, dir_name)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def cleanup_temp_files(max_age_hours: int = 24):
    """
    Очищает старые временные файлы
    
    Args:
        max_age_hours: Максимальный возраст файлов в часах
    """
    import time
    
    if not os.path.exists(TEMP_BASE_DIR):
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for item in os.listdir(TEMP_BASE_DIR):
        item_path = os.path.join(TEMP_BASE_DIR, item)
        try:
            if os.path.isfile(item_path):
                file_age = current_time - os.path.getmtime(item_path)
                if file_age > max_age_seconds:
                    os.unlink(item_path)
            elif os.path.isdir(item_path):
                # Удаляем пустые директории
                try:
                    os.rmdir(item_path)
                except OSError:
                    pass  # Директория не пустая
        except OSError:
            pass  # Игнорируем ошибки доступа 