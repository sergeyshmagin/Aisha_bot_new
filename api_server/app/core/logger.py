"""
Логгер для API сервера webhook
"""
import logging
import sys
from pathlib import Path

def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """Настройка логгера"""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Избегаем дублирования хендлеров
    if logger.handlers:
        return logger
    
    # Форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Консольный хендлер
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый хендлер (если указан файл)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_webhook_logger() -> logging.Logger:
    """Получить логгер для webhook"""
    return setup_logger("webhook", "logs/webhook.log")

def get_api_logger() -> logging.Logger:
    """Получить логгер для API"""
    return setup_logger("api", "logs/api.log") 