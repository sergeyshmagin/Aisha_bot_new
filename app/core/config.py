"""
Конфигурация приложения
"""
import os
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

from pydantic_settings import BaseSettings
from pydantic import Field, validator

class Settings(BaseSettings):
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
    
    # ========== НАСТРОЙКИ АВАТАРОВ ==========
    
    # Лимиты фотографий
    AVATAR_MIN_PHOTOS: int = Field(10, env="AVATAR_MIN_PHOTOS")
    AVATAR_MAX_PHOTOS: int = Field(20, env="AVATAR_MAX_PHOTOS") 
    AVATAR_MAX_PHOTOS_PER_USER: int = Field(5, env="AVATAR_MAX_PHOTOS_PER_USER")
    
    # Ограничения файлов
    PHOTO_MAX_SIZE: int = Field(20 * 1024 * 1024, env="PHOTO_MAX_SIZE")  # 20MB
    PHOTO_MIN_RESOLUTION: int = Field(512, env="PHOTO_MIN_RESOLUTION")
    PHOTO_MAX_RESOLUTION: int = Field(4096, env="PHOTO_MAX_RESOLUTION")
    PHOTO_ALLOWED_FORMATS: List[str] = Field(["jpg", "jpeg", "png", "webp"], env="PHOTO_ALLOWED_FORMATS")
    
    # FAL AI интеграция
    FAL_API_KEY: str = Field("", env="FAL_KEY")
    FAL_TRAINING_TEST_MODE: bool = Field(True, env="FAL_TRAINING_TEST_MODE")  # 🎯 КЛЮЧЕВОЙ ПАРАМЕТР!
    FAL_WEBHOOK_URL: str = Field("https://aibots.kz/api/avatar/status_update", env="FAL_WEBHOOK_URL")
    FAL_DEFAULT_MODE: str = Field("character", env="FAL_MODE")
    FAL_DEFAULT_ITERATIONS: int = Field(500, env="FAL_ITERATIONS")
    FAL_DEFAULT_PRIORITY: str = Field("quality", env="FAL_PRIORITY")
    FAL_TRIGGER_WORD: str = Field("TOK", env="FAL_TRIGGER_WORD")
    FAL_LORA_RANK: int = Field(32, env="FAL_LORA_RANK")
    FAL_FINETUNE_TYPE: str = Field("full", env="FAL_FINETUNE_TYPE")
    
    # UX настройки
    PHOTO_UPLOAD_TIMEOUT: int = Field(300, env="PHOTO_UPLOAD_TIMEOUT")  # 5 минут
    GALLERY_PHOTOS_PER_PAGE: int = Field(6, env="GALLERY_PHOTOS_PER_PAGE")
    TRAINING_STATUS_UPDATE_INTERVAL: int = Field(30, env="TRAINING_STATUS_UPDATE_INTERVAL")  # секунд
    AUTO_GENERATE_PREVIEW: bool = Field(True, env="AUTO_GENERATE_PREVIEW")
    AVATAR_CREATION_COOLDOWN: int = Field(86400, env="AVATAR_CREATION_COOLDOWN")  # 24 часа
    
    # Валидация и безопасность
    ENABLE_FACE_DETECTION: bool = Field(True, env="ENABLE_FACE_DETECTION")
    ENABLE_NSFW_DETECTION: bool = Field(True, env="ENABLE_NSFW_DETECTION")
    MIN_FACE_SIZE: int = Field(100, env="MIN_FACE_SIZE")  # минимальный размер лица в пикселях
    QUALITY_THRESHOLD: float = Field(0.5, env="QUALITY_THRESHOLD")  # минимальная оценка качества
    
    # Стоимость сервисов (в кредитах)
    AVATAR_CREATION_COST: float = Field(10.0, env="AVATAR_CREATION_COST")
    AVATAR_GENERATION_COST: float = Field(1.0, env="AVATAR_GENERATION_COST")
    
    # ========== КОНЕЦ НАСТРОЕК АВАТАРОВ ==========
    
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
    POSTGRES_HOST: Optional[str] = Field(default="192.168.0.4")
    POSTGRES_PORT: Optional[int] = Field(default=5432)
    POSTGRES_DB: Optional[str] = Field(default="aisha")
    POSTGRES_USER: Optional[str] = Field(default="aisha_user")
    POSTGRES_PASSWORD: Optional[str] = Field(default="KbZZGJHX09KSH7r9ev4m")
    DATABASE_URL: Optional[str] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """Автоматически собираем DATABASE_URL из переменных PostgreSQL"""
        if isinstance(v, str) and v:
            return v
        return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_HOST')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
    
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
    POSTGRES_PASSWORD: Optional[str] = Field(default="KbZZGJHX09KSH7r9ev4m")
    
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
