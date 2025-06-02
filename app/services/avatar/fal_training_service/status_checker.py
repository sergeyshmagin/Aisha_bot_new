"""
Модуль для активного опрашивания статуса обучения в FAL AI
Резервный механизм на случай если webhook не доходит
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from app.core.logger import get_logger
from app.core.config import settings
from app.database.models import Avatar, AvatarStatus, AvatarTrainingType
from app.core.database import get_session

logger = get_logger(__name__)class FALStatusChecker:
    """Активное опрашивание статуса обучения в FAL AI"""
    
    def __init__(self):
        self.fal_api_key = settings.FAL_API_KEY or settings.FAL_KEY
        self.check_interval = 60  # Проверяем каждую минуту
        self.max_check_duration = 3600  # Максимум 1 час проверок
        
    async def start_status_monitoring(self, avatar_id: UUID, request_id: str, training_type: str) -> None:
        """
        Запускает мониторинг статуса обучения
        
        Args:
            avatar_id: ID аватара
            request_id: ID запроса в FAL AI
            training_type: Тип обучения (portrait/style)
        """
        logger.info(f"🔍 Запуск мониторинга статуса для аватара {avatar_id}, request_id: {request_id}")
