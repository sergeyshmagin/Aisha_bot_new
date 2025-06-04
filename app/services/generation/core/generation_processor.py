"""
Модуль обработки процесса генерации изображений
"""
import asyncio
from typing import List
from uuid import UUID

from app.core.logger import get_logger
from app.database.models.generation import ImageGeneration, GenerationStatus
from app.services.fal.generation_service import FALGenerationService
from app.services.generation.balance.balance_manager import BalanceManager
from app.services.generation.config.generation_config import GenerationConfig
from app.services.generation.storage.image_storage import ImageStorage

logger = get_logger(__name__)


class GenerationProcessor:
    """Обработчик процесса генерации"""
    
    def __init__(self):
        self.fal_service = FALGenerationService()
        self.balance_manager = BalanceManager()
        self.config_manager = GenerationConfig()
        self.storage = ImageStorage()
    
    async def start_generation_process(self, generation: ImageGeneration):
        """
        Запускает процесс генерации асинхронно
        
        Args:
            generation: Объект генерации
        """
        asyncio.create_task(self._process_generation(generation))
        logger.info(f"Запущена генерация {generation.id} для пользователя {generation.user_id}")
    
    async def _process_generation(self, generation: ImageGeneration):
        """
        Обрабатывает генерацию изображения
        
        Args:
            generation: Объект генерации
        """
        try:
            logger.info(f"[Generation Process] Начинаем обработку генерации {generation.id}")
            
            # Обновляем статус на "в процессе"
            generation.status = GenerationStatus.PROCESSING
            await self._update_generation(generation)
            
            # Получаем конфигурацию генерации
            config = self.config_manager.get_generation_config(
                generation.quality_preset,
                generation.aspect_ratio,
                generation.num_images
            )
            
            # Получаем аватар для генерации
            from app.services.generation.core.generation_manager import GenerationManager
            manager = GenerationManager()
            avatar = await manager.get_avatar(generation.avatar_id, generation.user_id)
            
            if not avatar:
                raise Exception(f"Аватар {generation.avatar_id} не найден")
            
            # Запускаем генерацию через FAL AI
            logger.info(f"[Generation Process] Отправляем запрос в FAL AI: {generation.final_prompt[:100]}...")
            
            image_url = await self.fal_service.generate_avatar_image(
                avatar=avatar,
                prompt=generation.final_prompt,
                generation_config=config
            )
            
            if not image_url:
                raise Exception("FAL AI вернул пустой результат")
            
            # Формируем результат в ожидаемом формате
            fal_result = {'images': [image_url]}
            
            # Сохраняем изображения в MinIO
            saved_urls = await self.storage.save_images_to_minio(generation, fal_result['images'])
            
            # Используем MinIO URL если удалось сохранить, иначе fallback к FAL URL
            result_urls = saved_urls if saved_urls else fal_result['images']
            
            # Обновляем генерацию с результатами
            generation.result_urls = result_urls
            generation.status = GenerationStatus.COMPLETED
            await self._update_generation(generation)
            
            logger.info(f"[Generation Process] ✅ Генерация {generation.id} завершена успешно")
            
            # Отправляем уведомление пользователю
            await self._notify_user(generation)
            
        except Exception as e:
            logger.exception(f"[Generation Process] ❌ Ошибка генерации {generation.id}: {e}")
            
            # Обновляем статус на ошибку
            generation.status = GenerationStatus.FAILED
            generation.error_message = str(e)
            await self._update_generation(generation)
            
            # Возвращаем баланс пользователю
            await self._refund_generation(generation)
            
            # Отправляем уведомление об ошибке
            await self._notify_error(generation)
    
    async def _update_generation(self, generation: ImageGeneration):
        """
        Обновляет генерацию в БД
        
        Args:
            generation: Объект генерации
        """
        from app.services.generation.core.generation_manager import GenerationManager
        manager = GenerationManager()
        await manager.update_generation(generation)
    
    async def _refund_generation(self, generation: ImageGeneration):
        """
        Возвращает баланс пользователю при ошибке генерации
        
        Args:
            generation: Объект генерации
        """
        try:
            cost = self.balance_manager.calculate_cost(generation.num_images)
            await self.balance_manager.refund_balance(generation.user_id, cost)
            logger.info(f"Возвращен баланс {cost} за неудачную генерацию {generation.id}")
        except Exception as e:
            logger.exception(f"Ошибка возврата баланса для генерации {generation.id}: {e}")
    
    async def _notify_user(self, generation: ImageGeneration):
        """
        Отправляет уведомление пользователю о завершении генерации
        
        Args:
            generation: Объект генерации
        """
        # TODO: Реализовать отправку уведомления через бота
        logger.info(f"Нужно отправить уведомление пользователю {generation.user_id} о завершении генерации {generation.id}")
    
    async def _notify_error(self, generation: ImageGeneration):
        """
        Отправляет уведомление об ошибке генерации
        
        Args:
            generation: Объект генерации
        """
        # TODO: Реализовать отправку уведомления об ошибке
        logger.info(f"Нужно отправить уведомление об ошибке пользователю {generation.user_id} для генерации {generation.id}") 