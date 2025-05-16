"""
Асинхронный менеджер для работы с файлами.
Централизует все файловые операции в проекте.
"""

import os
import shutil
import asyncio
import logging
from pathlib import Path
from typing import Optional, Union, List
import aiofiles
import aiofiles.os

logger = logging.getLogger(__name__)

class AsyncFileManager:
    """Асинхронный менеджер для работы с файлами."""
    
    @staticmethod
    async def ensure_dir(path: Union[str, Path]) -> None:
        """
        Асинхронно создает директорию, если она не существует.
        
        Args:
            path: Путь к директории
        """
        try:
            await aiofiles.os.makedirs(str(path), exist_ok=True)
            logger.debug(f"Directory ensured: {path}")
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            raise
    
    @staticmethod
    async def safe_remove(path: Union[str, Path]) -> None:
        """
        Безопасно удаляет файл, игнорируя ошибки если файл не существует.
        
        Args:
            path: Путь к файлу
        """
        try:
            await aiofiles.os.remove(str(path))
            logger.debug(f"File removed: {path}")
        except FileNotFoundError:
            logger.debug(f"File not found (ignored): {path}")
        except Exception as e:
            logger.error(f"Error removing file {path}: {e}")
            raise
    
    @staticmethod
    async def safe_rmtree(path: Union[str, Path]) -> None:
        """
        Безопасно удаляет директорию рекурсивно.
        
        Args:
            path: Путь к директории
        """
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: shutil.rmtree(str(path), ignore_errors=True))
            logger.debug(f"Directory tree removed: {path}")
        except Exception as e:
            logger.error(f"Error removing directory tree {path}: {e}")
            raise
    
    @staticmethod
    async def exists(path: Union[str, Path]) -> bool:
        """
        Асинхронно проверяет существование файла или директории.
        
        Args:
            path: Путь к файлу или директории
            
        Returns:
            bool: True если файл/директория существует
        """
        try:
            await aiofiles.os.stat(str(path))
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking existence of {path}: {e}")
            raise
    
    @staticmethod
    async def get_size(path: Union[str, Path]) -> Optional[int]:
        """
        Асинхронно получает размер файла.
        
        Args:
            path: Путь к файлу
            
        Returns:
            Optional[int]: Размер файла в байтах или None если файл не существует
        """
        try:
            stat = await aiofiles.os.stat(str(path))
            return stat.st_size
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting size of {path}: {e}")
            raise
    
    @staticmethod
    async def list_dir(path: Union[str, Path]) -> List[str]:
        """
        Асинхронно получает список файлов в директории.
        
        Args:
            path: Путь к директории
            
        Returns:
            List[str]: Список имен файлов
        """
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: os.listdir(str(path)))
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            raise
    
    @staticmethod
    async def read_file(path: Union[str, Path], encoding: str = "utf-8") -> str:
        """
        Асинхронно читает текстовый файл.
        
        Args:
            path: Путь к файлу
            encoding: Кодировка файла
            
        Returns:
            str: Содержимое файла
        """
        try:
            async with aiofiles.open(str(path), "r", encoding=encoding) as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            raise
    
    @staticmethod
    async def write_file(path: Union[str, Path], content: str, encoding: str = "utf-8") -> None:
        """
        Асинхронно записывает текст в файл.
        
        Args:
            path: Путь к файлу
            content: Содержимое для записи
            encoding: Кодировка файла
        """
        try:
            async with aiofiles.open(str(path), "w", encoding=encoding) as f:
                await f.write(content)
            logger.debug(f"File written: {path}")
        except Exception as e:
            logger.error(f"Error writing file {path}: {e}")
            raise
    
    @staticmethod
    async def read_binary(path: Union[str, Path]) -> bytes:
        """
        Асинхронно читает бинарный файл.
        
        Args:
            path: Путь к файлу
            
        Returns:
            bytes: Содержимое файла
        """
        try:
            async with aiofiles.open(str(path), "rb") as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Error reading binary file {path}: {e}")
            raise
    
    @staticmethod
    async def write_binary(path: Union[str, Path], content: bytes) -> None:
        """
        Асинхронно записывает бинарные данные в файл.
        
        Args:
            path: Путь к файлу
            content: Бинарные данные для записи
        """
        try:
            async with aiofiles.open(str(path), "wb") as f:
                await f.write(content)
            logger.debug(f"Binary file written: {path}")
        except Exception as e:
            logger.error(f"Error writing binary file {path}: {e}")
            raise 