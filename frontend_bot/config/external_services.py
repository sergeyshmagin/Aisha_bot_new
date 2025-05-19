"""
Конфигурация внешних сервисов.
"""

import os
from typing import Dict, Any, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator, HttpUrl
from enum import Enum

# Базовые настройки
EXTERNAL_SERVICES: Dict[str, Dict[str, Any]] = {
    "minio": {
        "endpoint": os.getenv("MINIO_ENDPOINT", "192.168.0.4:9000"),
        "access_key": os.getenv("MINIO_ACCESS_KEY", "aisha_minio"),
        "secret_key": os.getenv("MINIO_SECRET_KEY", ""),
        "secure": False,
    },
    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "password": os.getenv("REDIS_PASSWORD", ""),
        "db": 0,
    }
}

# Настройки для тестов
TEST_SERVICES: Dict[str, Dict[str, Any]] = {
    "minio": {
        "endpoint": os.getenv("TEST_MINIO_ENDPOINT", "192.168.0.4:9000"),
        "access_key": os.getenv("TEST_MINIO_ACCESS_KEY", "aisha_test"),
        "secret_key": os.getenv("TEST_MINIO_SECRET_KEY", ""),
        "secure": False,
    },
    "redis": {
        "host": os.getenv("TEST_REDIS_HOST", "localhost"),
        "port": int(os.getenv("TEST_REDIS_PORT", "6379")),
        "password": os.getenv("TEST_REDIS_PASSWORD", ""),
        "db": 1,
    }
}

# Бакеты MinIO
MINIO_BUCKETS = {
    "avatars": "avatars",  # Аватары пользователей
    "transcripts": "transcripts",  # Транскрипты
    "documents": "documents",  # Документы (протоколы, отчеты)
    "temp": "temp",  # Временные файлы
    "test": "test-bucket"  # Тестовый бакет
}

# Политики хранения (в днях)
RETENTION_POLICIES = {
    "avatars": None,  # Бессрочно
    "documents": None,  # Бессрочно
    "transcripts": 90,  # 90 дней
    "temp": 3,  # 3 дня
    "test": 1  # 1 день для тестов
}

# Структура бакетов
BUCKET_STRUCTURES = {
    "avatars": {
        "pattern": "users/{user_id}/avatars/{avatar_id}/{file_type}",
        "file_types": ["original.png", "processed.webp", "metadata.json"]
    },
    "transcripts": {
        "pattern": "users/{user_id}/transcripts/{session_id}/{file_type}",
        "file_types": ["original.mp3", "transcript.txt", "summary.json"]
    },
    "documents": {
        "pattern": "users/{user_id}/documents/{doc_id}/{file_type}",
        "file_types": ["protocol.docx", "protocol.pdf"]
    },
    "temp": {
        "pattern": "temp/{user_id}/{timestamp}/{file_name}",
        "file_types": None  # Любые файлы
    }
}

class FalMode(str, Enum):
    CHARACTER = "character"
    STYLE = "style"
    CUSTOM = "custom"

class FalPriority(str, Enum):
    QUALITY = "quality"
    SPEED = "speed"
    BALANCED = "balanced"

class ExternalServicesConfig(BaseSettings):
    # Telegram
    TELEGRAM_TOKEN: str = Field(..., env="TELEGRAM_TOKEN", min_length=1)
    TELEGRAM_WEBHOOK_URL: Optional[HttpUrl] = Field(None, env="TELEGRAM_WEBHOOK_URL")
    
    # OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY", min_length=1)
    OPENAI_EMAIL: Optional[str] = Field(None, env="OPENAI_EMAIL")
    OPENAI_PASSWORD: Optional[str] = Field(None, env="OPENAI_PASSWORD")
    OPENAI_MODEL: str = Field("gpt-3.5-turbo", env="OPENAI_MODEL")
    ASSISTANT_ID: str = Field(..., env="ASSISTANT_ID", min_length=1)
    
    # FAL.AI
    FAL_KEY: str = Field(..., env="FAL_KEY", min_length=1)
    FAL_WEBHOOK_URL: HttpUrl = Field("https://aibots.kz/api/avatar/status_update", env="FAL_WEBHOOK_URL")
    FAL_MODE: FalMode = Field(FalMode.CHARACTER, env="FAL_MODE")
    FAL_ITERATIONS: int = Field(500, env="FAL_ITERATIONS", ge=1, le=1000)
    FAL_PRIORITY: FalPriority = Field(FalPriority.QUALITY, env="FAL_PRIORITY")
    FAL_CAPTIONING: bool = Field(True, env="FAL_CAPTIONING")
    FAL_TRIGGER_WORD: str = Field("TOK", env="FAL_TRIGGER_WORD", min_length=1)
    FAL_LORA_RANK: int = Field(32, env="FAL_LORA_RANK", ge=1, le=128)
    FAL_FINETUNE_TYPE: str = Field("full", env="FAL_FINETUNE_TYPE")
    FAL_TRAINING_TEST_MODE: bool = Field(False, env="FAL_TRAINING_TEST_MODE")
    
    # Astria
    ASTRIA_API_KEY: Optional[str] = Field(None, env="ASTRIA_API_KEY")
    
    # Backend
    BACKEND_URL: HttpUrl = Field("http://localhost:8000", env="BACKEND_URL")
    
    # MinIO
    MINIO_ENDPOINT: str = Field(..., env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(..., env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(..., env="MINIO_SECRET_KEY")
    MINIO_SECURE: bool = Field(False, env="MINIO_SECURE")
    MINIO_BUCKET: str = Field(..., env="MINIO_BUCKET")
    
    # Redis
    REDIS_HOST: str = Field(..., env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT", ge=1, le=65535)
    REDIS_DB: int = Field(0, env="REDIS_DB", ge=0)
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    REDIS_SSL: bool = Field(False, env="REDIS_SSL")
    REDIS_POOL_SIZE: int = Field(10, env="REDIS_POOL_SIZE", ge=1)
    REDIS_POOL_TIMEOUT: int = Field(5, env="REDIS_POOL_TIMEOUT", ge=1)
    REDIS_RETRY_ON_TIMEOUT: bool = Field(True, env="REDIS_RETRY_ON_TIMEOUT")
    REDIS_MAX_RETRIES: int = Field(3, env="REDIS_MAX_RETRIES", ge=1)
    REDIS_RETRY_INTERVAL: int = Field(1, env="REDIS_RETRY_INTERVAL", ge=1)
    
    # PostgreSQL
    POSTGRES_HOST: str = Field("192.168.0.4", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT", ge=1, le=65535)
    POSTGRES_DB: str = Field(..., env="POSTGRES_DB")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    DATABASE_URL: Optional[str] = Field(None, env="DATABASE_URL")
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_HOST')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
    
    @validator("FAL_ITERATIONS")
    def validate_fal_iterations(cls, v: int) -> int:
        if v < 1 or v > 1000:
            raise ValueError("FAL_ITERATIONS must be between 1 and 1000")
        return v
    
    @validator("FAL_LORA_RANK")
    def validate_fal_lora_rank(cls, v: int) -> int:
        if v < 1 or v > 128:
            raise ValueError("FAL_LORA_RANK must be between 1 and 128")
        return v
    
    @property
    def redis_url(self) -> str:
        protocol = "rediss" if self.REDIS_SSL else "redis"
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"{protocol}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    model_config = {"extra": "allow"} 