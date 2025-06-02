"""
Отслеживание прогресса обучения аватаров
Выделено из app/services/avatar/training_service.py для соблюдения правила ≤500 строк
"""
from typing import Dict, Any, Optional
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import Avatar
from app.services.fal.client import FalAIClient
from .models import TrainingProgress

logger = logging.getLogger(__name__)class ProgressTracker:
    """Отслеживание прогресса обучения аватаров"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.fal_client = FalAIClient()
    
    async def get_training_progress(self, avatar_id: UUID) -> Dict[str, Any]:
        """
        Получает прогресс обучения аватара
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            Dict[str, Any]: Информация о прогрессе обучения
        """
        try:
            query = select(Avatar).where(Avatar.id == avatar_id)
            result = await self.session.execute(query)
            avatar = result.scalar_one_or_none()
            
            if not avatar:
                raise ValueError(f"Аватар {avatar_id} не найден")
            
            # Базовая информация
            progress_info = {
                "avatar_id": str(avatar_id),
                "status": avatar.status.value,
                "progress": avatar.training_progress,
                "created_at": avatar.created_at.isoformat() if avatar.created_at else None,
                "training_started_at": avatar.training_started_at.isoformat() if avatar.training_started_at else None,
                "training_completed_at": avatar.training_completed_at.isoformat() if avatar.training_completed_at else None,
                "finetune_id": avatar.finetune_id,
                "fal_request_id": avatar.fal_request_id,
            }
            
            # Добавляем время обучения если есть
            if avatar.training_started_at and avatar.training_completed_at:
                duration = avatar.training_completed_at - avatar.training_started_at
                progress_info["training_duration_seconds"] = duration.total_seconds()
            
            # Добавляем расширенную информацию для активного обучения
            if avatar.status.value == "training" and avatar.finetune_id:
                # Можем попробовать получить актуальный статус от FAL AI
                try:
                    fal_status = await self.fal_client.get_training_status(avatar.finetune_id)
                    progress_info["fal_status"] = fal_status
                except Exception as e:
                    logger.warning(f"[PROGRESS] Не удалось получить статус от FAL AI для {avatar_id}: {e}")
                    progress_info["fal_status"] = None
            
            # Добавляем информацию об ошибках если есть
            if avatar.avatar_data and "error_message" in avatar.avatar_data:
                progress_info["error_message"] = avatar.avatar_data["error_message"]
                progress_info["error_timestamp"] = avatar.avatar_data.get("error_timestamp")
            
            return progress_info
            
        except Exception as e:
            logger.exception(f"[PROGRESS] Ошибка получения прогресса {avatar_id}: {e}")
            raise
    
    async def find_avatar_by_finetune_id(self, finetune_id: str) -> Optional[UUID]:
        """
        Находит аватар по finetune_id
        
        Args:
            finetune_id: ID обучения FAL AI
            
        Returns:
            Optional[UUID]: ID аватара или None
        """
        query = select(Avatar.id).where(Avatar.finetune_id == finetune_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def find_avatar_by_request_id(self, request_id: str) -> Optional[Avatar]:
        """
        Находит аватар по fal_request_id
        
        Args:
            request_id: Request ID от FAL AI
            
        Returns:
            Optional[Avatar]: Аватар или None
        """
        query = select(Avatar).where(Avatar.fal_request_id == request_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_training_statistics(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Получает статистику обучения аватаров
        
        Args:
            user_id: ID пользователя (если None, то общая статистика)
            
        Returns:
            Dict[str, Any]: Статистика обучения
        """
        try:
            from sqlalchemy import func
            from app.database.models import AvatarStatus
            
            # Базовый запрос
            query = select(
                Avatar.status,
                func.count(Avatar.id).label('count')
            ).group_by(Avatar.status)
            
            # Фильтруем по пользователю если указан
            if user_id:
                query = query.where(Avatar.user_id == user_id)
            
            result = await self.session.execute(query)
            status_counts = {row.status.value: row.count for row in result}
            
            # Дополнительная статистика
            total_avatars = sum(status_counts.values())
            
            # Статистика времени обучения
            duration_query = select(
                func.avg(
                    func.extract('epoch', Avatar.training_completed_at - Avatar.training_started_at)
                ).label('avg_duration'),
                func.min(
                    func.extract('epoch', Avatar.training_completed_at - Avatar.training_started_at)
                ).label('min_duration'),
                func.max(
                    func.extract('epoch', Avatar.training_completed_at - Avatar.training_started_at)
                ).label('max_duration')
            ).where(
                Avatar.training_started_at.isnot(None),
                Avatar.training_completed_at.isnot(None),
                Avatar.status == AvatarStatus.COMPLETED
            )
            
            if user_id:
                duration_query = duration_query.where(Avatar.user_id == user_id)
            
            duration_result = await self.session.execute(duration_query)
            duration_stats = duration_result.first()
            
            statistics = {
                "total_avatars": total_avatars,
                "status_distribution": status_counts,
                "success_rate": (
                    status_counts.get("completed", 0) / total_avatars * 100 
                    if total_avatars > 0 else 0
                ),
                "training_duration": {
                    "average_seconds": duration_stats.avg_duration if duration_stats.avg_duration else 0,
                    "min_seconds": duration_stats.min_duration if duration_stats.min_duration else 0,
                    "max_seconds": duration_stats.max_duration if duration_stats.max_duration else 0,
                } if duration_stats else None
            }
            
            logger.info(f"[STATISTICS] Получена статистика обучения: {statistics}")
            return statistics
            
        except Exception as e:
            logger.exception(f"[STATISTICS] Ошибка получения статистики: {e}")
            raise
