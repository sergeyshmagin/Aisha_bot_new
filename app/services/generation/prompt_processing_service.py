"""
Сервис обработки промптов для генерации изображений
Создает детальные, профессиональные промпты для максимального качества генерации
"""
import aiohttp
from typing import Optional, Dict, Any
import time
import random
import re
import json

from app.core.config import settings
from app.core.logger import get_logger
from app.shared.utils.openai import get_openai_headers

logger = get_logger(__name__)class PromptProcessingService:
    """Сервис для создания детальных профессиональных промптов"""
    
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o"
    
    async def process_prompt(self, user_prompt: str, avatar_type: str) -> Dict[str, Any]:
        """
        Обрабатывает пользовательский промпт для FLUX Pro v1.1 Ultra
        Создает фотореалистичный промпт по шпаргалке и оптимизированный negative prompt
        
        Args:
            user_prompt: Промпт от пользователя
            avatar_type: Тип аватара (portrait, style, etc.)
            
        Returns:
            dict: Результат обработки с processed prompt и negative prompt
        """
        start_time = time.time()
        
        try:
            logger.info(f"[Prompt Processing] Начата обработка: '{user_prompt[:50]}...'")
