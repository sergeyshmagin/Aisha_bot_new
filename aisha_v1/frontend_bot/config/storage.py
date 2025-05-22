"""
Настройки хранилища (MinIO).
"""

from pathlib import Path
from typing import List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from datetime import timedelta

class StorageConfig(BaseSettings):
    """Настройки хранилища."""
    
    # MinIO
    MINIO_ENDPOINT: str = Field(..., env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(..., env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(..., env="MINIO_SECRET_KEY")
    MINIO_SECURE: bool = Field(False, env="MINIO_SECURE")
    MINIO_BUCKET: str = Field(..., env="MINIO_BUCKET")
    
    # Бакеты MinIO
    MINIO_BUCKETS: Dict[str, str] = Field(
        default={
            "avatars": "avatars",  # Аватары пользователей
            "transcripts": "transcripts",  # Транскрипты
            "documents": "documents",  # Документы (протоколы, отчеты)
            "temp": "temp",  # Временные файлы
            "test": "test-bucket"  # Тестовый бакет
        }
    )
    
    # Пути
    AVATAR_STORAGE_PATH: Path = Field(default_factory=lambda: Path("storage/avatars"))
    TRANSCRIPTS_PATH: Path = Field(default_factory=lambda: Path("storage/transcripts"))
    THUMBNAIL_PATH: Path = Field(default_factory=lambda: Path("storage/avatars/thumbnails"))
    AVATAR_DIR: str = Field("avatars")
    
    # Лимиты файлов
    MAX_FILE_SIZE: int = Field(50 * 1024 * 1024, env="MAX_FILE_SIZE", ge=1)  # 50 MB
    MAX_AUDIO_DURATION: int = Field(3600, env="MAX_AUDIO_DURATION", ge=1)  # 1 час
    MAX_VIDEO_DURATION: int = Field(3600, env="MAX_VIDEO_DURATION", ge=1)  # 1 час
    MAX_PHOTO_SIZE: int = Field(20 * 1024 * 1024, env="MAX_PHOTO_SIZE", ge=1)  # 20 MB
    
    # Разрешенные форматы
    ALLOWED_AUDIO_FORMATS: List[str] = Field(["mp3", "wav", "ogg", "m4a", "flac", "aac", "wma", "opus"])
    ALLOWED_VIDEO_FORMATS: List[str] = Field(["mp4", "mov", "avi", "mkv"])
    ALLOWED_PHOTO_FORMATS: List[str] = Field(["jpg", "jpeg", "png"])
    
    # Лимиты аватаров
    AVATAR_MIN_PHOTOS: int = Field(10, env="AVATAR_MIN_PHOTOS", ge=1)
    AVATAR_MAX_PHOTOS: int = Field(20, env="AVATAR_MAX_PHOTOS", ge=1)
    AVATARS_PER_PAGE: int = Field(3, env="AVATARS_PER_PAGE", ge=1)
    PHOTO_MAX_MB: int = Field(20, env="PHOTO_MAX_MB", ge=1)
    PHOTO_MIN_RES: int = Field(512, env="PHOTO_MIN_RES", ge=1)
    THUMBNAIL_SIZE: int = Field(256, env="THUMBNAIL_SIZE", ge=1)
    
    # Эмодзи
    PROGRESSBAR_EMOJI_FILLED: str = Field("🟩")
    PROGRESSBAR_EMOJI_CURRENT: str = Field("🟦")
    PROGRESSBAR_EMOJI_EMPTY: str = Field("⬜")
    
    # Статусы
    AVATAR_STATUS_TRAINING: str = Field("Обучается...")
    AVATAR_STATUS_READY: str = Field("Готов")
    AVATAR_STATUS_ERROR: str = Field("Ошибка")
    
    # Гендеры
    AVATAR_GENDER_MALE: str = Field("Мужской")
    AVATAR_GENDER_FEMALE: str = Field("Женский")
    AVATAR_GENDER_OTHER: str = Field("Другое")
    
    @validator("ALLOWED_AUDIO_FORMATS", "ALLOWED_VIDEO_FORMATS", "ALLOWED_PHOTO_FORMATS")
    def validate_formats(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Formats list cannot be empty")
        return [f.lower() for f in v]
    
    @validator("AVATAR_MAX_PHOTOS")
    def validate_max_photos(cls, v: int, values: Dict[str, Any]) -> int:
        if v < values.get("AVATAR_MIN_PHOTOS", 1):
            raise ValueError("AVATAR_MAX_PHOTOS must be greater than AVATAR_MIN_PHOTOS")
        return v
    
    @property
    def minio_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию MinIO."""
        return {
            "endpoint": self.MINIO_ENDPOINT,
            "access_key": self.MINIO_ACCESS_KEY,
            "secret_key": self.MINIO_SECRET_KEY,
            "secure": self.MINIO_SECURE
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Разрешаем дополнительные поля из .env

# Структура бакетов
BUCKET_STRUCTURES: Dict[str, Dict[str, Any]] = {
    "avatars": {
        "path": "avatars/{user_id}/{avatar_id}",
        "files": {
            "original": "original.png",
            "processed": "processed.webp",
            "metadata": "metadata.json"
        }
    },
    "transcripts": {
        "path": "transcripts/{user_id}/{session_id}",
        "files": {
            "original": "original.mp3",
            "transcript": "transcript.txt",
            "summary": "summary.json"
        }
    },
    "documents": {
        "path": "documents/{user_id}/{doc_id}",
        "files": {
            "protocol": "protocol.docx",
            "pdf": "protocol.pdf"
        }
    },
    "temp": {
        "path": "temp/{user_id}/{timestamp}",
        "files": {
            "any": "*"
        }
    }
}

# Политики хранения
RETENTION_POLICIES: Dict[str, Dict[str, Any]] = {
    "avatars": {
        "expiry": None,  # Бессрочное хранение
        "versioning": True
    },
    "transcripts": {
        "expiry": timedelta(days=90),  # 90 дней
        "versioning": False
    },
    "documents": {
        "expiry": None,  # Бессрочное хранение
        "versioning": True
    },
    "temp": {
        "expiry": timedelta(days=3),  # 3 дня
        "versioning": False
    }
}

# Лимиты файлов
FILE_LIMITS: Dict[str, Dict[str, int]] = {
    "avatars": {
        "max_size": 10 * 1024 * 1024,  # 10 MB
        "max_count": 5
    },
    "transcripts": {
        "max_size": 50 * 1024 * 1024,  # 50 MB
        "max_duration": 3600  # 1 час
    },
    "documents": {
        "max_size": 20 * 1024 * 1024,  # 20 MB
        "max_count": 10
    },
    "temp": {
        "max_size": 100 * 1024 * 1024,  # 100 MB
        "max_age": 3 * 24 * 3600  # 3 дня в секундах
    }
}

# Форматы файлов
FILE_FORMATS: Dict[str, list] = {
    "avatars": ["png", "jpg", "jpeg", "webp"],
    "transcripts": ["mp3", "wav", "ogg"],
    "documents": ["docx", "pdf", "txt"],
    "temp": ["*"]  # Любые форматы
} 