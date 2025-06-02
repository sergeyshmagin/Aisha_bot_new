"""
Сервис генерации изображений с FAL AI
"""
import asyncio
import os
from typing import Dict, List, Optional, Any
from uuid import UUID

import fal_client

from ...core.config import settings
from ...core.logger import get_logger
from ...database.models import Avatar, AvatarTrainingType

logger = get_logger(__name__)class FALGenerationService:
    """
    Сервис для генерации изображений с обученными моделями FAL AI.
    
    Поддерживает:
    - Портретные аватары (LoRA файлы)
    - Стилевые аватары (finetune_id)
    - Тестовый режим
    """

    def __init__(self):
        self.api_key = settings.effective_fal_api_key
