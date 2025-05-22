"""
Модуль для хранения аудио файлов
"""
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
from aisha_v2.app.core.config import settings
from aisha_v2.app.services.audio_processing.types import AudioStorage
from aisha_v2.app.core.exceptions import AudioProcessingError

logger = logging.getLogger(__name__)

class LocalAudioStorage(AudioStorage):
    """Локальное хранилище аудио файлов"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or settings.AUDIO_STORAGE_PATH
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Создает директорию для хранения, если она не существует"""
        try:
            Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Ошибка при создании директории хранения: {e}")
            raise AudioProcessingError(f"Ошибка инициализации хранилища: {str(e)}")
    
    async def save(self, audio_data: bytes, filename: Optional[str] = None) -> str:
        """
        Сохраняет аудио файл
        
        Args:
            audio_data: Аудио данные
            filename: Имя файла (если не указано, генерируется UUID)
            
        Returns:
            str: Путь к сохраненному файлу
            
        Raises:
            AudioProcessingError: При ошибке сохранения
        """
        try:
            # Генерируем имя файла, если не указано
            if not filename:
                filename = f"{uuid.uuid4()}.mp3"
            
            # Создаем путь к файлу
            file_path = Path(self.storage_path) / filename
            
            # Сохраняем файл
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(audio_data)
            
            logger.info(f"Аудио файл сохранен: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении аудио: {e}")
            raise AudioProcessingError(f"Ошибка сохранения: {str(e)}")
    
    async def load(self, filename: str) -> bytes:
        """
        Загружает аудио файл
        
        Args:
            filename: Имя файла
            
        Returns:
            bytes: Аудио данные
            
        Raises:
            AudioProcessingError: При ошибке загрузки
        """
        try:
            # Создаем путь к файлу
            file_path = Path(self.storage_path) / filename
            
            # Проверяем существование файла
            if not file_path.exists():
                raise AudioProcessingError(f"Файл не найден: {filename}")
            
            # Загружаем файл
            async with aiofiles.open(file_path, 'rb') as f:
                data = await f.read()
            
            logger.info(f"Аудио файл загружен: {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке аудио: {e}")
            raise AudioProcessingError(f"Ошибка загрузки: {str(e)}")
    
    async def delete(self, filename: str) -> bool:
        """
        Удаляет аудио файл
        
        Args:
            filename: Имя файла
            
        Returns:
            bool: True если файл удален, иначе False
            
        Raises:
            AudioProcessingError: При ошибке удаления
        """
        try:
            # Создаем путь к файлу
            file_path = Path(self.storage_path) / filename
            
            # Проверяем существование файла
            if not file_path.exists():
                logger.warning(f"Файл не найден при удалении: {filename}")
                return False
            
            # Удаляем файл
            file_path.unlink()
            
            logger.info(f"Аудио файл удален: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при удалении аудио: {e}")
            raise AudioProcessingError(f"Ошибка удаления: {str(e)}")
    
    async def cleanup_old_files(self, max_age_days: int = 7):
        """
        Удаляет старые файлы
        
        Args:
            max_age_days: Максимальный возраст файлов в днях
            
        Raises:
            AudioProcessingError: При ошибке очистки
        """
        try:
            # Получаем текущее время
            now = datetime.now()
            
            # Проходим по всем файлам
            for file_path in Path(self.storage_path).glob('*'):
                if not file_path.is_file():
                    continue
                
                # Получаем время создания файла
                created = datetime.fromtimestamp(file_path.stat().st_ctime)
                
                # Проверяем возраст файла
                age = (now - created).days
                if age > max_age_days:
                    # Удаляем старый файл
                    file_path.unlink()
                    logger.info(f"Удален старый файл: {file_path}")
            
        except Exception as e:
            logger.error(f"Ошибка при очистке старых файлов: {e}")
            raise AudioProcessingError(f"Ошибка очистки: {str(e)}") 