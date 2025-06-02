"""
Обработка webhook от FAL AI с валидацией данных
Выделено из app/services/avatar/training_service.py для соблюдения правила ≤500 строк
"""
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select

from app.database.models import Avatar, AvatarStatus, AvatarTrainingType
from .models import WebhookData
from .progress_tracker import ProgressTracker
from ..training_data_validator import AvatarTrainingDataValidator

logger = logging.getLogger(__name__)class WebhookHandler:
    """Обработка webhook от FAL AI"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.progress_tracker = ProgressTracker(session)
        self.data_validator = AvatarTrainingDataValidator(session)
    
    async def handle_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Обрабатывает webhook от FAL AI с валидацией данных
        
        Args:
            webhook_data: Данные webhook от FAL AI
            
        Returns:
            bool: True если webhook обработан успешно
        """
        try:
            # Парсим данные webhook
            webhook = WebhookData.from_dict(webhook_data)
            
            if not webhook.request_id:
                logger.warning("[WEBHOOK] Получен webhook без request_id")
                return False
            
            logger.info(
                f"[WEBHOOK] Получен статус обучения: "
                f"request_id={webhook.request_id}, status={webhook.status}, progress={webhook.progress}"
            )
            
            # Находим аватар по request_id
            avatar = await self.progress_tracker.find_avatar_by_request_id(webhook.request_id)
            
            if not avatar:
                logger.warning(f"[WEBHOOK] Аватар с request_id {webhook.request_id} не найден")
                return False
            
            # Обрабатываем результат в зависимости от статуса
            if webhook.status == "completed":
                await self._process_training_completion_with_validation(avatar, webhook)
            else:
                # Обновляем статус аватара для промежуточных состояний
                await self._process_training_status_update(avatar.id, webhook)
            
            return True
            
        except Exception as e:
            logger.exception(f"[WEBHOOK] Ошибка обработки webhook: {e}")
            return False
    
    async def _process_training_completion_with_validation(self, avatar: Avatar, webhook: WebhookData) -> None:
        """
        Обрабатывает завершение обучения аватара С ВАЛИДАЦИЕЙ ДАННЫХ
        
        Args:
            avatar: Аватар
            webhook: Данные webhook от FAL AI
        """
        try:
            logger.info(f"🔍 [WEBHOOK] Начинаем валидацию и обработку завершения обучения для аватара {avatar.id}")
            
            # ИСПОЛЬЗУЕМ ВАЛИДАТОР для обеспечения правильности данных
            update_data = await self.data_validator.validate_and_fix_training_completion(
                avatar=avatar,
                webhook_result=webhook.result or {}
            )
            
            # Дополняем данными из webhook
            update_data.update({
                "training_completed_at": datetime.utcnow(),
                "fal_response_data": webhook.result
            })
            
            logger.info(f"✅ [WEBHOOK] Валидированные данные для аватара {avatar.id}: {list(update_data.keys())}")
            
            # Обновляем аватар в БД
            stmt = (
                update(Avatar)
                .where(Avatar.id == avatar.id)
                .values(**update_data)
            )
            
            await self.session.execute(stmt)
            await self.session.commit()
            
            # Удаляем фотографии после успешного завершения обучения
            await self._cleanup_training_photos(avatar.id)
            
            # Отправляем уведомление пользователю
            try:
                from app.services.avatar.notification_service import AvatarNotificationService
                notification_service = AvatarNotificationService(self.session)
                notification_sent = await notification_service.send_completion_notification(avatar)
                
                if notification_sent:
                    logger.info(f"[WEBHOOK] ✅ Уведомление о завершении отправлено для аватара {avatar.id} (через webhook_handler)")
                else:
                    logger.warning(f"[WEBHOOK] ⚠️ Не удалось отправить уведомление для аватара {avatar.id} (через webhook_handler)")
                    
            except Exception as notification_error:
                logger.error(f"[WEBHOOK] ❌ Ошибка отправки уведомления для аватара {avatar.id} (через webhook_handler): {notification_error}")
            
            logger.info(f"[WEBHOOK] ✅ Обучение аватара {avatar.id} успешно завершено с валидацией данных!")
            
        except Exception as e:
            logger.exception(f"[WEBHOOK] Ошибка обработки завершения обучения {avatar.id}: {e}")
            # Откатываемся к ошибке
            await self._update_avatar_status(
                avatar.id,
                AvatarStatus.ERROR,
                error_message=f"Ошибка обработки результата: {str(e)}"
            )
    
    async def _process_training_status_update(self, avatar_id: UUID, webhook: WebhookData) -> None:
        """
        Обрабатывает обновление статуса обучения от FAL AI
        
        Args:
            avatar_id: ID аватара
            webhook: Данные webhook от FAL AI
        """
        # Маппинг статусов FAL AI в наши статусы
        status_mapping = {
            "queued": AvatarStatus.TRAINING,
            "in_progress": AvatarStatus.TRAINING,
            "failed": AvatarStatus.ERROR,
            "cancelled": AvatarStatus.CANCELLED,
        }
        
        new_status = status_mapping.get(webhook.status, AvatarStatus.TRAINING)
        
        # Дополнительные параметры в зависимости от статуса
        update_params = {
            "progress": webhook.progress,
        }
        
        if new_status == AvatarStatus.ERROR:
            update_params["error_message"] = webhook.message or "Ошибка обучения на FAL AI"
        
        await self._update_avatar_status(avatar_id, new_status, **update_params)
        
        logger.info(
            f"[WEBHOOK] Обновлен статус аватара {avatar_id}: "
            f"{webhook.status} -> {new_status.value} (progress: {webhook.progress}%)"
        )
    
    async def _cleanup_training_photos(self, avatar_id: UUID) -> None:
        """
        Удаляет фотографии аватара после успешного завершения обучения
        
        Args:
            avatar_id: ID аватара
        """
        try:
            from app.core.config import settings
            from app.database.models import AvatarPhoto
            from app.services.storage import StorageService
            from sqlalchemy import select
            
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
        progress: int = None,
        error_message: str = None
    ) -> None:
        """
        Обновляет статус аватара
        
        Args:
            avatar_id: ID аватара
            status: Новый статус
            progress: Прогресс обучения (0-100)
            error_message: Сообщение об ошибке
        """
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if progress is not None:
            update_data["training_progress"] = max(0, min(100, progress))
        
        if error_message:
            # Получаем текущие данные аватара
            query = select(Avatar.avatar_data).where(Avatar.id == avatar_id)
            result = await self.session.execute(query)
            current_data = result.scalar() or {}
            
            # Добавляем информацию об ошибке
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
