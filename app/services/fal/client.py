"""
FAL AI клиент для обучения моделей аватаров
"""
import asyncio
import io
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID

import fal_client
from PIL import Image

from ...core.config import settings
from ...core.logger import get_logger

logger = get_logger(__name__)class FalAIClient:
    """
    Клиент для работы с FAL AI API.
    
    Основные функции:
    - Обучение персональных моделей (finetune)
    - Мониторинг прогресса обучения
    - Генерация изображений с обученными моделями
    - Управление файлами и архивами
    """

    def __init__(self):
        self.logger = logger
        self.api_key = settings.FAL_API_KEY
        self.test_mode = settings.AVATAR_TEST_MODE
