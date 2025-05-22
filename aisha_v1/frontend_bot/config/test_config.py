"""
Тестовая конфигурация для тестов.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator, HttpUrl

from .base import BaseConfig
from .database import DatabaseConfig
from .storage import StorageConfig
from .external_services import (
    MINIO_BUCKETS,
    RETENTION_POLICIES,
    BUCKET_STRUCTURES,
    FalMode,
    FalPriority,
    ExternalServicesConfig
)

class TestConfig(BaseConfig, DatabaseConfig, StorageConfig, ExternalServicesConfig):
    """Тестовая конфигурация."""
    
    # Тестовые настройки базы данных
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "test_db"
    POSTGRES_USER: str = "test_user"
    POSTGRES_PASSWORD: str = "test_password"
    
    # Тестовые настройки Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1
    REDIS_PASSWORD: str = None
    
    # Тестовые настройки MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "test_access_key"
    MINIO_SECRET_KEY: str = "test_secret_key"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "test-bucket"
    
    # Тестовые настройки OpenAI
    OPENAI_API_KEY: str = "test_api_key"
    ASSISTANT_ID: str = "test_assistant_id"
    
    # Тестовые настройки Telegram
    TELEGRAM_TOKEN: str = "test_token"
    
    # Системные пути
    PYTHONPATH: Optional[str] = Field(None, env="PYTHONPATH")
    TEST_DATABASE_URL: Optional[str] = Field(None, env="TEST_DATABASE_URL")
    
    # Пути приложения
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    STORAGE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "storage")
    LOGS_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")
    DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    TEMP_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "temp")
    
    # Логирование
    LOG_LEVEL: str = Field("DEBUG", env="LOG_LEVEL")
    LOG_FORMAT: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_DATE_FORMAT: str = Field("%Y-%m-%d %H:%M:%S")
    LOG_MAX_BYTES: int = Field(10 * 1024 * 1024)  # 10 MB
    LOG_BACKUP_COUNT: int = Field(5)
    
    # Безопасность
    ALLOWED_USERS: List[int] = Field(default=[123456789], env="ALLOWED_USERS")
    ADMIN_IDS: List[int] = Field(default=[123456789], env="ADMIN_IDS")
    
    # Мониторинг
    ENABLE_METRICS: bool = Field(False, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(9091, env="METRICS_PORT", ge=1, le=65535)
    
    # Баланс
    INITIAL_BALANCE: float = Field(1000.0, env="INITIAL_BALANCE", ge=0)
    MIN_BALANCE: float = Field(0.0, env="MIN_BALANCE", ge=0)
    COIN_PRICE: float = Field(1.0, env="COIN_PRICE", gt=0)
    
    # Стоимость сервисов
    AVATAR_CREATION_COST: float = Field(10.0, env="AVATAR_CREATION_COST", ge=0)
    TRANSCRIPT_COST: float = Field(5.0, env="TRANSCRIPT_COST", ge=0)
    PHOTO_ENHANCE_COST: float = Field(3.0, env="PHOTO_ENHANCE_COST", ge=0)
    
    # Настройки бота
    MAX_MESSAGE_LENGTH: int = Field(4096, ge=1)
    MAX_VOICE_DURATION: int = Field(300, ge=1)  # секунд
    DEFAULT_LANGUAGE: str = Field("ru")
    SUPPORTED_LANGUAGES: List[str] = Field(["ru", "en"])
    
    # Настройки кэширования
    CACHE_ENABLED: bool = Field(True, env="CACHE_ENABLED")
    CACHE_TTL: int = Field(60, env="CACHE_TTL", ge=1)  # 1 минута для тестов
    CACHE_MAX_SIZE: int = Field(100, env="CACHE_MAX_SIZE", ge=1)
    
    # Настройки очередей
    QUEUE_PREFIX: str = Field("test_queue:")
    MAX_RETRIES: int = Field(2, ge=1)
    RETRY_DELAY: int = Field(1, ge=1)  # 1 секунда для тестов
    
    # Структуры данных из продакшена
    MINIO_BUCKETS: Dict[str, str] = Field(default=MINIO_BUCKETS)
    RETENTION_POLICIES: Dict[str, int] = Field(default=RETENTION_POLICIES)
    BUCKET_STRUCTURES: Dict[str, Dict[str, str]] = Field(default=BUCKET_STRUCTURES)
    
    # Заглушки для обязательных внешних сервисов
    FAL_KEY: str = Field("test_fal_key", env="FAL_KEY")
    FAL_MODE: FalMode = Field(FalMode.CHARACTER, env="FAL_MODE")
    FAL_PRIORITY: FalPriority = Field(FalPriority.QUALITY, env="FAL_PRIORITY")
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_HOST')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
    
    @validator("ALLOWED_USERS", "ADMIN_IDS", pre=True)
    def parse_int_list(cls, v: str) -> List[int]:
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v
    
    @validator("SUPPORTED_LANGUAGES")
    def validate_languages(cls, v: List[str], values) -> List[str]:
        if not v:
            raise ValueError("SUPPORTED_LANGUAGES cannot be empty")
        if values.get("DEFAULT_LANGUAGE") not in v:
            raise ValueError("DEFAULT_LANGUAGE must be in SUPPORTED_LANGUAGES")
        return v
    
    class Config:
        env_file = ".env.test"
        case_sensitive = True 