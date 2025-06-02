# LEGACY: Весь этот сервис предназначен только для Style аватаров (finetune_id)
# Теперь используются только Portrait аватары с LoRA файлами
# Сервис больше не используется и может быть удален в будущем

"""
LEGACY: Сервис для автоматического обновления finetune_id аватаров

Этот сервис предназначен для массового обновления finetune_id у аватаров
в случае проблем с валидацией или обновления API.

Основные функции:
- Обновления устаревших finetune_id
- Массовые обновления по маппингу
- Поиск проблемных записей
- Валидация UUID формата finetune_id

ВАЖНО: Работает только со Style аватарами (AvatarTrainingType.STYLE)
Portrait аватары используют LoRA файлы, а не finetune_id
"""

# from typing import List, Dict, Any, Optional
# from uuid import UUID
# import re

# from sqlalchemy import select, update
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.core.logger import get_logger
# from app.database.models import Avatar, AvatarTrainingType
# from app.core.di import get_db_session

# logger = get_logger(__name__)


# class FinetuneUpdaterService:
#     """
#     LEGACY: Сервис для автоматического обновления finetune_id аватаров
#     Теперь все аватары используют Portrait модель с LoRA файлами
#     """
    
#     def __init__(self):
#         """Инициализация сервиса"""
#         logger.info("🔧 FinetuneUpdaterService инициализирован")

#     async def update_finetune_id_by_name(
#         self,
#         avatar_name: str,
#         new_finetune_id: str,
#         user_id: Optional[UUID] = None,
#         reason: str = "Manual update"
#     ) -> bool:
#         """
#         LEGACY: Обновляет finetune_id аватара по имени
        
#         Args:
#             avatar_name: Имя аватара для поиска
#             new_finetune_id: Новый finetune_id
#             user_id: ID пользователя для дополнительной фильтрации (опционально)
#             reason: Причина обновления для логирования
            
#         Returns:
#             bool: True если обновление прошло успешно
#         """
#         # ... rest of legacy code 