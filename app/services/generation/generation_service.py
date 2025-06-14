"""
🎯 Основной сервис генерации изображений
Рефакторенная версия с модульной архитектурой
"""
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

from app.core.logger import get_logger

from app.database.models import ImageGeneration, GenerationStatus
from .balance.balance_manager import BalanceManager
from .config.generation_config import GenerationConfig
from .storage.image_storage import ImageStorage
from .core.generation_manager import GenerationManager
from .core.generation_processor import GenerationProcessor
from .style_service import StyleService
from .prompt_processing_service import PromptProcessingService


logger = get_logger(__name__)

# Экспорт константы для обратной совместимости
from app.core.config import settings
# Константа теперь импортируется из constants.py
# GENERATION_COST = settings.IMAGE_GENERATION_COST  # Перенесено в constants.py

class ImageGenerationService:
    """
    Главный сервис генерации изображений
    Координирует работу всех модулей
    """
    
    def __init__(self):
        self.balance_manager = BalanceManager()
        self.generation_manager = GenerationManager()
        self.generation_processor = GenerationProcessor()
        self.storage = ImageStorage()
        self.style_service = StyleService()
        self.prompt_processor = PromptProcessingService()
    
    async def generate_from_template(
        self,
        user_id: UUID,
        avatar_id: UUID,
        template_id: str,
        quality_preset: str = "balanced",
        aspect_ratio: str = "1:1",
        num_images: int = 1
    ) -> ImageGeneration:
        """
        Генерирует изображение по шаблону с проверкой баланса
        
        Args:
            user_id: ID пользователя
            avatar_id: ID аватара
            template_id: ID шаблона стиля
            quality_preset: Качество генерации
            aspect_ratio: Соотношение сторон
            num_images: Количество изображений
            
        Returns:
            ImageGeneration: Объект генерации
            
        Raises:
            ValueError: Если недостаточно баланса или шаблон не найден
        """
        # Рассчитываем и списываем баланс
        total_cost = self.balance_manager.calculate_cost(num_images)
        await self.balance_manager.check_and_charge_balance(user_id, total_cost)
        
        # Получаем шаблон
        template = await self.style_service.get_template_by_id(template_id)
        if not template:
            # Возвращаем баланс при ошибке
            await self.balance_manager.refund_balance(user_id, total_cost)
            raise ValueError(f"Шаблон {template_id} не найден")
        
        # Получаем и проверяем аватар
        avatar = await self.generation_manager.get_avatar(avatar_id, user_id)
        if not avatar:
            await self.balance_manager.refund_balance(user_id, total_cost)
            raise ValueError(f"Аватар {avatar_id} не найден")
        
        if not self.generation_manager.is_avatar_ready_for_generation(avatar):
            await self.balance_manager.refund_balance(user_id, total_cost)
            error_msg = self.generation_manager.get_avatar_status_message(avatar)
            raise ValueError(error_msg)
        
        # Создаем запись генерации
        generation = ImageGeneration(
            user_id=user_id,
            avatar_id=avatar_id,
            template_id=template_id,
            original_prompt=template.prompt,
            final_prompt=self.generation_manager.build_final_prompt(template.prompt, avatar),
            quality_preset=quality_preset,
            aspect_ratio=aspect_ratio,
            num_images=num_images,
            status=GenerationStatus.PENDING
        )
        
        # Сохраняем в БД
        await self.generation_manager.save_generation(generation)
        
        # Увеличиваем популярность шаблона
        await self.style_service.increment_template_popularity(template_id)
        
        # Запускаем генерацию асинхронно
        await self.generation_processor.start_generation_process(generation)
        
        logger.info(f"Запущена генерация по шаблону {generation.id} для пользователя {user_id}")
        return generation
    
    async def generate_custom(
        self,
        user_id: UUID,
        avatar_id: UUID,
        custom_prompt: str,
        quality_preset: str = "balanced",
        aspect_ratio: str = "1:1",
        num_images: int = 1
    ) -> ImageGeneration:
        """
        Генерирует изображение по кастомному промпту с проверкой баланса
        
        Args:
            user_id: ID пользователя
            avatar_id: ID аватара
            custom_prompt: Кастомный промпт
            quality_preset: Качество генерации
            aspect_ratio: Соотношение сторон
            num_images: Количество изображений
            
        Returns:
            ImageGeneration: Объект генерации
            
        Raises:
            ValueError: Если недостаточно баланса
        """
        # Рассчитываем и списываем баланс
        total_cost = self.balance_manager.calculate_cost(num_images)
        await self.balance_manager.check_and_charge_balance(user_id, total_cost)
        
        # Получаем и проверяем аватар
        avatar = await self.generation_manager.get_avatar(avatar_id, user_id)
        if not avatar:
            await self.balance_manager.refund_balance(user_id, total_cost)
            raise ValueError(f"Аватар {avatar_id} не найден")
        
        if not self.generation_manager.is_avatar_ready_for_generation(avatar):
            await self.balance_manager.refund_balance(user_id, total_cost)
            error_msg = self.generation_manager.get_avatar_status_message(avatar)
            raise ValueError(error_msg)
        
        # Обрабатываем промпт через GPT
        avatar_type = avatar.training_type.value if avatar.training_type else "portrait"
        prompt_result = await self.prompt_processor.process_prompt(custom_prompt, avatar_type)
        
        processed_prompt = prompt_result["processed"]
        negative_prompt = prompt_result["negative_prompt"]
        logger.info(f"Промпт обработан: '{custom_prompt[:50]}...' → '{processed_prompt[:50]}...'")
        
        if negative_prompt:
            logger.info(f"Negative prompt создан: {len(negative_prompt)} символов")
        else:
            logger.info("Negative prompt встроен в основной промпт (FLUX Pro модель)")
        
        # Создаем запись генерации
        generation = ImageGeneration(
            user_id=user_id,
            avatar_id=avatar_id,
            template_id=None,
            original_prompt=custom_prompt,
            final_prompt=self.generation_manager.build_final_prompt(processed_prompt, avatar),
            quality_preset=quality_preset,
            aspect_ratio=aspect_ratio,
            num_images=num_images,
            status=GenerationStatus.PENDING
        )
        
        # Сохраняем в БД
        await self.generation_manager.save_generation(generation)
        
        # Запускаем генерацию асинхронно
        await self.generation_processor.start_generation_process(generation)
        
        logger.info(f"Запущена кастомная генерация {generation.id} для пользователя {user_id}")
        return generation
    
    # Методы делегирования к модулям
    async def get_user_generations(self, user_id: UUID, limit: int = 20, offset: int = 0) -> List[ImageGeneration]:
        """Получает генерации пользователя"""
        return await self.generation_manager.get_user_generations(user_id, limit, offset)
    
    async def get_generation_by_id(self, generation_id: UUID) -> Optional[ImageGeneration]:
        """Получает генерацию по ID"""
        return await self.generation_manager.get_generation_by_id(generation_id)
    
    async def get_generations_by_ids(self, generation_ids: List[UUID]) -> List[ImageGeneration]:
        """Получает генерации по списку ID"""
        return await self.generation_manager.get_generations_by_ids(generation_ids)
    
    async def delete_generation(self, generation_id: UUID) -> bool:
        """
        Удаляет генерацию
        
        Args:
            generation_id: ID генерации
            
        Returns:
            bool: True если успешно удалено
        """
        # Получаем генерацию для удаления файлов
        generation = await self.generation_manager.get_generation_by_id(generation_id)
        if not generation:
            return False
        
        # Удаляем изображения из MinIO если есть
        if generation.result_urls:
            await self.storage.delete_images_from_minio(generation.result_urls, generation_id)
        
        # Удаляем запись из БД
        return await self.generation_manager.delete_generation(generation_id)
    
    async def toggle_favorite(self, generation_id: UUID, user_id: UUID) -> bool:
        """Переключает статус избранного для генерации"""
        return await self.generation_manager.toggle_favorite(generation_id, user_id) 