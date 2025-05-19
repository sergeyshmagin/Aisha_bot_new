"""
Базовые настройки приложения.
"""

from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator

class BaseConfig(BaseSettings):
    """Базовые настройки приложения."""
    
    # Пути
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    STORAGE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "storage")
    LOGS_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "logs")
    DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    TEMP_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "temp")
    AVATAR_FSM_PATH: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "storage" / "avatar_fsm")
    AVATAR_PHOTOS_PATH: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "storage" / "avatar_photos")
    
    # Логирование
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_DATE_FORMAT: str = Field("%Y-%m-%d %H:%M:%S")
    LOG_MAX_BYTES: int = Field(10 * 1024 * 1024)  # 10 MB
    LOG_BACKUP_COUNT: int = Field(5)
    
    # Безопасность
    ALLOWED_USERS: List[int] = Field(default_factory=list, env="ALLOWED_USERS")
    ADMIN_IDS: List[int] = Field(default_factory=list, env="ADMIN_IDS")
    
    # Мониторинг
    ENABLE_METRICS: bool = Field(True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(9090, env="METRICS_PORT", ge=1, le=65535)
    
    # Баланс
    INITIAL_BALANCE: float = Field(100.0, env="INITIAL_BALANCE", ge=0)
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
    CACHE_TTL: int = Field(3600, env="CACHE_TTL", ge=1)  # 1 час
    CACHE_MAX_SIZE: int = Field(1000, env="CACHE_MAX_SIZE", ge=1)
    
    # Настройки очередей
    QUEUE_PREFIX: str = Field("queue:")
    MAX_RETRIES: int = Field(3, ge=1)
    RETRY_DELAY: int = Field(60, ge=1)  # секунд
    
    # Настройки показа галереи
    GALLERY_DEBOUNCE_TIMEOUT: int = Field(2, env="GALLERY_DEBOUNCE_TIMEOUT", ge=1)  # секунд
    
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
        env_file = ".env"
        case_sensitive = True 