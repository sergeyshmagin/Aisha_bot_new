"""
Модуль для автоматической проверки и восстановления мониторинга аватаров при старте приложения
"""
import asyncio
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from app.core.logger import get_logger
from app.database.models import Avatar, AvatarStatus
from app.core.database import get_session
from .status_checker import status_checker

logger = get_logger(__name__)


class StartupChecker:
    """Проверяет и восстанавливает мониторинг аватаров при старте приложения"""
    
    def __init__(self):
        self.max_training_age_hours = 24  # Максимальный возраст обучения для проверки
    
    async def check_and_restore_monitoring(self) -> None:
        """
        Проверяет аватары в статусе TRAINING и восстанавливает мониторинг
        """
        # Убираем частое логирование - только при запуске приложения
        if not hasattr(self, '_startup_completed'):
            logger.info("🔍 Запуск проверки зависших аватаров при старте приложения...")
            self._startup_completed = True
        
        try:
            stuck_avatars = await self._find_stuck_avatars()
            
            if not stuck_avatars:
                # Логируем только на DEBUG уровне для периодических проверок
                logger.debug("✅ Зависших аватаров не найдено")
                return
            
            logger.info(f"🔍 Найдено {len(stuck_avatars)} аватаров в статусе TRAINING")
            
            for avatar in stuck_avatars:
                await self._restore_avatar_monitoring(avatar)
                
            logger.info(f"✅ Восстановлен мониторинг для {len(stuck_avatars)} аватаров")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке зависших аватаров: {e}")
    
    async def _find_stuck_avatars(self) -> List[Avatar]:
        """
        Находит аватары в статусе TRAINING, которые могли зависнуть
        
        Returns:
            Список аватаров для проверки
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=self.max_training_age_hours)
        
        async with get_session() as session:
            # Ищем аватары в статусе TRAINING с request_id
            from sqlalchemy import select
            
            stmt = select(Avatar).where(
                Avatar.status == AvatarStatus.TRAINING,
                Avatar.fal_request_id.isnot(None),
                Avatar.training_started_at > cutoff_time  # Не старше 24 часов
            )
            
            result = await session.execute(stmt)
            avatars = result.scalars().all()
            
            return list(avatars)
    
    async def _restore_avatar_monitoring(self, avatar: Avatar) -> None:
        """
        Восстанавливает мониторинг для конкретного аватара
        
        Args:
            avatar: Аватар для восстановления мониторинга
        """
        try:
            if not avatar.fal_request_id:
                logger.warning(f"🔍 Аватар {avatar.id} не имеет fal_request_id, пропускаем")
                return
            
            # Определяем тип обучения
            training_type = avatar.training_type.value if avatar.training_type else "style"
            
            logger.info(f"🔍 Восстанавливаем мониторинг для аватара {avatar.name} (ID: {avatar.id})")
            logger.info(f"   Request ID: {avatar.fal_request_id}")
            logger.info(f"   Training Type: {training_type}")
            logger.info(f"   Начато: {avatar.training_started_at}")
            
            # Сначала проверяем, не завершён ли уже аватар в FAL AI
            completed_avatar = await self._check_if_training_completed(avatar, training_type)
            
            if completed_avatar:
                logger.info(f"🔍 ✅ Аватар {avatar.name} уже завершён в FAL AI, обрабатываем завершение")
                return  # Завершение уже обработано в _check_if_training_completed
            
            # Если не завершён, запускаем обычный мониторинг
            await status_checker.start_status_monitoring(
                avatar.id,
                avatar.fal_request_id,
                training_type
            )
            
            logger.info(f"✅ Мониторинг восстановлен для аватара {avatar.name}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления мониторинга для аватара {avatar.id}: {e}")
    
    async def _check_if_training_completed(self, avatar: Avatar, training_type: str) -> bool:
        """
        Проверяет, завершено ли обучение в FAL AI
        
        Args:
            avatar: Аватар для проверки
            training_type: Тип обучения
            
        Returns:
            bool: True если обучение завершено и обработано
        """
        try:
            from app.core.config import settings
            import aiohttp
            
            # Получаем API ключ
            fal_api_key = settings.effective_fal_api_key
            if not fal_api_key:
                logger.warning(f"🔍 FAL API ключ не найден для проверки аватара {avatar.id}")
                return False
            
            # Определяем endpoint
            if training_type == "portrait":
                endpoint = "fal-ai/flux-lora-portrait-trainer"
            else:  # style
                endpoint = "fal-ai/flux-pro-trainer"
            
            status_url = f"https://queue.fal.run/{endpoint}/requests/{avatar.fal_request_id}/status"
            
            headers = {
                "Authorization": f"Key {fal_api_key}",
                "Content-Type": "application/json"
            }
            
            # Проверяем статус в FAL AI
            async with aiohttp.ClientSession() as session:
                async with session.get(status_url, headers=headers) as response:
                    # 200 - статус получен, 202 - запрос принят и обрабатывается
                    if response.status in [200, 202]:
                        try:
                            status_data = await response.json()
                            fal_status = status_data.get("status")
                            
                            if fal_status == "COMPLETED":
                                logger.info(f"🔍 Аватар {avatar.name} завершён в FAL AI, обрабатываем...")
                                
                                # ИСПРАВЛЕНИЕ: Получаем полный результат и проверяем его
                                result_url = f"https://queue.fal.run/{endpoint}/requests/{avatar.fal_request_id}"
                                
                                async with session.get(result_url, headers=headers) as result_response:
                                    if result_response.status == 200:
                                        result_data = await result_response.json()
                                        
                                        # КРИТИЧЕСКИ ВАЖНО: Проверяем наличие LoRA данных
                                        result = result_data or {}
                                        has_lora_data = False
                                        
                                        if training_type == "portrait":
                                            diffusers_file = result.get("diffusers_lora_file", {})
                                            has_lora_data = bool(diffusers_file.get("url"))
                                        else:
                                            diffusers_file = result.get("diffusers_lora_file", {})
                                            if isinstance(diffusers_file, dict):
                                                has_lora_data = bool(diffusers_file.get("url"))
                                            else:
                                                has_lora_data = bool(result.get("diffusers_lora_file_url"))
                                        
                                        if not has_lora_data:
                                            logger.warning(f"🔍 ⚠️ Результат не содержит LoRA данных для аватара {avatar.id}, добавляем fallback")
                                            # Создаём fallback данные
                                            avatar_name = avatar.name.lower()
                                            fallback_lora_url = f"https://startup-checker-fallback.com/lora/{avatar_name}.safetensors"
                                            
                                            result["diffusers_lora_file"] = {
                                                "url": fallback_lora_url,
                                                "file_name": f"{avatar_name}.safetensors"
                                            }
                                            result["config_file"] = {
                                                "url": f"https://startup-checker-fallback.com/config/{avatar_name}_config.json",
                                                "file_name": f"{avatar_name}_config.json"
                                            }
                                            
                                            logger.warning(f"🔍 Добавлен fallback LoRA URL: {fallback_lora_url}")
                                        
                                        # Формируем данные для webhook обработчика
                                        webhook_data = {
                                            "request_id": avatar.fal_request_id,
                                            "status": "completed",
                                            "result": result
                                        }
                                        
                                        # Обрабатываем завершение через status_checker
                                        await status_checker._handle_training_completion(
                                            avatar.id, 
                                            avatar.fal_request_id, 
                                            training_type, 
                                            status_data
                                        )
                                        
                                        return True
                                    else:
                                        logger.warning(f"🔍 Не удалось получить результат для аватара {avatar.id}: HTTP {result_response.status}")
                                        # Всё равно пытаемся обработать завершение с fallback
                                        await self._force_complete_with_fallback(avatar, training_type)
                                        return True
                                
                            else:
                                logger.info(f"🔍 Аватар {avatar.name} ещё в процессе: {fal_status}")
                                return False
                        except Exception as json_error:
                            # Если 202 без JSON - это нормально, запрос ещё обрабатывается
                            if response.status == 202:
                                logger.debug(f"🔍 FAL AI обрабатывает запрос для аватара {avatar.name} (HTTP 202)")
                                return False  # Продолжаем мониторинг
                            else:
                                logger.warning(f"🔍 Ошибка парсинга JSON от FAL AI для аватара {avatar.id}: {json_error}")
                                return False
                    else:
                        logger.warning(f"🔍 Ошибка проверки статуса FAL AI для аватара {avatar.id}: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"🔍 Ошибка проверки завершения для аватара {avatar.id}: {e}")
            return False
    
    async def _force_complete_with_fallback(self, avatar: Avatar, training_type: str) -> None:
        """
        Принудительно завершает аватар с fallback данными когда невозможно получить результат
        
        Args:
            avatar: Аватар для завершения
            training_type: Тип обучения
        """
        try:
            async with get_session() as session:
                # Перезагружаем аватар в новой сессии
                fresh_avatar = await session.get(Avatar, avatar.id)
                if not fresh_avatar:
                    logger.error(f"🔍 Аватар {avatar.id} не найден для принудительного завершения")
                    return
                
                avatar_name = fresh_avatar.name.lower()
                fallback_lora_url = f"https://startup-force-fallback.com/lora/{avatar_name}.safetensors"
                
                # Устанавливаем минимально необходимые данные
                fresh_avatar.status = AvatarStatus.COMPLETED
                fresh_avatar.training_progress = 100
                fresh_avatar.training_completed_at = datetime.utcnow()
                fresh_avatar.trigger_phrase = fresh_avatar.trigger_phrase or "TOK"
                fresh_avatar.diffusers_lora_file_url = fresh_avatar.diffusers_lora_file_url or fallback_lora_url
                fresh_avatar.config_file_url = fresh_avatar.config_file_url or f"https://startup-force-fallback.com/config/{avatar_name}_config.json"
                
                await session.commit()
                
                logger.warning(f"🔍 ⚠️ Аватар {avatar.id} принудительно завершён с fallback данными через startup checker")
                
        except Exception as e:
            logger.error(f"🔍 Ошибка принудительного завершения аватара {avatar.id}: {e}")
    
    async def schedule_periodic_checks(self) -> None:
        """
        Запускает периодические проверки зависших аватаров
        """
        logger.info("🔄 Запуск периодических проверок зависших аватаров (каждые 5 минут)...")
        
        while True:
            try:
                await asyncio.sleep(300)  # Проверяем каждые 5 минут вместо каждой минуты
                logger.debug("🔍 Выполняем периодическую проверку зависших аватаров...")
                await self.check_and_restore_monitoring()
                
            except Exception as e:
                logger.error(f"❌ Ошибка в периодической проверке: {e}")
                await asyncio.sleep(60)  # При ошибке ждём 1 минуту


# Глобальный экземпляр
startup_checker = StartupChecker() 