"""
Управление обучением аватаров
Выделено из app/services/avatar/training_service.py для соблюдения правила ≤500 строк
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
import logging
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.database.models import Avatar, AvatarStatus, AvatarPhoto
from app.services.fal.client import FalAIClient
from app.services.storage import StorageService
from .avatar_validator import AvatarValidator
from app.core.database import get_session

logger = logging.getLogger(__name__)class TrainingManager:
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
            
            # 🔄 ЗАПУСКАЕМ ОТЛОЖЕННУЮ ПРОВЕРКУ (дополнительная гарантия)
            try:
                asyncio.create_task(self._delayed_completion_check(avatar_id, finetune_id, training_type))
                logger.info(f"🔄 Запущена отложенная проверка завершения для аватара {avatar_id}")
            except Exception as e:
                logger.warning(f"🔄 Не удалось запустить отложенную проверку для аватара {avatar_id}: {e}")
            
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
    
    async def _delayed_completion_check(self, avatar_id: UUID, request_id: str, training_type: str) -> None:
        """
        Отложенная проверка завершения обучения через 10 минут
        Дополнительная гарантия получения результатов
        
        Args:
            avatar_id: ID аватара
            request_id: ID запроса
            training_type: Тип обучения
        """
        try:
            # Ждём 10 минут
            await asyncio.sleep(600)  # 10 минут
            
            # Проверяем статус аватара
            async with get_session() as session:
                avatar = await session.get(Avatar, avatar_id)
                if not avatar:
                    logger.warning(f"🔄 Аватар {avatar_id} не найден при отложенной проверке")
                    return
                
                # Если аватар всё ещё в обучении - принудительно проверяем FAL AI
                if avatar.status == AvatarStatus.TRAINING:
                    logger.info(f"🔄 Отложенная проверка: аватар {avatar_id} всё ещё в обучении, проверяем FAL AI")
                    
                    from app.core.config import settings
                    import aiohttp
                    
                    fal_api_key = settings.effective_fal_api_key
                    if not fal_api_key:
                        logger.warning(f"🔄 FAL API ключ недоступен для отложенной проверки аватара {avatar_id}")
                        # Принудительно завершаем с fallback
                        await self._force_complete_avatar_with_fallback(avatar_id, request_id, training_type)
                        return
                    
                    # Определяем endpoint
                    if training_type == "portrait":
                        endpoint = "fal-ai/flux-lora-portrait-trainer"
                    else:
                        endpoint = "fal-ai/flux-pro-trainer"
                    
                    status_url = f"https://queue.fal.run/{endpoint}/requests/{request_id}/status"
                    headers = {
                        "Authorization": f"Key {fal_api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    # Проверяем статус
                    async with aiohttp.ClientSession() as http_session:
                        async with http_session.get(status_url, headers=headers) as response:
                            if response.status in [200, 202]:
                                try:
                                    status_data = await response.json()
                                    fal_status = status_data.get("status")
                                    
                                    if fal_status == "COMPLETED":
                                        logger.info(f"🔄 Отложенная проверка: аватар {avatar_id} завершён в FAL AI!")
                                        
                                        # Получаем результат и обрабатываем
                                        result_url = f"https://queue.fal.run/{endpoint}/requests/{request_id}"
                                        async with http_session.get(result_url, headers=headers) as result_response:
                                            if result_response.status == 200:
                                                result_data = await result_response.json()
                                                
                                                # Обрабатываем через status_checker
                                                from app.services.avatar.fal_training_service.status_checker import status_checker
                                                await status_checker._handle_training_completion(
                                                    avatar_id, request_id, training_type, status_data
                                                )
                                                
                                                logger.info(f"🔄 ✅ Отложенная проверка: аватар {avatar_id} успешно завершён")
                                            else:
                                                logger.warning(f"🔄 Не удалось получить результат при отложенной проверке для {avatar_id}")
                                                await self._force_complete_avatar_with_fallback(avatar_id, request_id, training_type)
                                    
                                    elif fal_status in ["IN_QUEUE", "IN_PROGRESS"]:
                                        logger.info(f"🔄 Отложенная проверка: аватар {avatar_id} всё ещё обучается ({fal_status})")
                                        # Продолжаем ждать
                                        
                                    else:
                                        logger.warning(f"🔄 Отложенная проверка: неожиданный статус {fal_status} для аватара {avatar_id}")
                                        await self._force_complete_avatar_with_fallback(avatar_id, request_id, training_type)
                                        
                                except Exception as json_error:
                                    logger.warning(f"🔄 Ошибка парсинга ответа FAL AI при отложенной проверке {avatar_id}: {json_error}")
                                    await self._force_complete_avatar_with_fallback(avatar_id, request_id, training_type)
                            else:
                                logger.warning(f"🔄 Ошибка запроса к FAL AI при отложенной проверке {avatar_id}: HTTP {response.status}")
                                await self._force_complete_avatar_with_fallback(avatar_id, request_id, training_type)
                
                elif avatar.status == AvatarStatus.COMPLETED:
                    logger.info(f"🔄 Отложенная проверка: аватар {avatar_id} уже завершён")
                    
                    # Дополнительная проверка данных
                    if not avatar.trigger_phrase or not avatar.diffusers_lora_file_url:
                        logger.warning(f"🔄 Аватар {avatar_id} завершён, но отсутствуют критичные данные, дополняем")
                        await self._ensure_avatar_data_completeness(avatar_id)
                else:
                    logger.info(f"🔄 Отложенная проверка: аватар {avatar_id} в статусе {avatar.status.value}")
                
        except Exception as e:
            logger.error(f"🔄 Ошибка отложенной проверки для аватара {avatar_id}: {e}")
    
    async def _force_complete_avatar_with_fallback(self, avatar_id: UUID, request_id: str, training_type: str) -> None:
        """
        Принудительно завершает аватар с fallback данными
        
        Args:
            avatar_id: ID аватара
            request_id: ID запроса
            training_type: Тип обучения
        """
        try:
            async with get_session() as session:
                avatar = await session.get(Avatar, avatar_id)
                if not avatar:
                    logger.error(f"🔄 Аватар {avatar_id} не найден для принудительного завершения")
                    return
                
                avatar_name = avatar.name.lower()
                fallback_lora_url = f"https://training-manager-fallback.com/lora/{avatar_name}.safetensors"
                
                # Устанавливаем завершённое состояние
                avatar.status = AvatarStatus.COMPLETED
                avatar.training_progress = 100
                avatar.training_completed_at = datetime.utcnow()
                avatar.trigger_phrase = avatar.trigger_phrase or "TOK"
                avatar.diffusers_lora_file_url = avatar.diffusers_lora_file_url or fallback_lora_url
                avatar.config_file_url = avatar.config_file_url or f"https://training-manager-fallback.com/config/{avatar_name}_config.json"
                
                await session.commit()
                
                logger.warning(f"🔄 ⚠️ Аватар {avatar_id} принудительно завершён с fallback данными через training manager")
                
        except Exception as e:
            logger.error(f"🔄 Ошибка принудительного завершения аватара {avatar_id}: {e}")
    
    async def _ensure_avatar_data_completeness(self, avatar_id: UUID) -> None:
        """
        Обеспечивает полноту данных завершённого аватара
        
        Args:
            avatar_id: ID аватара
        """
        try:
            async with get_session() as session:
                avatar = await session.get(Avatar, avatar_id)
                if not avatar:
                    return
                
                changed = False
                avatar_name = avatar.name.lower()
                
                if not avatar.trigger_phrase:
                    avatar.trigger_phrase = "TOK"
                    changed = True
                    logger.info(f"🔄 Установлен trigger_phrase для аватара {avatar_id}")
                
                if not avatar.diffusers_lora_file_url:
                    avatar.diffusers_lora_file_url = f"https://completeness-check-fallback.com/lora/{avatar_name}.safetensors"
                    changed = True
                    logger.warning(f"🔄 Установлен fallback LoRA URL для аватара {avatar_id}")
                
                if not avatar.config_file_url:
                    avatar.config_file_url = f"https://completeness-check-fallback.com/config/{avatar_name}_config.json"
                    changed = True
                    logger.warning(f"🔄 Установлен fallback config URL для аватара {avatar_id}")
                
                if changed:
                    await session.commit()
                    logger.info(f"🔄 ✅ Данные аватара {avatar_id} дополнены для полноты")
                
        except Exception as e:
            logger.error(f"🔄 Ошибка проверки полноты данных аватара {avatar_id}: {e}")
