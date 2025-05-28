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
from app.database.models import Avatar, AvatarStatus
from app.core.database import get_session

logger = get_logger(__name__)


class FALStatusChecker:
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
        
        # Запускаем в фоне
        asyncio.create_task(self._monitor_training_status(avatar_id, request_id, training_type))
    
    async def _monitor_training_status(self, avatar_id: UUID, request_id: str, training_type: str) -> None:
        """
        Мониторит статус обучения до завершения
        
        Args:
            avatar_id: ID аватара
            request_id: ID запроса в FAL AI
            training_type: Тип обучения (portrait/style)
        """
        start_time = datetime.utcnow()
        max_end_time = start_time + timedelta(seconds=self.max_check_duration)
        
        # Определяем endpoint для проверки статуса
        if training_type == "portrait":
            endpoint = "fal-ai/flux-lora-portrait-trainer"
        else:  # style
            endpoint = "fal-ai/flux-pro-trainer"
        
        status_url = f"https://queue.fal.run/{endpoint}/requests/{request_id}/status"
        
        # Даём время на инициализацию обучения (30 секунд)
        logger.info(f"🔍 Ожидание инициализации обучения для аватара {avatar_id}...")
        await asyncio.sleep(90)
        
        consecutive_not_training_checks = 0
        max_consecutive_checks = 3  # Максимум 3 проверки подряд с неправильным статусом
        
        while datetime.utcnow() < max_end_time:
            try:
                # Сначала проверяем статус в FAL AI
                status_data = await self._check_fal_status(status_url)
                
                if status_data:
                    fal_status = status_data.get("status")
                    logger.debug(f"🔍 FAL AI статус для {avatar_id}: {fal_status}")
                    
                    # Если FAL AI показывает что обучение активно, продолжаем мониторинг
                    if fal_status in ["IN_QUEUE", "IN_PROGRESS"]:
                        consecutive_not_training_checks = 0
                        await self._process_status_update(avatar_id, request_id, training_type, status_data)
                        
                    elif fal_status == "COMPLETED":
                        logger.info(f"🔍 Обучение завершено для аватара {avatar_id}")
                        await self._process_status_update(avatar_id, request_id, training_type, status_data)
                        return
                        
                    elif fal_status in ["FAILED", "CANCELLED"]:
                        logger.warning(f"🔍 Обучение прервано для аватара {avatar_id}: {fal_status}")
                        await self._process_status_update(avatar_id, request_id, training_type, status_data)
                        return
                
                # Проверяем статус аватара в БД только если FAL AI не отвечает
                if not status_data:
                    async with get_session() as session:
                        avatar = await session.get(Avatar, avatar_id)
                        if not avatar:
                            logger.warning(f"🔍 Аватар {avatar_id} не найден в БД")
                            return
                            
                        if avatar.status != AvatarStatus.TRAINING:
                            consecutive_not_training_checks += 1
                            logger.info(f"🔍 Аватар {avatar_id} не в статусе TRAINING ({consecutive_not_training_checks}/{max_consecutive_checks})")
                            
                            # Останавливаем только после нескольких проверок подряд
                            if consecutive_not_training_checks >= max_consecutive_checks:
                                logger.info(f"🔍 Останавливаем мониторинг для аватара {avatar_id} (статус: {avatar.status.value})")
                                return
                        else:
                            consecutive_not_training_checks = 0
                
                # Ждём до следующей проверки
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"🔍 Ошибка мониторинга статуса для аватара {avatar_id}: {e}")
                await asyncio.sleep(self.check_interval)
        
        logger.warning(f"🔍 Превышено время мониторинга для аватара {avatar_id}")
    
    async def _check_fal_status(self, status_url: str) -> Optional[Dict[str, Any]]:
        """
        Проверяет статус запроса в FAL AI
        
        Args:
            status_url: URL для проверки статуса
            
        Returns:
            Данные статуса или None при ошибке
        """
        headers = {
            "Authorization": f"Key {self.fal_api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(status_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"🔍 Статус FAL AI: {data}")
                        return data
                    else:
                        logger.warning(f"🔍 Ошибка запроса статуса FAL AI: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"🔍 Ошибка запроса к FAL AI: {e}")
            return None
    
    async def _process_status_update(self, avatar_id: UUID, request_id: str, training_type: str, status_data: Dict[str, Any]) -> None:
        """
        Обрабатывает обновление статуса от FAL AI
        
        Args:
            avatar_id: ID аватара
            request_id: ID запроса
            training_type: Тип обучения
            status_data: Данные статуса от FAL AI
        """
        fal_status = status_data.get("status")
        
        # Маппинг статусов FAL AI в наши статусы
        status_mapping = {
            "IN_QUEUE": AvatarStatus.TRAINING,
            "IN_PROGRESS": AvatarStatus.TRAINING,
            "COMPLETED": AvatarStatus.COMPLETED,
            "FAILED": AvatarStatus.ERROR,
            "CANCELLED": AvatarStatus.CANCELLED,
        }
        
        new_status = status_mapping.get(fal_status, AvatarStatus.TRAINING)
        
        logger.info(f"🔍 Обновление статуса аватара {avatar_id}: {fal_status} -> {new_status.value}")
        
        # Если обучение завершено, получаем результат
        if fal_status == "COMPLETED":
            await self._handle_training_completion(avatar_id, request_id, training_type, status_data)
        else:
            # Обновляем только статус
            await self._update_avatar_status(avatar_id, new_status)
    
    async def _handle_training_completion(self, avatar_id: UUID, request_id: str, training_type: str, status_data: Dict[str, Any]) -> None:
        """
        Обрабатывает завершение обучения
        
        Args:
            avatar_id: ID аватара
            request_id: ID запроса
            training_type: Тип обучения
            status_data: Данные статуса от FAL AI
        """
        try:
            # Получаем полный результат
            result_data = await self._get_training_result(request_id, training_type)
            
            if result_data:
                # Имитируем webhook данные для обработки
                webhook_data = {
                    "request_id": request_id,
                    "status": "completed",
                    "result": result_data.get("response", {})
                }
                
                # Используем существующий webhook обработчик с сессией
                async with get_session() as session:
                    from app.services.avatar.training_service.webhook_handler import WebhookHandler
                    webhook_handler = WebhookHandler(session)
                    
                    success = await webhook_handler.handle_webhook(webhook_data)
                    
                    if success:
                        logger.info(f"🔍 Обучение аватара {avatar_id} завершено через status checker")
                        
                        # Отправляем уведомление пользователю
                        try:
                            from app.services.avatar.notification_service import AvatarNotificationService
                            notification_service = AvatarNotificationService(session)
                            notification_sent = await notification_service.send_completion_notification_by_id(avatar_id)
                            
                            if notification_sent:
                                logger.info(f"🔍 ✅ Уведомление о завершении отправлено для аватара {avatar_id}")
                            else:
                                logger.warning(f"🔍 ⚠️ Не удалось отправить уведомление для аватара {avatar_id}")
                                
                        except Exception as notification_error:
                            logger.error(f"🔍 ❌ Ошибка отправки уведомления для аватара {avatar_id}: {notification_error}")
                        
                    else:
                        logger.error(f"🔍 Ошибка обработки webhook для аватара {avatar_id}")
                        await self._update_avatar_status(avatar_id, AvatarStatus.ERROR)
            else:
                logger.error(f"🔍 Не удалось получить результат обучения для аватара {avatar_id}")
                await self._update_avatar_status(avatar_id, AvatarStatus.ERROR)
                
        except Exception as e:
            logger.error(f"🔍 Ошибка обработки завершения обучения для аватара {avatar_id}: {e}")
            await self._update_avatar_status(avatar_id, AvatarStatus.ERROR)
    
    async def _get_training_result(self, request_id: str, training_type: str) -> Optional[Dict[str, Any]]:
        """
        Получает результат обучения от FAL AI
        
        Args:
            request_id: ID запроса
            training_type: Тип обучения
            
        Returns:
            Результат обучения или None при ошибке
        """
        # Определяем endpoint
        if training_type == "portrait":
            endpoint = "fal-ai/flux-lora-portrait-trainer"
        else:  # style
            endpoint = "fal-ai/flux-pro-trainer"
        
        result_url = f"https://queue.fal.run/{endpoint}/requests/{request_id}"
        
        headers = {
            "Authorization": f"Key {self.fal_api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(result_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"🔍 Получен результат обучения: {data}")
                        return data
                    else:
                        logger.warning(f"🔍 Ошибка получения результата: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"🔍 Ошибка запроса результата: {e}")
            return None
    
    async def _update_avatar_status(self, avatar_id: UUID, status: AvatarStatus) -> None:
        """
        Обновляет статус аватара в БД
        
        Args:
            avatar_id: ID аватара
            status: Новый статус
        """
        try:
            async with get_session() as session:
                avatar = await session.get(Avatar, avatar_id)
                if avatar:
                    avatar.status = status
                    if status == AvatarStatus.COMPLETED:
                        avatar.training_completed_at = datetime.utcnow()
                        avatar.training_progress = 100
                    
                    await session.commit()
                    logger.info(f"🔍 Статус аватара {avatar_id} обновлён на {status.value}")
                    
        except Exception as e:
            logger.error(f"🔍 Ошибка обновления статуса аватара {avatar_id}: {e}")


# Глобальный экземпляр
status_checker = FALStatusChecker() 