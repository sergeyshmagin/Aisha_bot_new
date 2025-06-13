"""
Модели данных для работы с Imagen 4 API
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class AspectRatio(str, Enum):
    """Доступные соотношения сторон для Imagen 4"""
    SQUARE = "1:1"
    LANDSCAPE_4_3 = "4:3"
    LANDSCAPE_16_9 = "16:9"
    PORTRAIT_3_4 = "3:4"
    PORTRAIT_9_16 = "9:16"


class Imagen4Request(BaseModel):
    """Запрос к Imagen 4 API"""
    prompt: str = Field(..., description="Промпт для генерации")
    negative_prompt: Optional[str] = Field("", description="Негативный промпт")
    aspect_ratio: AspectRatio = Field(AspectRatio.SQUARE, description="Соотношение сторон")
    num_images: int = Field(1, ge=1, le=4, description="Количество изображений (1-4)")
    seed: Optional[int] = Field(None, description="Seed для воспроизводимости")


class Imagen4Image(BaseModel):
    """Информация об изображении от Imagen 4"""
    url: str = Field(..., description="URL изображения")
    content_type: Optional[str] = Field(None, description="MIME тип")
    file_name: Optional[str] = Field(None, description="Имя файла")
    file_size: Optional[int] = Field(None, description="Размер файла в байтах")


class Imagen4Response(BaseModel):
    """Ответ от Imagen 4 API"""
    images: List[Imagen4Image] = Field(..., description="Сгенерированные изображения")
    seed: Optional[int] = Field(None, description="Использованный seed")
    request_id: Optional[str] = Field(None, description="ID запроса")


class Imagen4GenerationStatus(str, Enum):
    """Статусы генерации Imagen 4"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Imagen4GenerationResult(BaseModel):
    """Результат генерации с дополнительной информацией"""
    status: Imagen4GenerationStatus
    response: Optional[Imagen4Response] = None
    error_message: Optional[str] = None
    generation_time: Optional[float] = None
    cost_credits: float = Field(5.0, description="Стоимость в кредитах")
    
    
class Imagen4Config(BaseModel):
    """Конфигурация Imagen 4 сервиса"""
    api_key: str
    enabled: bool = True
    default_aspect_ratio: AspectRatio = AspectRatio.SQUARE
    max_images: int = 4
    generation_cost: float = 5.0
    api_endpoint: str = "fal-ai/imagen4/preview"
    timeout_seconds: int = 300  # 5 минут 