"""
Сервис управления обучением аватаров с FAL AI
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ...core.config import settings
from ...core.logger import get_logger
from ...database.models import Avatar, AvatarPhoto, AvatarStatus
from ..base import BaseService
from ..fal.client import FalAIClient

logger = get_logger(__name__)


class AvatarTrainingService(BaseService):
    """
    Сервис для управления обучением аватаров с интеграцией FAL AI.
    
    Основные функции:
    - Запуск обучения аватаров
    - Мониторинг прогресса
    - Обработка webhook от FAL AI
    - Управление состояниями обучения
    """

    def __init__(self, session: AsyncSession):
        super().__init__()
        self.session = session
        self.fal_client = FalAIClient()

    async def start_training(
        self, 
        avatar_id: UUID, 
        custom_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Запускает обучение аватара
        
        Args:
            avatar_id: ID аватара для обучения
            custom_config: Пользовательская конфигурация обучения
            
        Returns:
            bool: True если обучение запущено успешно
            
        Raises:
            ValueError: При ошибках валидации
            RuntimeError: При критических ошибках
        """
        try:
            # 1. Получаем аватар и проверяем готовность к обучению
            avatar = await self._get_avatar_for_training(avatar_id)
            
            # 2. Получаем фотографии аватара
            photo_urls = await self._get_avatar_photo_urls(avatar_id)
            
            if len(photo_urls) < settings.AVATAR_MIN_PHOTOS:
                raise ValueError(
                    f"Недостаточно фотографий для обучения: {len(photo_urls)}/{settings.AVATAR_MIN_PHOTOS}"
                )
            
            # 3. Обновляем статус аватара на "обучается"
            await self._update_avatar_status(
                avatar_id,
                AvatarStatus.TRAINING,
                progress=0,
                training_started_at=datetime.utcnow()
            )
            
            # 4. Запускаем обучение на FAL AI
            logger.info(f"[TRAINING] Запуск обучения аватара {avatar_id}")
            
            finetune_id = await self.fal_client.train_avatar(
                user_id=avatar.user_id,
                avatar_id=avatar_id,
                name=avatar.name,
                gender=avatar.gender.value,
                photo_urls=photo_urls,
                training_config=custom_config
            )
            
            if not finetune_id:
                # Откатываем статус при ошибке
                await self._update_avatar_status(
                    avatar_id,
                    AvatarStatus.ERROR,
                    error_message="Не удалось запустить обучение на FAL AI"
                )
                raise RuntimeError("FAL AI не смог запустить обучение")
            
            # 5. Сохраняем finetune_id и обновляем конфигурацию
            await self._save_training_info(avatar_id, finetune_id, custom_config)
            
            logger.info(
                f"[TRAINING] Обучение аватара {avatar_id} запущено успешно: "
                f"finetune_id={finetune_id}"
            )
            
            return True
            
        except Exception as e:
            logger.exception(f"[TRAINING] Ошибка запуска обучения аватара {avatar_id}: {e}")
            
            # Пытаемся откатить статус
            try:
                await self._update_avatar_status(
                    avatar_id,
                    AvatarStatus.ERROR,
                    error_message=str(e)
                )
            except Exception as rollback_error:
                logger.exception(f"[TRAINING] Ошибка отката статуса: {rollback_error}")
            
            raise

    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Обрабатывает webhook от FAL AI
        
        Args:
            webhook_data: Данные webhook от FAL AI
            
        Returns:
            bool: True если webhook обработан успешно
        """
        try:
            # Извлекаем информацию из webhook
            finetune_id = webhook_data.get("finetune_id")
            status = webhook_data.get("status")
            progress = webhook_data.get("progress", 0)
            message = webhook_data.get("message", "")
            
            if not finetune_id:
                logger.warning("[WEBHOOK] Получен webhook без finetune_id")
                return False
            
            logger.info(
                f"[WEBHOOK] Получен статус обучения: "
                f"finetune_id={finetune_id}, status={status}, progress={progress}"
            )
            
            # Находим аватар по finetune_id
            avatar_id = await self._find_avatar_by_finetune_id(finetune_id)
            
            if not avatar_id:
                logger.warning(f"[WEBHOOK] Аватар с finetune_id {finetune_id} не найден")
                return False
            
            # Обновляем статус аватара в зависимости от статуса FAL AI
            await self._process_training_status_update(
                avatar_id, status, progress, message
            )
            
            return True
            
        except Exception as e:
            logger.exception(f"[WEBHOOK] Ошибка обработки webhook: {e}")
            return False

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
            }
            
            # Добавляем время обучения если есть
            if avatar.training_started_at and avatar.training_completed_at:
                duration = avatar.training_completed_at - avatar.training_started_at
                progress_info["training_duration_seconds"] = duration.total_seconds()
            
            # Добавляем расширенную информацию для активного обучения
            if avatar.status == AvatarStatus.TRAINING and avatar.finetune_id:
                # Можем попробовать получить актуальный статус от FAL AI
                fal_status = await self.fal_client.get_training_status(avatar.finetune_id)
                progress_info["fal_status"] = fal_status
            
            return progress_info
            
        except Exception as e:
            logger.exception(f"[TRAINING] Ошибка получения прогресса {avatar_id}: {e}")
            raise

    async def cancel_training(self, avatar_id: UUID) -> bool:
        """
        Отменяет обучение аватара
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            bool: True если отмена прошла успешно
        """
        try:
            # Проверяем что аватар в процессе обучения
            query = select(Avatar).where(Avatar.id == avatar_id)
            result = await self.session.execute(query)
            avatar = result.scalar_one_or_none()
            
            if not avatar:
                raise ValueError(f"Аватар {avatar_id} не найден")
            
            if avatar.status not in [AvatarStatus.TRAINING, AvatarStatus.READY_FOR_TRAINING]:
                raise ValueError(f"Аватар {avatar_id} не в процессе обучения (статус: {avatar.status})")
            
            # TODO: Реализовать отмену обучения в FAL AI
            # В текущей версии FAL AI нет API для отмены, но мы можем обновить статус
            
            # Обновляем статус на отмененный
            await self._update_avatar_status(
                avatar_id,
                AvatarStatus.CANCELLED,
                progress=avatar.training_progress,
                error_message="Обучение отменено пользователем"
            )
            
            logger.info(f"[TRAINING] Обучение аватара {avatar_id} отменено")
            return True
            
        except Exception as e:
            logger.exception(f"[TRAINING] Ошибка отмены обучения {avatar_id}: {e}")
            raise

    async def _get_avatar_for_training(self, avatar_id: UUID) -> Avatar:
        """
        Получает аватар и проверяет готовность к обучению
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            Avatar: Аватар готовый к обучению
            
        Raises:
            ValueError: При ошибках валидации
        """
        query = select(Avatar).where(Avatar.id == avatar_id)
        result = await self.session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            raise ValueError(f"Аватар {avatar_id} не найден")
        
        # Проверяем статус
        if avatar.status not in [AvatarStatus.READY_FOR_TRAINING, AvatarStatus.PHOTOS_UPLOADING]:
            raise ValueError(f"Аватар {avatar_id} не готов к обучению (статус: {avatar.status})")
        
        # Проверяем что уже не обучается
        if avatar.finetune_id and avatar.status == AvatarStatus.TRAINING:
            raise ValueError(f"Аватар {avatar_id} уже обучается (finetune_id: {avatar.finetune_id})")
        
        return avatar

    async def _get_avatar_photo_urls(self, avatar_id: UUID) -> List[str]:
        """
        Получает URL фотографий аватара из MinIO
        
        Args:
            avatar_id: ID аватара
            
        Returns:
            List[str]: Список URL фотографий
        """
        query = (
            select(AvatarPhoto.minio_key)
            .where(AvatarPhoto.avatar_id == avatar_id)
            .order_by(AvatarPhoto.upload_order)
        )
        
        result = await self.session.execute(query)
        minio_keys = result.scalars().all()
        
        # Конвертируем MinIO ключи в полные URL
        # В нашем случае minio_key уже содержит полный путь к объекту
        photo_urls = [minio_key for minio_key in minio_keys]
        
        logger.info(f"[TRAINING] Найдено {len(photo_urls)} фотографий для аватара {avatar_id}")
        return photo_urls

    async def _update_avatar_status(
        self,
        avatar_id: UUID,
        status: AvatarStatus,
        progress: Optional[int] = None,
        training_started_at: Optional[datetime] = None,
        training_completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Обновляет статус аватара
        
        Args:
            avatar_id: ID аватара
            status: Новый статус
            progress: Прогресс обучения (0-100)
            training_started_at: Время начала обучения
            training_completed_at: Время завершения обучения
            error_message: Сообщение об ошибке
        """
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if progress is not None:
            update_data["training_progress"] = max(0, min(100, progress))
        
        if training_started_at:
            update_data["training_started_at"] = training_started_at
        
        if training_completed_at:
            update_data["training_completed_at"] = training_completed_at
        
        if error_message:
            # Сохраняем ошибку в avatar_data
            query = select(Avatar.avatar_data).where(Avatar.id == avatar_id)
            result = await self.session.execute(query)
            current_data = result.scalar() or {}
            current_data["error_message"] = error_message
            current_data["error_timestamp"] = datetime.utcnow().isoformat()
            update_data["avatar_data"] = current_data
        
        stmt = (
            update(Avatar)
            .where(Avatar.id == avatar_id)
            .values(**update_data)
        )
        
        await self.session.execute(stmt)
        await self.session.commit()

    async def _save_training_info(
        self,
        avatar_id: UUID,
        finetune_id: str,
        training_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Сохраняет информацию об обучении
        
        Args:
            avatar_id: ID аватара
            finetune_id: ID обучения FAL AI
            training_config: Конфигурация обучения
        """
        update_data = {
            "finetune_id": finetune_id,
            "updated_at": datetime.utcnow()
        }
        
        if training_config:
            update_data["training_config"] = training_config
        
        stmt = (
            update(Avatar)
            .where(Avatar.id == avatar_id)
            .values(**update_data)
        )
        
        await self.session.execute(stmt)
        await self.session.commit()

    async def _find_avatar_by_finetune_id(self, finetune_id: str) -> Optional[UUID]:
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

    async def _process_training_status_update(
        self,
        avatar_id: UUID,
        fal_status: str,
        progress: int,
        message: str
    ) -> None:
        """
        Обрабатывает обновление статуса обучения от FAL AI
        
        Args:
            avatar_id: ID аватара
            fal_status: Статус от FAL AI
            progress: Прогресс (0-100)
            message: Сообщение от FAL AI
        """
        # Маппинг статусов FAL AI в наши статусы
        status_mapping = {
            "queued": AvatarStatus.TRAINING,
            "in_progress": AvatarStatus.TRAINING,
            "completed": AvatarStatus.COMPLETED,
            "failed": AvatarStatus.ERROR,
            "cancelled": AvatarStatus.CANCELLED,
        }
        
        new_status = status_mapping.get(fal_status, AvatarStatus.TRAINING)
        
        # Дополнительные параметры в зависимости от статуса
        update_params = {
            "progress": progress,
        }
        
        if new_status == AvatarStatus.COMPLETED:
            update_params["training_completed_at"] = datetime.utcnow()
            update_params["progress"] = 100
        elif new_status == AvatarStatus.ERROR:
            update_params["error_message"] = message or "Ошибка обучения на FAL AI"
        
        await self._update_avatar_status(avatar_id, new_status, **update_params)
        
        logger.info(
            f"[WEBHOOK] Обновлен статус аватара {avatar_id}: "
            f"{fal_status} -> {new_status.value} (progress: {progress}%)"
        ) 