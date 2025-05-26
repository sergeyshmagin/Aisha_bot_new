"""
Система логирования для API сервера
"""
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from .config import settings

def setup_logging():
    """Настройка логирования для API сервера"""
    
    # Создаем директорию для логов
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    
    # Основной логгер API сервера
    api_logger = logging.getLogger("api_server")
    api_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Логгер для webhook
    webhook_logger = logging.getLogger("webhook")
    webhook_logger.setLevel(logging.INFO)
    
    # Общий форматтер
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Консольный хендлер
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    api_logger.addHandler(console_handler)
    
    # Файловый хендлер для API сервера
    api_file_handler = RotatingFileHandler(
        log_dir / "api_server.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    api_file_handler.setFormatter(formatter)
    api_logger.addHandler(api_file_handler)
    
    # Файловый хендлер для webhook
    webhook_file_handler = RotatingFileHandler(
        log_dir / settings.WEBHOOK_LOG_FILE,
        maxBytes=5*1024*1024,   # 5MB
        backupCount=3,
        encoding="utf-8"
    )
    webhook_file_handler.setFormatter(formatter)
    webhook_logger.addHandler(webhook_file_handler)
    
    return api_logger, webhook_logger

def get_api_logger():
    """Получить логгер API сервера"""
    return logging.getLogger("api_server")

def get_webhook_logger():
    """Получить логгер webhook"""
    return logging.getLogger("webhook") 