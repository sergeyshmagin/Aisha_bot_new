"""
Тесты для модуля логирования.
"""

import pytest
import logging
import sys
from pathlib import Path
from frontend_bot.utils.logger import setup_logging
from frontend_bot.shared.file_operations import AsyncFileManager
from frontend_bot.config import LOG_DIR

@pytest.fixture
async def temp_dir(tmp_path):
    """Создает временную директорию для тестов."""
    test_dir = tmp_path / "test_dir"
    await AsyncFileManager.ensure_dir(test_dir)
    yield test_dir
    await AsyncFileManager.safe_rmtree(test_dir)

@pytest.mark.asyncio
async def test_setup_logging(temp_dir):
    """Тест настройки логирования."""
    # Сохраняем оригинальные хендлеры
    original_handlers = logging.getLogger().handlers.copy()
    
    try:
        # Настраиваем логирование
        await setup_logging()
        
        # Проверяем, что директория для логов создана
        assert await AsyncFileManager.exists(Path(LOG_DIR))
        
        # Проверяем корневой логгер
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        
        # Проверяем хендлеры
        handlers = root_logger.handlers
        assert len(handlers) == 2  # Console и File handler
        
        # Проверяем форматтеры
        for handler in handlers:
            formatter = handler.formatter
            assert formatter is not None
            assert "%(asctime)s" in formatter._fmt
            assert "%(name)s" in formatter._fmt
            assert "%(levelname)s" in formatter._fmt
            assert "%(message)s" in formatter._fmt
        
        # Проверяем уровни логирования для сторонних библиотек
        assert logging.getLogger("telegram").level == logging.WARNING
        assert logging.getLogger("aiohttp").level == logging.WARNING
        assert logging.getLogger("asyncio").level == logging.WARNING
        
    finally:
        # Восстанавливаем оригинальные хендлеры
        root_logger.handlers = original_handlers

@pytest.mark.asyncio
async def test_log_file_creation(temp_dir):
    """Тест создания файла логов."""
    # Настраиваем логирование
    await setup_logging()
    
    # Проверяем, что файл логов создан
    log_file = Path(LOG_DIR) / "bot.log"
    assert await AsyncFileManager.exists(log_file)
    
    # Записываем тестовое сообщение
    logger = logging.getLogger("test")
    test_message = "Test log message"
    logger.info(test_message)
    
    # Проверяем, что сообщение записано в файл
    content = await AsyncFileManager.read_file(log_file)
    assert test_message in content

@pytest.mark.asyncio
async def test_log_levels(temp_dir):
    """Тест уровней логирования."""
    # Настраиваем логирование
    await setup_logging()
    
    logger = logging.getLogger("test")
    log_file = Path(LOG_DIR) / "bot.log"
    
    # Записываем сообщения разных уровней
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Проверяем содержимое файла
    content = await AsyncFileManager.read_file(log_file)
    
    # Debug не должен быть записан (уровень INFO)
    assert "Debug message" not in content
    assert "Info message" in content
    assert "Warning message" in content
    assert "Error message" in content

@pytest.mark.asyncio
async def test_log_format(temp_dir):
    """Тест формата логов."""
    # Настраиваем логирование
    await setup_logging()
    
    logger = logging.getLogger("test")
    log_file = Path(LOG_DIR) / "bot.log"
    
    # Записываем тестовое сообщение
    test_message = "Test format message"
    logger.info(test_message)
    
    # Проверяем формат
    content = await AsyncFileManager.read_file(log_file)
    log_line = content.strip()
    
    # Проверяем компоненты формата
    assert "test" in log_line  # Имя логгера
    assert "INFO" in log_line  # Уровень
    assert test_message in log_line  # Сообщение
    assert " - " in log_line  # Разделители

@pytest.mark.asyncio
async def test_multiple_loggers(temp_dir):
    """Тест работы нескольких логгеров."""
    # Настраиваем логирование
    await setup_logging()
    
    # Создаем несколько логгеров
    loggers = {
        "test1": logging.getLogger("test1"),
        "test2": logging.getLogger("test2"),
        "test3": logging.getLogger("test3")
    }
    
    log_file = Path(LOG_DIR) / "bot.log"
    
    # Записываем сообщения от разных логгеров
    for name, logger in loggers.items():
        logger.info(f"Message from {name}")
    
    # Проверяем содержимое файла
    content = await AsyncFileManager.read_file(log_file)
    
    # Проверяем, что все сообщения записаны
    for name in loggers:
        assert f"Message from {name}" in content
        assert name in content  # Имя логгера в строке

@pytest.mark.asyncio
async def test_external_libraries_logging(temp_dir):
    """Тест логирования для внешних библиотек."""
    # Настраиваем логирование
    await setup_logging()
    
    log_file = Path(LOG_DIR) / "bot.log"
    
    # Записываем сообщения от внешних библиотек
    logging.getLogger("telegram").info("Telegram info")
    logging.getLogger("telegram").warning("Telegram warning")
    
    logging.getLogger("aiohttp").info("Aiohttp info")
    logging.getLogger("aiohttp").warning("Aiohttp warning")
    
    # Проверяем содержимое файла
    content = await AsyncFileManager.read_file(log_file)
    
    # Info не должен быть записан (уровень WARNING)
    assert "Telegram info" not in content
    assert "Aiohttp info" not in content
    
    # Warning должен быть записан
    assert "Telegram warning" in content
    assert "Aiohttp warning" in content 