"""
Модуль для настройки логирования.
"""

import logging
import sys
from pathlib import Path
from frontend_bot.shared.file_operations import AsyncFileManager
from frontend_bot.config import LOG_DIR

def get_logger(name: str) -> logging.Logger:
    """
    Получает логгер с указанным именем.
    
    Args:
        name: Имя логгера
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    return logging.getLogger(name)

async def setup_logging():
    """
    Настраивает логирование для приложения.
    Создает директорию для логов, если она не существует.
    """
    # Создаем директорию для логов
    await AsyncFileManager.ensure_dir(Path(LOG_DIR))
    
    # Настраиваем формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Очищаем существующие хендлеры
    root_logger.handlers.clear()
    
    # Добавляем хендлер для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(console_handler)
    
    # Добавляем хендлер для записи в файл
    file_handler = logging.FileHandler(
        Path(LOG_DIR) / "bot.log",
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    root_logger.addHandler(file_handler)
    
    # Устанавливаем уровень логирования для сторонних библиотек
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
