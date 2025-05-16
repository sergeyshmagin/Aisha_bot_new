"""
Расширенный модуль логирования с поддержкой ротации, JSON и Redis.
"""

import json
import logging
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from logging.handlers import RotatingFileHandler
from frontend_bot.shared.redis_client import redis_client
from frontend_bot.config import LOG_DIR, LOG_LEVEL, REDIS_LOG_TTL

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

class RedisHandler(logging.Handler):
    """Хендлер для отправки критических логов в Redis."""
    
    def __init__(self, level: int = logging.ERROR):
        """Инициализация хендлера."""
        super().__init__(level)
        self._prefix = "log:"
        self._ttl = REDIS_LOG_TTL
        self._loop = asyncio.get_event_loop()
        
    def emit(self, record: logging.LogRecord) -> None:
        """Отправляет запись лога в Redis."""
        try:
            log_data = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
                
            if hasattr(record, "extra"):
                log_data.update(record.extra)
                
            # Сохраняем в Redis с TTL асинхронно
            key = f"{self._prefix}{datetime.now().timestamp()}"
            asyncio.run_coroutine_threadsafe(
                redis_client.set_json(key, log_data, expire=self._ttl),
                self._loop
            )
            
        except Exception as e:
            self.handleError(record)

async def setup_advanced_logging() -> None:
    """
    Настраивает расширенное логирование с поддержкой:
    - Ротации файлов
    - JSON форматирования
    - Redis для критических логов
    """
    # Создаем директорию для логов
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
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
    
    # Добавляем хендлер для критических логов в Redis
    redis_handler = RedisHandler(level=logging.ERROR)
    redis_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(redis_handler)
    
    # Устанавливаем уровень логирования для сторонних библиотек
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

async def get_critical_logs(limit: int = 100) -> list[Dict[str, Any]]:
    """
    Получает критические логи из Redis.
    
    Args:
        limit: Максимальное количество логов
        
    Returns:
        list[Dict[str, Any]]: Список логов
    """
    try:
        keys = await redis_client._client.keys("log:*")
        keys.sort(reverse=True)  # Сначала новые
        keys = keys[:limit]
        
        logs = []
        for key in keys:
            log_data = await redis_client.get_json(key)
            if log_data:
                logs.append(log_data)
                
        return logs
    except Exception as e:
        logging.error(f"Error getting critical logs: {e}")
        return []

async def clear_old_logs() -> None:
    """Очищает старые логи из Redis."""
    try:
        await redis_client.delete_pattern("log:*")
    except Exception as e:
        logging.error(f"Error clearing old logs: {e}")

async def cleanup_logs() -> None:
    """Очищает все логи и закрывает хендлеры."""
    try:
        # Очищаем логи в Redis
        await clear_old_logs()
        
        # Закрываем хендлеры
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)
            
        # Удаляем файлы логов
        log_dir = Path(LOG_DIR)
        for log_file in log_dir.glob("*.log*"):
            try:
                log_file.unlink()
            except Exception as e:
                logging.error(f"Error deleting log file {log_file}: {e}")
                
    except Exception as e:
        logging.error(f"Error cleaning up logs: {e}") 