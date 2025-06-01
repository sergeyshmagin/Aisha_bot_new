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
    
    async def update_finetune_id_if_needed(
        self, 
        avatar_id: UUID, 
        new_finetune_id: str,
        reason: str = "Updated via status_checker"
    ) -> bool:
        """
        Обновляет finetune_id аватара если требуется
        
        Args:
            avatar_id: ID аватара
            new_finetune_id: Новый корректный finetune_id
            reason: Причина обновления
            
        Returns:
            bool: Успешность обновления
        """
        try:
            async with get_session() as session:
                from app.services.avatar.finetune_updater_service import FinetuneUpdaterService
                
                updater = FinetuneUpdaterService(session)
                
                success = await updater.update_finetune_id_by_id(
                    avatar_id=avatar_id,
                    new_finetune_id=new_finetune_id,
                    reason=reason,
                    updated_by="fal_status_checker"
                )
                
                if success:
                    logger.info(f"🔄 ✅ finetune_id аватара {avatar_id} обновлен через status_checker")
                else:
                    logger.error(f"🔄 ❌ Не удалось обновить finetune_id аватара {avatar_id}")
                
                return success
                
        except Exception as e:
            logger.error(f"🔄 ❌ Ошибка обновления finetune_id для аватара {avatar_id}: {e}")
            return False
    
    async def check_and_fix_invalid_finetune_ids(self) -> Dict[str, Any]:
        """
        Проверяет и исправляет аватары с некорректными finetune_id
        
        Returns:
            Dict[str, Any]: Результат операции
        """
        logger.info("🔍 Проверка аватаров с некорректными finetune_id...")
        
        try:
            async with get_session() as session:
                from app.services.avatar.finetune_updater_service import FinetuneUpdaterService
                
                updater = FinetuneUpdaterService(session)
                
                # Находим аватары с некорректными finetune_id
                invalid_avatars = await updater.find_avatars_with_invalid_finetune_ids()
                
                result = {
                    "found_invalid": len(invalid_avatars),
                    "fixed": 0,
                    "errors": [],
                    "details": []
                }
                
                if not invalid_avatars:
                    logger.info("🔍 ✅ Все аватары имеют корректные finetune_id")
                    return result
                
                logger.warning(f"🔍 ⚠️ Найдено {len(invalid_avatars)} аватаров с некорректными finetune_id")
                
                # Для каждого аватара с некорректным finetune_id
                for avatar_info in invalid_avatars:
                    avatar_name = avatar_info["name"]
                    invalid_finetune_id = avatar_info["finetune_id"]
                    
                    logger.warning(f"🔍 ⚠️ Аватар {avatar_name} имеет некорректный finetune_id: {invalid_finetune_id}")
                    
                    # Добавляем в детали для отчета
                    result["details"].append({
                        "avatar_name": avatar_name,
                        "avatar_id": avatar_info["id"],
                        "invalid_finetune_id": invalid_finetune_id,
                        "status": avatar_info["status"],
                        "action": "requires_manual_update"
                    })
                
                # Здесь можно добавить автоматическое исправление если есть правила маппинга
                # Например, если у нас есть база данных соответствий старых и новых ID
                
                logger.info(f"🔍 📊 Результат проверки:")
                logger.info(f"   Найдено некорректных: {result['found_invalid']}")
                logger.info(f"   Исправлено автоматически: {result['fixed']}")
                logger.info(f"   Требует ручного вмешательства: {len(result['details'])}")
                
                return result
                
        except Exception as e:
            logger.error(f"🔍 ❌ Ошибка проверки некорректных finetune_id: {e}")
            return {"error": str(e)}
    
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
                    # 200 - статус получен, 202 - запрос принят и обрабатывается
                    if response.status in [200, 202]:
                        try:
                            data = await response.json()
                            logger.debug(f"🔍 Статус FAL AI (HTTP {response.status}): {data}")
                            return data
                        except Exception as json_error:
                            # Если 202 без JSON - это нормально, запрос ещё обрабатывается
                            if response.status == 202:
                                logger.debug(f"🔍 FAL AI обрабатывает запрос (HTTP 202)")
                                return {"status": "IN_PROGRESS", "message": "Request is being processed"}
                            else:
                                logger.warning(f"🔍 Ошибка парсинга JSON от FAL AI: {json_error}")
                                return None
                    else:
                        logger.warning(f"🔍 Ошибка запроса статуса FAL AI: HTTP {response.status}")
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
        Обрабатывает завершение обучения с использованием валидатора данных
        
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
                logger.info(f"🔍 Получен результат обучения для аватара {avatar_id}")
                logger.debug(f"🔍 Структура результата: {list(result_data.keys())}")
                
                # Используем валидатор данных для правильной обработки
                async with get_session() as session:
                    from app.services.avatar.training_data_validator import AvatarTrainingDataValidator
                    from app.database.models import Avatar
                    from sqlalchemy import select
                    
                    # Получаем аватар
                    query = select(Avatar).where(Avatar.id == avatar_id)
                    result = await session.execute(query)
                    avatar = result.scalar_one_or_none()
                    
                    if not avatar:
                        logger.error(f"🔍 Аватар {avatar_id} не найден в БД")
                        return
                    
                    # Инициализируем валидатор
                    data_validator = AvatarTrainingDataValidator(session)
                    
                    # Подготавливаем webhook данные для валидатора
                    webhook_result = {
                        "request_id": request_id,
                        "status": "completed",
                        "result": result_data,
                        "completed_at": datetime.utcnow().isoformat()
                    }
                    
                    # КРИТИЧЕСКИ ВАЖНО: Используем валидатор для обработки результата
                    logger.info(f"🔍 Применяем валидацию данных для аватара {avatar.name} ({avatar.training_type})")
                    
                    try:
                        # Валидатор автоматически извлечет правильные данные и применит строгие правила
                        update_data = await data_validator.validate_and_fix_training_completion(
                            avatar=avatar,
                            webhook_result=webhook_result
                        )
                        
                        # Применяем валидированные данные
                        from sqlalchemy import update as sql_update
                        stmt = sql_update(Avatar).where(Avatar.id == avatar_id).values(**update_data)
                        await session.execute(stmt)
                        await session.commit()
                        
                        logger.info(f"🔍 ✅ Аватар {avatar_id} обновлен через валидатор с корректными данными")
                        
                        # Отправляем уведомление пользователю
                        try:
                            from app.services.avatar.notification_service import AvatarNotificationService
                            notification_service = AvatarNotificationService(session)
                            notification_sent = await notification_service.send_completion_notification_by_id(avatar_id)
                            
                            if notification_sent:
                                logger.info(f"🔍 ✅ Уведомление отправлено для аватара {avatar_id} (через status_checker)")
                            else:
                                logger.warning(f"🔍 ⚠️ Не удалось отправить уведомление для аватара {avatar_id}")
                                
                        except Exception as notification_error:
                            logger.error(f"🔍 ❌ Ошибка отправки уведомления: {notification_error}")
                            
                    except Exception as validation_error:
                        logger.error(f"🔍 ❌ Ошибка валидации данных для аватара {avatar_id}: {validation_error}")
                        # Устанавливаем fallback при ошибке валидации
                        await self._set_completed_with_fallback(avatar_id, request_id, training_type)
                        
            else:
                logger.error(f"🔍 Не удалось получить результат обучения для аватара {avatar_id}")
                await self._set_completed_with_fallback(avatar_id, request_id, training_type)
                
        except Exception as e:
            logger.error(f"🔍 Ошибка обработки завершения обучения для аватара {avatar_id}: {e}")
            try:
                await self._set_completed_with_fallback(avatar_id, request_id, training_type)
            except Exception as fallback_error:
                logger.error(f"🔍 Критическая ошибка установки fallback для аватара {avatar_id}: {fallback_error}")
                await self._update_avatar_status(avatar_id, AvatarStatus.ERROR)
    
    async def _set_completed_with_fallback(self, avatar_id: UUID, request_id: str, training_type: str) -> None:
        """
        Устанавливает аватар как завершённый с fallback данными согласно правилам валидации
        
        Args:
            avatar_id: ID аватара
            request_id: ID запроса  
            training_type: Тип обучения
        """
        try:
            async with get_session() as session:
                from sqlalchemy import select, update
                
                query = select(Avatar).where(Avatar.id == avatar_id)
                result = await session.execute(query)
                avatar = result.scalar_one_or_none()
                
                if not avatar:
                    logger.error(f"🔍 Аватар {avatar_id} не найден для установки fallback")
                    return
                
                avatar_name = avatar.name.lower()
                
                # Применяем правила валидации для fallback данных
                update_data = {
                    "status": AvatarStatus.COMPLETED,
                    "training_progress": 100,
                    "training_completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                # СТРОГИЕ ПРАВИЛА: разные данные для разных типов аватаров
                if avatar.training_type == AvatarTrainingType.STYLE:
                    # Style аватары ДОЛЖНЫ иметь finetune_id и НЕ должны иметь LoRA
                    fallback_finetune_id = f"fallback-style-{avatar_name}-{avatar_id.hex[:8]}"
                    
                    update_data.update({
                        "finetune_id": fallback_finetune_id,
                        "trigger_word": avatar.trigger_word or "TOK",
                        "diffusers_lora_file_url": None,  # ПРИНУДИТЕЛЬНО очищаем для Style
                        "config_file_url": None
                    })
                    
                    logger.warning(f"🔍 ⚠️ Style аватар {avatar_id} установлен с fallback finetune_id: {fallback_finetune_id}")
                    
                else:  # Portrait
                    # Portrait аватары ДОЛЖНЫ иметь LoRA и НЕ должны иметь finetune_id
                    fallback_lora_url = f"https://emergency-fallback.com/lora/{avatar_name}.safetensors"
                    fallback_config_url = f"https://emergency-fallback.com/config/{avatar_name}_config.json"
                    
                    update_data.update({
                        "diffusers_lora_file_url": fallback_lora_url,
                        "config_file_url": fallback_config_url,
                        "trigger_phrase": avatar.trigger_phrase or "TOK",
                        "finetune_id": None  # ПРИНУДИТЕЛЬНО очищаем для Portrait
                    })
                    
                    logger.warning(f"🔍 ⚠️ Portrait аватар {avatar_id} установлен с fallback LoRA: {fallback_lora_url}")
                
                # Добавляем информацию о fallback в avatar_data
                avatar_data = avatar.avatar_data or {}
                avatar_data["fallback_history"] = avatar_data.get("fallback_history", [])
                avatar_data["fallback_history"].append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": "Status checker fallback - no valid training result",
                    "request_id": request_id,
                    "training_type": training_type,
                    "source": "status_checker"
                })
                update_data["avatar_data"] = avatar_data
                
                # Применяем обновления
                stmt = update(Avatar).where(Avatar.id == avatar_id).values(**update_data)
                await session.execute(stmt)
                await session.commit()
                
                logger.info(f"🔍 ✅ Fallback данные применены для аватара {avatar_id} согласно правилам валидации")
                
        except Exception as e:
            logger.error(f"🔍 Ошибка установки fallback для аватара {avatar_id}: {e}")
            raise
    
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
                    # 200 - результат получен, 202 - запрос принят и обрабатывается
                    if response.status in [200, 202]:
                        try:
                            data = await response.json()
                            logger.info(f"🔍 Получен результат обучения (HTTP {response.status}): {data}")
                            return data
                        except Exception as json_error:
                            # Если 202 без JSON - это нормально, запрос ещё обрабатывается
                            if response.status == 202:
                                logger.debug(f"🔍 FAL AI ещё обрабатывает запрос результата (HTTP 202)")
                                return None  # Результат ещё не готов
                            else:
                                logger.warning(f"🔍 Ошибка парсинга JSON результата от FAL AI: {json_error}")
                                return None
                    else:
                        logger.warning(f"🔍 Ошибка получения результата: HTTP {response.status}")
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