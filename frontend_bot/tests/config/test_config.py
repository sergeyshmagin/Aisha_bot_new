"""
Тесты для конфигурации.
"""

import os
import pytest
from pathlib import Path
from pydantic import ValidationError

from frontend_bot.config import settings
from frontend_bot.config.base import BaseConfig
from frontend_bot.config.database import DatabaseConfig
from frontend_bot.config.storage import StorageConfig
from frontend_bot.config.external_services import ExternalServicesConfig, FalMode, FalPriority

def test_base_config():
    """Тест базовой конфигурации."""
    config = BaseConfig()
    
    # Проверка путей
    assert isinstance(config.BASE_DIR, Path)
    assert isinstance(config.STORAGE_DIR, Path)
    assert isinstance(config.LOGS_DIR, Path)
    assert isinstance(config.DATA_DIR, Path)
    assert isinstance(config.TEMP_DIR, Path)
    
    # Проверка логирования
    assert config.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    assert isinstance(config.LOG_FORMAT, str)
    assert isinstance(config.LOG_DATE_FORMAT, str)
    assert config.LOG_MAX_BYTES > 0
    assert config.LOG_BACKUP_COUNT > 0
    
    # Проверка безопасности
    assert isinstance(config.ALLOWED_USERS, list)
    assert isinstance(config.ADMIN_IDS, list)
    
    # Проверка мониторинга
    assert isinstance(config.ENABLE_METRICS, bool)
    assert 1 <= config.METRICS_PORT <= 65535
    
    # Проверка баланса
    assert config.INITIAL_BALANCE >= 0
    assert config.MIN_BALANCE >= 0
    assert config.COIN_PRICE > 0
    
    # Проверка стоимости сервисов
    assert config.AVATAR_CREATION_COST >= 0
    assert config.TRANSCRIPT_COST >= 0
    assert config.PHOTO_ENHANCE_COST >= 0
    
    # Проверка настроек бота
    assert config.MAX_MESSAGE_LENGTH > 0
    assert config.MAX_VOICE_DURATION > 0
    assert isinstance(config.SUPPORTED_LANGUAGES, list)
    assert config.DEFAULT_LANGUAGE in config.SUPPORTED_LANGUAGES
    
    # Проверка кэширования
    assert isinstance(config.CACHE_ENABLED, bool)
    assert config.CACHE_TTL > 0
    assert config.CACHE_MAX_SIZE > 0
    
    # Проверка очередей
    assert isinstance(config.QUEUE_PREFIX, str)
    assert config.MAX_RETRIES > 0
    assert config.RETRY_DELAY > 0

def test_database_config():
    """Тест конфигурации базы данных."""
    config = DatabaseConfig(
        POSTGRES_HOST="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_DB="test",
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        REDIS_HOST="localhost",
        REDIS_PORT=6379,
        REDIS_DB=0
    )
    
    # Проверка PostgreSQL
    assert isinstance(config.POSTGRES_HOST, str)
    assert 1 <= config.POSTGRES_PORT <= 65535
    assert isinstance(config.POSTGRES_DB, str)
    assert isinstance(config.POSTGRES_USER, str)
    assert isinstance(config.POSTGRES_PASSWORD, str)
    assert config.DATABASE_URL is not None
    
    # Проверка Redis
    assert isinstance(config.REDIS_HOST, str)
    assert 1 <= config.REDIS_PORT <= 65535
    assert config.REDIS_DB >= 0
    assert isinstance(config.REDIS_POOL_SIZE, int)
    assert config.REDIS_POOL_SIZE > 0
    assert isinstance(config.REDIS_POOL_TIMEOUT, int)
    assert config.REDIS_POOL_TIMEOUT > 0
    assert isinstance(config.REDIS_RETRY_ON_TIMEOUT, bool)
    assert isinstance(config.REDIS_MAX_RETRIES, int)
    assert config.REDIS_MAX_RETRIES > 0
    assert isinstance(config.REDIS_RETRY_INTERVAL, int)
    assert config.REDIS_RETRY_INTERVAL > 0
    assert config.REDIS_URL is not None

