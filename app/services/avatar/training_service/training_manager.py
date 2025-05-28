"""
Управление обучением аватаров
Выделено из app/services/avatar/training_service.py для соблюдения правила ≤500 строк
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.database.models import Avatar, AvatarStatus, AvatarPhoto
from app.services.fal.client import FalAIClient
from app.services.storage import StorageService
from .avatar_validator import AvatarValidator

logger = logging.getLogger(__name__)


class TrainingManager:
    """Управление запуском и отменой обучения аватаров"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.fal_client = FalAIClient()
        self.validator = AvatarValidator(session)
    
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
            avatar = await self.validator.get_avatar_for_training(avatar_id)
            
            # 2. Получаем фотографии аватара
            photo_urls = await self.validator.get_avatar_photo_urls(avatar_id)
            
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
            
            # 5. Сохраняем request_id и обновляем конфигурацию
            await self._save_training_info(avatar_id, finetune_id, custom_config)
            
            # 🔍 ЗАПУСКАЕМ МОНИТОРИНГ СТАТУСА как резервный механизм
            try:
                from app.services.avatar.fal_training_service.status_checker import status_checker
                await status_checker.start_status_monitoring(avatar_id, finetune_id, training_type)
                logger.info(f"🔍 Запущен мониторинг статуса для аватара {avatar_id}, request_id: {finetune_id}")
            except Exception as e:
                logger.warning(f"🔍 Не удалось запустить мониторинг статуса для аватара {avatar_id}: {e}")
                # Не прерываем процесс - это не критическая ошибка
            
            logger.info(
                f"[TRAINING] Обучение аватара {avatar_id} запущено успешно: "
                f"request_id={finetune_id}"
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
    
    async def cleanup_training_photos(self, avatar_id: UUID) -> None:
        """
        Удаляет фотографии аватара после успешного завершения обучения
        
        Args:
            avatar_id: ID аватара
        """
        try:
            # Проверяем настройку - нужно ли удалять фото после обучения
            if not getattr(settings, 'DELETE_PHOTOS_AFTER_TRAINING', True):
                logger.info(f"[CLEANUP] Удаление фото после обучения отключено для аватара {avatar_id}")
                return
            
            # Получаем все фотографии аватара
            query = (
                select(AvatarPhoto)
                .where(AvatarPhoto.avatar_id == avatar_id)
                .order_by(AvatarPhoto.upload_order)
            )
            result = await self.session.execute(query)
            photos = result.scalars().all()
            
            if not photos:
                logger.info(f"[CLEANUP] Нет фотографий для удаления у аватара {avatar_id}")
                return
            
            # Удаляем фотографии из MinIO
            storage = StorageService()
            
            # Проверяем настройку - оставлять ли первое фото как превью
            keep_preview = getattr(settings, 'KEEP_PREVIEW_PHOTO', True)
            
            deleted_count = 0
            for i, photo in enumerate(photos):
                # Пропускаем первое фото если нужно оставить превью
                if i == 0 and keep_preview:
                    logger.debug(f"[CLEANUP] Оставляем первое фото {photo.id} как превью")
                    continue
                
                try:
                    # Удаляем файл из MinIO
                    await storage.delete_file("avatars", photo.minio_key)
                    
                    # Удаляем запись из БД
                    await self.session.delete(photo)
                    deleted_count += 1
                    
                    logger.debug(f"[CLEANUP] Удалено фото {photo.id} (ключ: {photo.minio_key})")
                    
                except Exception as e:
                    logger.warning(f"[CLEANUP] Не удалось удалить фото {photo.id}: {e}")
            
            # Сохраняем изменения в БД
            await self.session.commit()
            
            # Формируем сообщение о результатах очистки
            total_photos = len(photos)
            kept_count = total_photos - deleted_count
            
            if keep_preview and total_photos > 0:
                logger.info(
                    f"[CLEANUP] Удалено {deleted_count}/{total_photos} фотографий "
                    f"после завершения обучения аватара {avatar_id} "
                    f"(оставлено {kept_count} для превью)"
                )
            else:
                logger.info(
                    f"[CLEANUP] Удалено {deleted_count}/{total_photos} фотографий "
                    f"после завершения обучения аватара {avatar_id}"
                )
            
        except Exception as e:
            await self.session.rollback()
            logger.exception(f"[CLEANUP] Ошибка при удалении фотографий аватара {avatar_id}: {e}")
            # Не прерываем процесс - это не критическая ошибка
    
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
        request_id: str,
        training_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Сохраняет информацию об обучении
        
        Args:
            avatar_id: ID аватара
            request_id: Request ID от FAL AI для отслеживания
            training_config: Конфигурация обучения
        """
        update_data = {
            "fal_request_id": request_id,  # Сохраняем только request_id
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