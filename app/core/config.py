"""
Конфигурация приложения с поддержкой environs
"""
import os
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from environs import Env

# Инициализация environs для дополнительной функциональности
env = Env()
env.read_env()  # Автоматически читает .env файл

class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Основные настройки
    DEBUG: bool = True
    ENV: str = "development"
    INSTANCE_ID: str = Field(default="aisha-bot", env="INSTANCE_ID")
    
    # Telegram
    TELEGRAM_TOKEN: str = Field(default="test_token", env="TELEGRAM_BOT_TOKEN")
    # BACKEND_URL: str = "http://localhost:8000"  # LEGACY - удален
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default="test_key")
    ASSISTANT_ID: Optional[str] = None
    
    # Fal AI
    FAL_API_KEY: str = Field("", env="FAL_API_KEY")
    FAL_KEY: str = Field("", env="FAL_KEY")  # Альтернативное имя для совместимости
    FAL_WEBHOOK_URL: str = Field("https://aibots.kz:8443/api/v1/avatar/status_update", env="FAL_WEBHOOK_URL")
    
    @property
    def effective_fal_api_key(self) -> str:
        """Возвращает FAL API ключ из любого доступного источника"""
        return self.FAL_API_KEY or self.FAL_KEY or ""
    
    # FAL AI - Portrait Trainer Settings (ЕДИНСТВЕННЫЕ ИСПОЛЬЗУЕМЫЕ НАСТРОЙКИ)
    FAL_PORTRAIT_STEPS: int = Field(1000, env="FAL_PORTRAIT_STEPS")
    FAL_PORTRAIT_LEARNING_RATE: float = Field(0.0002, env="FAL_PORTRAIT_LEARNING_RATE")
    FAL_PORTRAIT_SUBJECT_CROP: bool = Field(True, env="FAL_PORTRAIT_SUBJECT_CROP")
    FAL_PORTRAIT_CREATE_MASKS: bool = Field(True, env="FAL_PORTRAIT_CREATE_MASKS")
    FAL_PORTRAIT_MULTIRESOLUTION: bool = Field(True, env="FAL_PORTRAIT_MULTIRESOLUTION")
    
    # FAL AI - Advanced Settings
    FAL_TRAINING_TIMEOUT: int = Field(1800, env="FAL_TRAINING_TIMEOUT")  # 30 минут
    FAL_STATUS_CHECK_INTERVAL: int = Field(30, env="FAL_STATUS_CHECK_INTERVAL")  # секунд
    FAL_MAX_RETRIES: int = Field(3, env="FAL_MAX_RETRIES")
    FAL_AUTO_MODEL_SELECTION: bool = Field(True, env="FAL_AUTO_MODEL_SELECTION")  # Автовыбор модели
    FAL_DEFAULT_QUALITY_PRESET: str = Field("fast", env="FAL_DEFAULT_QUALITY_PRESET")  # Качество по умолчанию
    
    # FAL AI - Пресеты качества (основываясь на документации flux-lora-portrait-trainer)
    FAL_PRESET_FAST: dict = Field(default={
        "portrait": {
            "steps": 1000,
            "learning_rate": 0.0002,
            "multiresolution_training": True,
            "subject_crop": True,
            "create_masks": False
        },
        "general": {
            "iterations": 800,
            "learning_rate": 0.0002,
            "priority": "speed"
        }
    }, env="FAL_PRESET_FAST")
    
    FAL_PRESET_BALANCED: dict = Field(default={
        "portrait": {
            "steps": 2500,
            "learning_rate": 0.00009,
            "multiresolution_training": True,
            "subject_crop": True,
            "create_masks": True
        },
        "general": {
            "iterations": 1500,
            "learning_rate": 0.00009,
            "priority": "balanced"
        }
    }, env="FAL_PRESET_BALANCED")
    
    FAL_PRESET_QUALITY: dict = Field(default={
        "portrait": {
            "steps": 4000,
            "learning_rate": 0.00005,
            "multiresolution_training": True,
            "subject_crop": True,
            "create_masks": True
        },
        "general": {
            "iterations": 3000,
            "learning_rate": 0.00005,
            "priority": "quality"
        }
    }, env="FAL_PRESET_QUALITY")
    
    # 🧪 FAL AI - Debug & Development Settings
    FAL_MOCK_TRAINING_DURATION: int = Field(30, env="FAL_MOCK_TRAINING_DURATION")  # секунд
    FAL_ENABLE_WEBHOOK_SIMULATION: bool = Field(True, env="FAL_ENABLE_WEBHOOK_SIMULATION") 
    FAL_TEST_REQUEST_PREFIX: str = Field("test_", env="FAL_TEST_REQUEST_PREFIX")
    
    # Пути
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    AUDIO_STORAGE_PATH: Path = BASE_DIR / "storage" / "audio"
    FFMPEG_PATH: str = "C:\\dev\\distr\\ffmpeg\\bin\\ffmpeg.exe"
    
    # Настройки аудио
    MAX_AUDIO_SIZE: int = 1024 * 1024 * 1024  # 1GB
    TELEGRAM_API_LIMIT: int = 20 * 1024 * 1024  # 20MB - лимит Telegram Bot API
    AUDIO_FORMATS: List[str] = ["mp3", "wav", "ogg", "m4a", "flac", "aac", "wma", "opus"]
    
    # Настройки транскрибации
    DEFAULT_LANGUAGE: str = "ru"
    SUPPORTED_LANGUAGES: List[str] = ["ru", "en"]
    WHISPER_MODEL: str = "whisper-1"
    WHISPER_LANGUAGE: str = "ru"
    
    # ========== НАСТРОЙКИ АВАТАРОВ ==========
    
    # Тестовый режим аватаров (для отладки)
    AVATAR_TEST_MODE: bool = Field(False, env="AVATAR_TEST_MODE")
    
    # Лимиты фотографий
    AVATAR_MIN_PHOTOS: int = Field(10, env="AVATAR_MIN_PHOTOS")
    AVATAR_MAX_PHOTOS: int = Field(20, env="AVATAR_MAX_PHOTOS")
    
    AVATAR_MAX_PHOTOS_PER_USER: int = Field(5, env="AVATAR_MAX_PHOTOS_PER_USER")
    
    # Ограничения файлов
    PHOTO_MAX_SIZE: int = Field(20 * 1024 * 1024, env="PHOTO_MAX_SIZE")  # 20MB
    PHOTO_MIN_RESOLUTION: int = Field(512, env="PHOTO_MIN_RESOLUTION")
    PHOTO_MAX_RESOLUTION: int = Field(4096, env="PHOTO_MAX_RESOLUTION")
    PHOTO_ALLOWED_FORMATS: List[str] = Field(["jpg", "jpeg", "png", "webp"], env="PHOTO_ALLOWED_FORMATS")
    
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
    AVATAR_CREATION_COST: float = Field(150.0, env="AVATAR_CREATION_COST")  # Создание аватара
    IMAGE_GENERATION_COST: float = Field(5.0, env="IMAGE_GENERATION_COST")  # Генерация фото
    VIDEO_5S_GENERATION_COST: float = Field(20.0, env="VIDEO_5S_GENERATION_COST")  # Видео 5 сек
    VIDEO_10S_GENERATION_COST: float = Field(40.0, env="VIDEO_10S_GENERATION_COST")  # Видео 10 сек
    VIDEO_PRO_5S_GENERATION_COST: float = Field(30.0, env="VIDEO_PRO_5S_GENERATION_COST")  # Видео PRO 5 сек
    VIDEO_PRO_10S_GENERATION_COST: float = Field(60.0, env="VIDEO_PRO_10S_GENERATION_COST")  # Видео PRO 10 сек
    PORN_VIDEO_5S_GENERATION_COST: float = Field(30.0, env="PORN_VIDEO_5S_GENERATION_COST")  # Парное видео 5 сек
    PORN_VIDEO_10S_GENERATION_COST: float = Field(60.0, env="PORN_VIDEO_10S_GENERATION_COST")  # Парное видео 10 сек
    TRANSCRIPTION_COST_PER_MINUTE: float = Field(10.0, env="TRANSCRIPTION_COST_PER_MINUTE")  # Транскрибация за минуту
    
    # Пакеты пополнения баланса
    TOPUP_PACKAGES: dict = Field(default={
        "small": {"coins": 250, "price_rub": 490, "price_kzt": 2500, "popular": False},
        "medium": {"coins": 500, "price_rub": 870, "price_kzt": 4900, "popular": True},
        "large": {"coins": 1000, "price_rub": 1540, "price_kzt": 8800, "popular": False}
    }, env="TOPUP_PACKAGES")
    
    # Ссылки на документы
    OFFER_URL: str = Field("https://telegra.ph/Dogovor-publichnoj-oferty-06-06-2", env="OFFER_URL")
    PRIVACY_URL: str = Field("https://telegra.ph/Politika-konfidencialnosti-i-obrabotki-personalnyh-dannyh-06-06-2", env="PRIVACY_URL")
    
    # Управление хранением фотографий
    DELETE_PHOTOS_AFTER_TRAINING: bool = Field(True, env="DELETE_PHOTOS_AFTER_TRAINING")  # Удалять фото после обучения
    KEEP_PREVIEW_PHOTO: bool = Field(True, env="KEEP_PREVIEW_PHOTO")  # Оставлять первое фото как превью
    
    # ========== КОНЕЦ НАСТРОЕК АВАТАРОВ ==========
    
    # Настройки хранения
    STORAGE_CLEANUP_DAYS: int = 7
    
    # Настройки логирования
    LOG_LEVEL: str = Field(default="DEBUG", env="LOG_LEVEL")  # Изменено с INFO на DEBUG
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # Детальное логирование
    ENABLE_SQL_LOGGING: bool = Field(default=False, env="ENABLE_SQL_LOGGING")
    ENABLE_TELEGRAM_LOGGING: bool = Field(default=True, env="ENABLE_TELEGRAM_LOGGING")
    ENABLE_TRANSCRIPTION_LOGGING: bool = Field(default=True, env="ENABLE_TRANSCRIPTION_LOGGING")
    LOG_TO_FILE: bool = Field(default=True, env="LOG_TO_FILE")
    LOG_FILE_PATH: str = Field(default="/app/logs/aisha-bot.log", env="LOG_FILE_PATH")
    
    # Настройки детального логирования ошибок
    ENABLE_DETAILED_ERROR_LOGGING: bool = Field(default=True, env="ENABLE_DETAILED_ERROR_LOGGING")
    LOG_STACK_TRACES: bool = Field(default=True, env="LOG_STACK_TRACES")
    
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
    
    # Настройки пула соединений БД
    DB_ECHO: bool = Field(default=False)  # Логирование SQL запросов
    DB_POOL_SIZE: int = Field(default=5)  # Размер пула соединений
    DB_MAX_OVERFLOW: int = Field(default=10)  # Максимальное переполнение пула
    DB_POOL_TIMEOUT: int = Field(default=30)  # Таймаут получения соединения из пула
    DB_POOL_RECYCLE: int = Field(default=3600)  # Время жизни соединения в секундах
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        """Автоматически собираем DATABASE_URL из переменных PostgreSQL"""
        if isinstance(v, str) and v:
            return v
        return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_HOST')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
    
    # MinIO
    MINIO_ENDPOINT: Optional[str] = Field(default="192.168.0.4:9000")
    MINIO_ACCESS_KEY: Optional[str] = Field(default="minioadmin")
    MINIO_SECRET_KEY: Optional[str] = Field(default="74rSbw9asQ1uMzcFeM5G")
    MINIO_BUCKET_NAME: Optional[str] = Field(default="aisha")
    MINIO_SECURE: bool = Field(default=False)  # 🎯 ВАЖНО: отключаем SSL для локального сервера
    MINIO_BUCKET_AVATARS: Optional[str] = Field(default="avatars")
    MINIO_BUCKET_PHOTOS: Optional[str] = Field(default="photos")
    MINIO_BUCKET_TEMP: Optional[str] = Field(default="temp")
    MINIO_PRESIGNED_EXPIRES: int = Field(default=3600)  # Время истечения presigned URL в секундах
    TEMP_DIR: Path = Path("/tmp") if os.name != 'nt' else Path(os.environ.get('TEMP', 'temp'))
    
    # Настройки алертов
    ENABLE_ALERTS: bool = False
    ALERT_EMAIL: Optional[str] = None
    ALERT_SLACK_WEBHOOK: Optional[str] = None
    
    # Backend - LEGACY удален
    # BACKEND_URL: Optional[str] = None
    
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
    
    # Настройки временных файлов
    TEMP_FILE_CLEANUP_INTERVAL: int = 3600  # Очистка каждый час (в секундах)
    TEMP_FILE_MAX_AGE: int = 3600  # Максимальный возраст временных файлов (1 час)
    AUTO_CLEANUP_ENABLED: bool = True  # Автоматическая очистка временных файлов
    
    class Config:
        """Конфигурация Pydantic"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Разрешаем дополнительные поля в переменных окружения

# Создаем экземпляр настроек
settings = Settings()
