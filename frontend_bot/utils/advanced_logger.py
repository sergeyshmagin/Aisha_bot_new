"""
Расширенный модуль логирования с поддержкой ротации и JSON.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from logging.handlers import RotatingFileHandler
from frontend_bot.config import settings

class JSONFormatter(logging.Formatter):
    """Форматтер для структурированного логирования в JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Добавляем исключение, если есть
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        # Добавляем дополнительные поля
        if hasattr(record, "extra"):
            log_data.update(record.extra)
            
        return json.dumps(log_data, ensure_ascii=False)

async def setup_advanced_logging() -> None:
    """
    Настраивает расширенное логирование с поддержкой:
    - Ротации файлов
    - JSON форматирования
    """
    # Создаем директорию для логов
    log_dir = Path(settings.LOGS_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Очищаем существующие хендлеры
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
    
    # Добавляем хендлер для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    root_logger.addHandler(console_handler)
    
    # Добавляем хендлер для записи в файл с ротацией
    file_handler = RotatingFileHandler(
        log_dir / "bot.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Устанавливаем уровень логирования для сторонних библиотек
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

async def cleanup_logs() -> None:
    """Очищает все логи и закрывает хендлеры."""
    try:
        # Закрываем хендлеры
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)
            
        # Удаляем файлы логов
        log_dir = Path(settings.LOGS_DIR)
        for log_file in log_dir.glob("*.log*"):
            try:
                log_file.unlink()
            except Exception as e:
                logging.error(f"Error deleting log file {log_file}: {e}")
                
    except Exception as e:
        logging.error(f"Error cleaning up logs: {e}") 