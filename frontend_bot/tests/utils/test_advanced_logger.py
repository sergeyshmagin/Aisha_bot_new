"""
Тесты для расширенного модуля логирования.
"""

import json
import logging
import os
import pytest
from datetime import datetime
from pathlib import Path
import asyncio

from frontend_bot.utils.advanced_logger import (
    JSONFormatter,
    RedisHandler,
    setup_advanced_logging,
    get_critical_logs,
    clear_old_logs,
    cleanup_logs
)
from frontend_bot.config import settings

@pytest.fixture
async def setup_logging():
    """Фикстура для настройки логирования."""
    # Очищаем предыдущие логи
    await cleanup_logs()
    
    # Настраиваем логирование
    await setup_advanced_logging()
    
    yield
    
    # Очищаем после тестов
    await cleanup_logs()

@pytest.mark.asyncio
async def test_json_formatter():
    """Тест форматтера JSON."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    log_data = json.loads(formatted)
    
    assert log_data["level"] == "INFO"
    assert log_data["logger"] == "test"
    assert log_data["message"] == "Test message"
    assert "timestamp" in log_data
    assert "module" in log_data
    assert "function" in log_data
    assert "line" in log_data

@pytest.mark.asyncio
async def test_redis_handler(setup_logging):
    """Тест хендлера для Redis."""
    handler = RedisHandler()
    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="Test error",
        args=(),
        exc_info=None
    )
    
    # Эмулируем отправку лога
    handler.emit(record)
    
    # Даем время на асинхронную запись
    await asyncio.sleep(0.1)
    
    # Проверяем, что лог появился в Redis
    logs = await get_critical_logs(limit=1)
    assert len(logs) > 0
    assert logs[0]["level"] == "ERROR"
    assert logs[0]["message"] == "Test error"

@pytest.mark.asyncio
async def test_setup_advanced_logging(setup_logging):
    """Тест настройки расширенного логирования."""
    # Проверяем создание директории
    assert Path(settings.LOG_DIR).exists()
    
    # Проверяем создание файла лога
    log_file = Path(settings.LOG_DIR) / "bot.log"
    assert log_file.exists()
    
    # Проверяем хендлеры
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) == 3  # Console, File, Redis
    
    # Проверяем форматирование
    console_handler = next(h for h in root_logger.handlers if isinstance(h, logging.StreamHandler))
    assert isinstance(console_handler.formatter, logging.Formatter)
    
    file_handler = next(h for h in root_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler))
    assert isinstance(file_handler.formatter, JSONFormatter)
    
    redis_handler = next(h for h in root_logger.handlers if isinstance(h, RedisHandler))
    assert isinstance(redis_handler.formatter, JSONFormatter)

@pytest.mark.asyncio
async def test_get_critical_logs(setup_logging):
    """Тест получения критических логов."""
    # Добавляем тестовые логи
    logger = logging.getLogger("test")
    logger.error("Test error 1")
    logger.error("Test error 2")
    
    # Даем время на асинхронную запись
    await asyncio.sleep(0.1)
    
    # Получаем логи
    logs = await get_critical_logs(limit=2)
    assert len(logs) == 2
    assert logs[0]["level"] == "ERROR"
    assert logs[0]["message"] == "Test error 2"
    assert logs[1]["message"] == "Test error 1"

@pytest.mark.asyncio
async def test_clear_old_logs(setup_logging):
    """Тест очистки старых логов."""
    # Добавляем тестовые логи
    logger = logging.getLogger("test")
    logger.error("Test error")
    
    # Даем время на асинхронную запись
    await asyncio.sleep(0.1)
    
    # Проверяем наличие логов
    logs = await get_critical_logs()
    assert len(logs) > 0
    
    # Очищаем логи
    await clear_old_logs()
    
    # Проверяем, что логи удалены
    logs = await get_critical_logs()
    assert len(logs) == 0

@pytest.mark.asyncio
async def test_log_rotation(setup_logging):
    """Тест ротации логов."""
    logger = logging.getLogger("test")
    log_file = Path(settings.LOG_DIR) / "bot.log"
    
    # Заполняем файл лога
    for i in range(1000):
        logger.info("x" * 1000)  # Большие сообщения
    
    # Даем время на запись
    await asyncio.sleep(0.1)
    
    # Проверяем создание файлов ротации
    log_files = list(Path(settings.LOG_DIR).glob("*.log*"))
    assert len(log_files) > 1  # Должен быть основной файл и файлы ротации 