"""
Модели данных для загрузки фотографий
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID

class PhotoUploadState(BaseModel):
    """Состояние загрузки фотографий"""
    avatar_id: UUID = Field(..., description="ID аватара")
    avatar_name: str = Field(..., description="Имя аватара")
    gender: str = Field(..., description="Пол аватара")
    training_type: str = Field(..., description="Тип обучения")
    photos_count: int = Field(default=0, description="Количество загруженных фото")
    min_photos: int = Field(default=10, description="Минимум фото")
    max_photos: int = Field(default=20, description="Максимум фото")

class PhotoUploadConfig:
    """Конфигурация загрузки фотографий"""
    MIN_PHOTOS = 10
    MAX_PHOTOS = 20
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    MIN_RESOLUTION = 512  # 512x512 пикселей
    SUPPORTED_FORMATS = ["jpg", "jpeg", "png"]
