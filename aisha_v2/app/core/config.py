"""
Конфигурация приложения
"""
import os
from pathlib import Path
from typing import Optional, Union, List, Dict

from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    """Настройки приложения"""
    
    # Основные настройки
    DEBUG: bool = True
    ENV: str = "development"
    
    # Telegram
    TELEGRAM_TOKEN: str = Field(default="test_token")
    BACKEND_URL: str = "http://localhost:8000"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default="test_key")
    ASSISTANT_ID: Optional[str] = None
    
    # Fal AI
    FAL_KEY: Optional[str] = Field(default="test_key")
    FAL_TRAINING_TEST_MODE: bool = Field(default=True)
    
    # Пути
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    AUDIO_STORAGE_PATH: Path = BASE_DIR / "storage" / "audio"
    FFMPEG_PATH: str = "C:\\dev\\distr\\ffmpeg\\bin\\ffmpeg.exe"
    
    # Настройки аудио
    MAX_AUDIO_SIZE: int = 25 * 1024 * 1024  # 25 МБ
    MAX_AUDIO_DURATION: int = 300  # 5 минут
    AUDIO_FORMATS: List[str] = ["mp3", "wav", "ogg", "m4a"]
    
    # Настройки транскрибации
    DEFAULT_LANGUAGE: str = "ru"
    SUPPORTED_LANGUAGES: List[str] = ["ru", "en"]
    WHISPER_MODEL: str = "whisper-1"
    WHISPER_LANGUAGE: str = "ru"
    
    # Настройки хранения
    STORAGE_CLEANUP_DAYS: int = 7
    
    # Настройки логирования
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # Настройки метрик
    ENABLE_METRICS: bool = False
    METRICS_HOST: str = "localhost"
    METRICS_PORT: int = 9090
    
    # Настройки трейсинга
    ENABLE_TRACING: bool = False
    TRACING_HOST: str = "localhost"
    
    # Настройки Redis
    REDIS_HOST: str = Field(default="192.168.0.3")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str = Field(default="wd7QuwAbG0wtyoOOw3Sm")
    REDIS_SSL: bool = Field(default=False)
    REDIS_POOL_SIZE: int = Field(default=10)
    REDIS_POOL_TIMEOUT: int = Field(default=5)
    REDIS_MAX_RETRIES: int = Field(default=3)
    
    # PostgreSQL
    POSTGRES_HOST: Optional[str] = Field(default="localhost")
    POSTGRES_PORT: Optional[int] = Field(default=5432)
    POSTGRES_DB: Optional[str] = Field(default="aisha")
    POSTGRES_USER: Optional[str] = Field(default="postgres")
    POSTGRES_PASSWORD: Optional[str] = Field(default="postgres")
    DATABASE_URL: Optional[str] = None
    
    # MinIO
    MINIO_ENDPOINT: Optional[str] = Field(default="localhost:9000")
    MINIO_ACCESS_KEY: Optional[str] = Field(default="minioadmin")
    MINIO_SECRET_KEY: Optional[str] = Field(default="minioadmin")
    MINIO_BUCKET_NAME: Optional[str] = Field(default="aisha")
    MINIO_SECURE: bool = Field(default=False)
    MINIO_BUCKET_AVATARS: Optional[str] = Field(default="avatars")
    MINIO_BUCKET_PHOTOS: Optional[str] = Field(default="photos")
    MINIO_BUCKET_TEMP: Optional[str] = Field(default="temp")
    MINIO_PRESIGNED_EXPIRES: int = Field(default=3600)  # Время истечения presigned URL в секундах
    TEMP_DIR: Path = Path("temp")
    
    # Настройки алертов
    ENABLE_ALERTS: bool = False
    ALERT_EMAIL: Optional[str] = None
    ALERT_SLACK_WEBHOOK: Optional[str] = None
    
    # Backend
    BACKEND_URL: Optional[str] = None
    
    # Python
    PYTHONPATH: Optional[str] = None
    
    # Redis
    REDIS_RETRY_ON_TIMEOUT: Union[bool, str] = True
    REDIS_RETRY_INTERVAL: Union[int, str] = 1
    
    # PostgreSQL
    POSTGRES_PASSWORD: Optional[str] = Field(default="postgres")
    
    # MinIO
    TRACING_PORT: int = 6831
    
    # MinIO buckets
    MINIO_BUCKETS: Dict[str, str] = {
        "avatars": "avatars",
        "transcripts": "transcripts",
        "documents": "documents",
        "temp": "temp",
        "test": "test-bucket"
    }
    
    class Config:
        """Конфигурация Pydantic"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Разрешаем дополнительные поля в переменных окружения

# Создаем экземпляр настроек
settings = Settings()

# Создаем директории, если они не существуют
settings.AUDIO_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
