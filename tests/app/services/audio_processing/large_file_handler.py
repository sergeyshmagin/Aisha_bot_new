"""
Обработчик больших аудио файлов (>20MB)
Использует прямые ссылки Telegram для скачивания файлов больше лимита Bot API
"""
import aiohttp
import asyncio
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from io import BytesIO

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

class LargeFileHandler:
    """Обработчик больших файлов через прямые ссылки Telegram"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/file/bot{bot_token}"
    
    async def download_large_file(self, file_path: str, max_size: int = 1024 * 1024 * 1024) -> Optional[bytes]:
        """
        Скачивает большой файл по прямой ссылке
        
        Args:
            file_path: Путь к файлу из Telegram API
            max_size: Максимальный размер файла в байтах (по умолчанию 1GB)
            
        Returns:
            bytes: Содержимое файла или None при ошибке
        """
        try:
            url = f"{self.base_url}/{file_path}"
            logger.info(f"Скачивание большого файла: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка скачивания файла: HTTP {response.status}")
                        return None
                    
                    # Проверяем размер файла
                    content_length = response.headers.get('content-length')
                    if content_length:
                        file_size = int(content_length)
                        if file_size > max_size:
                            logger.error(f"Файл слишком большой: {file_size} байт (лимит: {max_size})")
                            return None
                        
                        logger.info(f"Размер файла: {file_size / (1024*1024):.1f} МБ")
                    
                    # Скачиваем файл по частям
                    data = BytesIO()
                    downloaded = 0
                    
                    async for chunk in response.content.iter_chunked(8192):  # 8KB chunks
                        data.write(chunk)
                        downloaded += len(chunk)
                        
                        # Проверяем лимит во время скачивания
                        if downloaded > max_size:
                            logger.error(f"Превышен лимит размера файла: {downloaded} байт")
                            return None
                        
                        # Логируем прогресс для больших файлов
                        if downloaded % (10 * 1024 * 1024) == 0:  # Каждые 10MB
                            logger.info(f"Скачано: {downloaded / (1024*1024):.1f} МБ")
                    
                    logger.info(f"Файл успешно скачан: {downloaded / (1024*1024):.1f} МБ")
                    return data.getvalue()
                    
        except Exception as e:
            logger.exception(f"Ошибка при скачивании большого файла: {e}")
            return None
    
    async def download_to_temp_file(self, file_path: str, max_size: int = 1024 * 1024 * 1024) -> Optional[str]:
        """
        Скачивает большой файл во временный файл
        
        Args:
            file_path: Путь к файлу из Telegram API
            max_size: Максимальный размер файла в байтах
            
        Returns:
            str: Путь к временному файлу или None при ошибке
        """
        try:
            url = f"{self.base_url}/{file_path}"
            logger.info(f"Скачивание большого файла во временный файл: {url}")
            
            # Создаем временный файл
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
            temp_path = temp_file.name
            temp_file.close()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка скачивания файла: HTTP {response.status}")
                        Path(temp_path).unlink(missing_ok=True)
                        return None
                    
                    # Проверяем размер файла
                    content_length = response.headers.get('content-length')
                    if content_length:
                        file_size = int(content_length)
                        if file_size > max_size:
                            logger.error(f"Файл слишком большой: {file_size} байт (лимит: {max_size})")
                            Path(temp_path).unlink(missing_ok=True)
                            return None
                    
                    # Скачиваем файл по частям
                    downloaded = 0
                    
                    with open(temp_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Проверяем лимит во время скачивания
                            if downloaded > max_size:
                                logger.error(f"Превышен лимит размера файла: {downloaded} байт")
                                Path(temp_path).unlink(missing_ok=True)
                                return None
                            
                            # Логируем прогресс для больших файлов
                            if downloaded % (10 * 1024 * 1024) == 0:  # Каждые 10MB
                                logger.info(f"Скачано: {downloaded / (1024*1024):.1f} МБ")
                    
                    logger.info(f"Файл успешно скачан во временный файл: {temp_path} ({downloaded / (1024*1024):.1f} МБ)")
                    return temp_path
                    
        except Exception as e:
            logger.exception(f"Ошибка при скачивании большого файла: {e}")
            # Удаляем временный файл при ошибке
            if 'temp_path' in locals():
                Path(temp_path).unlink(missing_ok=True)
            return None
    
    def cleanup_temp_file(self, temp_path: str) -> None:
        """Удаляет временный файл"""
        try:
            Path(temp_path).unlink(missing_ok=True)
            logger.debug(f"Временный файл удален: {temp_path}")
        except Exception as e:
            logger.warning(f"Ошибка при удалении временного файла {temp_path}: {e}") 