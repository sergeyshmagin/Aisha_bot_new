"""
Валидатор данных обучения аватаров - строгие правила
"""
from typing import Dict, Any, Optional, Tuple
from uuid import UUID
import logging
import re
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from ...core.logger import get_logger
from ...database.models import Avatar, AvatarTrainingType, AvatarStatus

logger = get_logger(__name__)class AvatarTrainingDataValidator:
    """
    Валидатор для обеспечения корректной записи данных при обучении аватаров
    
    СТРОГИЕ ПРАВИЛА:
    - Style аватары: ТОЛЬКО finetune_id, diffusers_lora_file_url = NULL
    - Portrait аватары: ТОЛЬКО diffusers_lora_file_url, finetune_id = NULL
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def validate_and_fix_training_completion(
        self,
        avatar: Avatar,
        webhook_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Валидирует и исправляет данные завершения обучения
        Обеспечивает строгое соответствие правилам типов аватаров
        
        Args:
            avatar: Аватар для обновления
            webhook_result: Результат от FAL AI webhook
            
        Returns:
            Dict[str, Any]: Исправленные данные для обновления аватара
        """
        logger.info(f"🔍 Валидация данных обучения для аватара {avatar.id} ({avatar.training_type})")
