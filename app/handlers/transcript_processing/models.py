"""
Модели для обработки транскриптов
"""
from typing import Dict, Any
from pydantic import BaseModel, Field

class TranscriptResult(BaseModel):
    """Модель результата транскрипта"""
    id: str = Field(..., description="Уникальный идентификатор транскрипта")
    transcript_key: str = Field(..., description="Ключ для доступа к транскрипту в хранилище")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные транскрипта")