def test_storage_config():
    """Тест конфигурации хранилища."""
    config = StorageConfig(
        MINIO_ENDPOINT="localhost:9000",
        MINIO_ACCESS_KEY="test",
        MINIO_SECRET_KEY="test"
    )
    
    # Проверка MinIO
    assert isinstance(config.MINIO_ENDPOINT, str)
    assert isinstance(config.MINIO_ACCESS_KEY, str)
    assert isinstance(config.MINIO_SECRET_KEY, str)
    assert isinstance(config.MINIO_SECURE, bool)
    
    # Проверка путей
    assert isinstance(config.AVATAR_STORAGE_PATH, Path)
    assert isinstance(config.GALLERY_PATH, Path)
    assert isinstance(config.TRANSCRIPTS_PATH, Path)
    assert isinstance(config.THUMBNAIL_PATH, Path)
    assert isinstance(config.AVATAR_DIR, str)
    
    # Проверка лимитов файлов
    assert config.MAX_FILE_SIZE > 0
    assert config.MAX_AUDIO_DURATION > 0
    assert config.MAX_VIDEO_DURATION > 0
    assert config.MAX_PHOTO_SIZE > 0
    
    # Проверка форматов
    assert isinstance(config.ALLOWED_AUDIO_FORMATS, list)
    assert isinstance(config.ALLOWED_VIDEO_FORMATS, list)
    assert isinstance(config.ALLOWED_PHOTO_FORMATS, list)
    assert all(isinstance(f, str) for f in config.ALLOWED_AUDIO_FORMATS)
    assert all(isinstance(f, str) for f in config.ALLOWED_VIDEO_FORMATS)
    assert all(isinstance(f, str) for f in config.ALLOWED_PHOTO_FORMATS)
    
    # Проверка лимитов аватаров
    assert config.AVATAR_MIN_PHOTOS > 0
    assert config.AVATAR_MAX_PHOTOS >= config.AVATAR_MIN_PHOTOS
    assert config.AVATARS_PER_PAGE > 0
    assert config.PHOTO_MAX_MB > 0
    assert config.PHOTO_MIN_RES > 0
    assert config.THUMBNAIL_SIZE > 0
    
    # Проверка эмодзи
    assert isinstance(config.PROGRESSBAR_EMOJI_FILLED, str)
    assert isinstance(config.PROGRESSBAR_EMOJI_CURRENT, str)
    assert isinstance(config.PROGRESSBAR_EMOJI_EMPTY, str)
    
    # Проверка статусов
    assert isinstance(config.AVATAR_STATUS_TRAINING, str)
    assert isinstance(config.AVATAR_STATUS_READY, str)
    assert isinstance(config.AVATAR_STATUS_ERROR, str)
    
    # Проверка гендеров
    assert isinstance(config.AVATAR_GENDER_MALE, str)
    assert isinstance(config.AVATAR_GENDER_FEMALE, str)
    assert isinstance(config.AVATAR_GENDER_OTHER, str)
    
    # Проверка конфигурации MinIO
    minio_config = config.minio_config
    assert isinstance(minio_config, dict)
    assert "endpoint" in minio_config
    assert "access_key" in minio_config
    assert "secret_key" in minio_config
    assert "secure" in minio_config

def test_external_services_config():
    """Тест конфигурации внешних сервисов."""
    config = ExternalServicesConfig(
        TELEGRAM_TOKEN="test",
        OPENAI_API_KEY="test",
        ASSISTANT_ID="test",
        FAL_KEY="test",
        BACKEND_URL="http://localhost:8000"
    )
    
    # Проверка Telegram
    assert isinstance(config.TELEGRAM_TOKEN, str)
    assert config.TELEGRAM_TOKEN
    
    # Проверка OpenAI
    assert isinstance(config.OPENAI_API_KEY, str)
    assert config.OPENAI_API_KEY
    assert isinstance(config.ASSISTANT_ID, str)
    assert config.ASSISTANT_ID
    
    # Проверка FAL.AI
    assert isinstance(config.FAL_KEY, str)
    assert config.FAL_KEY
    assert isinstance(config.FAL_MODE, FalMode)
    assert 1 <= config.FAL_ITERATIONS <= 1000
    assert isinstance(config.FAL_PRIORITY, FalPriority)
    assert isinstance(config.FAL_CAPTIONING, bool)
    assert isinstance(config.FAL_TRIGGER_WORD, str)
    assert config.FAL_TRIGGER_WORD
    assert 1 <= config.FAL_LORA_RANK <= 128
    assert isinstance(config.FAL_FINETUNE_TYPE, str)
    assert isinstance(config.FAL_TRAINING_TEST_MODE, bool)
    
    # Проверка Astria
    assert config.ASTRIA_API_KEY is None or isinstance(config.ASTRIA_API_KEY, str)
    
    # Проверка Backend
    assert isinstance(config.BACKEND_URL, str)
    assert config.BACKEND_URL.startswith("http")

def test_validation_errors():
    """Тест валидации ошибок."""
    # Тест неверного порта PostgreSQL
    with pytest.raises(ValidationError):
        DatabaseConfig(
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=70000,  # Неверный порт
            POSTGRES_DB="test",
            POSTGRES_USER="test",
            POSTGRES_PASSWORD="test",
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_DB=0
        )
    
    # Тест неверного режима FAL.AI
    with pytest.raises(ValidationError):
        ExternalServicesConfig(
            TELEGRAM_TOKEN="test",
            OPENAI_API_KEY="test",
            ASSISTANT_ID="test",
            FAL_KEY="test",
            FAL_MODE="invalid_mode",  # Неверный режим
            BACKEND_URL="http://localhost:8000"
        )
    
    # Тест неверного количества фото для аватара
    with pytest.raises(ValidationError):
        StorageConfig(
            MINIO_ENDPOINT="localhost:9000",
            MINIO_ACCESS_KEY="test",
            MINIO_SECRET_KEY="test",
            AVATAR_MIN_PHOTOS=20,
            AVATAR_MAX_PHOTOS=10  # Меньше минимального
        )

def test_env_variables():
    """Тест загрузки переменных окружения."""
    # Устанавливаем тестовые переменные окружения
    os.environ["TELEGRAM_TOKEN"] = "test_token"
    os.environ["OPENAI_API_KEY"] = "test_key"
    os.environ["ASSISTANT_ID"] = "test_assistant"
    os.environ["FAL_KEY"] = "test_fal"
    os.environ["BACKEND_URL"] = "http://localhost:8000"
    
    # Создаем конфигурацию
    config = ExternalServicesConfig()
    
    # Проверяем значения
    assert config.TELEGRAM_TOKEN == "test_token"
    assert config.OPENAI_API_KEY == "test_key"
    assert config.ASSISTANT_ID == "test_assistant"
    assert config.FAL_KEY == "test_fal"
    assert config.BACKEND_URL == "http://localhost:8000"
    
    # Очищаем переменные окружения
    os.environ.pop("TELEGRAM_TOKEN", None)
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("ASSISTANT_ID", None)
    os.environ.pop("FAL_KEY", None)
    os.environ.pop("BACKEND_URL", None) 