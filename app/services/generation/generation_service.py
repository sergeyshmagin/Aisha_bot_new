"""
Сервис генерации изображений с интеграцией баланса
"""
import asyncio
import time
from datetime import datetime
from typing import List, Optional
from uuid import UUID
import aiohttp
from pathlib import Path

from app.core.database import get_session
from app.core.logger import get_logger
from app.database.models import User, Avatar, UserBalance
from app.database.models.generation import (
    ImageGeneration, GenerationStatus, StyleTemplate
)
from app.services.fal.generation_service import FALGenerationService
from app.services.generation.style_service import StyleService
from app.services.generation.prompt_processing_service import PromptProcessingService

logger = get_logger(__name__)

# Константы
GENERATION_COST = 50.0  # Стоимость одной генерации в единицах баланса


class ImageGenerationService:
    """Сервис генерации изображений с контролем баланса"""
    
    def __init__(self):
        self.fal_service = FALGenerationService()
        self.style_service = StyleService()
        self.prompt_processor = PromptProcessingService()
        # Не создаем UserService здесь, будем получать через DI или создавать с сессией
    
    def _get_user_service(self):
        """Получает UserService с сессией"""
        from app.core.di import get_user_service
        return get_user_service()
    
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
        
        # Рассчитываем общую стоимость
        total_cost = GENERATION_COST * num_images
        
        # Проверяем баланс пользователя и списываем
        async with self._get_user_service() as user_service:
            user_balance = await user_service.get_user_balance(user_id)
            if user_balance < total_cost:
                raise ValueError(
                    f"Недостаточно баланса. Требуется: {total_cost}, доступно: {user_balance}"
                )
            
            # Списываем баланс
            remaining_balance = await user_service.remove_coins(user_id, total_cost)
            if remaining_balance is None:
                raise ValueError("Ошибка списания баланса")
            
            logger.info(f"Списано {total_cost} единиц баланса. Остаток: {remaining_balance}")
        
        # Получаем шаблон
        template = await self.style_service.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Шаблон {template_id} не найден")
        
        # Получаем аватар
        avatar = await self._get_avatar(avatar_id, user_id)
        if not avatar:
            raise ValueError(f"Аватар {avatar_id} не найден")
        
        # Создаем запись генерации
        generation = ImageGeneration(
            user_id=user_id,
            avatar_id=avatar_id,
            template_id=template_id,
            original_prompt=template.prompt,
            final_prompt=self._build_final_prompt(template.prompt, avatar),
            quality_preset=quality_preset,
            aspect_ratio=aspect_ratio,
            num_images=num_images,
            status=GenerationStatus.PENDING
        )
        
        # Сохраняем в БД
        await self._save_generation(generation)
        
        # Увеличиваем популярность шаблона
        await self.style_service.increment_template_popularity(template_id)
        
        # Запускаем генерацию асинхронно
        asyncio.create_task(self._process_generation(generation))
        
        logger.info(f"Запущена генерация {generation.id} для пользователя {user_id}")
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
        
        # Рассчитываем общую стоимость
        total_cost = GENERATION_COST * num_images
        
        # Проверяем баланс пользователя и списываем
        async with self._get_user_service() as user_service:
            user_balance = await user_service.get_user_balance(user_id)
            if user_balance < total_cost:
                raise ValueError(
                    f"Недостаточно баланса. Требуется: {total_cost}, доступно: {user_balance}"
                )
            
            # Списываем баланс
            remaining_balance = await user_service.remove_coins(user_id, total_cost)
            if remaining_balance is None:
                raise ValueError("Ошибка списания баланса")
            
            logger.info(f"Списано {total_cost} единиц баланса. Остаток: {remaining_balance}")
        
        # Получаем аватар
        avatar = await self._get_avatar(avatar_id, user_id)
        if not avatar:
            raise ValueError(f"Аватар {avatar_id} не найден")
        
        # Обрабатываем промпт через GPT
        avatar_type = avatar.training_type.value if avatar.training_type else "portrait"
        prompt_result = await self.prompt_processor.process_prompt(custom_prompt, avatar_type)
        
        processed_prompt = prompt_result["processed"]
        negative_prompt = prompt_result["negative_prompt"]
        logger.info(f"Промпт обработан: '{custom_prompt[:50]}...' → '{processed_prompt[:50]}...'")
        logger.info(f"Negative prompt создан: {len(negative_prompt)} символов")
        
        # Создаем запись генерации
        generation = ImageGeneration(
            user_id=user_id,
            avatar_id=avatar_id,
            template_id=None,
            original_prompt=custom_prompt,
            final_prompt=self._build_final_prompt(processed_prompt, avatar),
            quality_preset=quality_preset,
            aspect_ratio=aspect_ratio,
            num_images=num_images,
            status=GenerationStatus.PENDING
        )
        
        # Сохраняем результат обработки промпта в дополнительные данные
        if hasattr(generation, 'prompt_metadata'):
            generation.prompt_metadata = {
                'prompt_processing': {
                    'original_prompt': prompt_result["original"],
                    'processed_prompt': prompt_result["processed"],
                    'negative_prompt': prompt_result["negative_prompt"],
                    'translation_needed': prompt_result["translation_needed"],
                    'processor_available': self.prompt_processor.is_available()
                }
            }
        
        # Сохраняем в БД
        await self._save_generation(generation)
        
        # Запускаем генерацию асинхронно
        asyncio.create_task(self._process_generation(generation))
        
        logger.info(f"Запущена кастомная генерация {generation.id} для пользователя {user_id}")
        return generation
    
    async def get_user_generations(
        self, 
        user_id: UUID, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[ImageGeneration]:
        """
        Получает историю генераций пользователя
        
        Args:
            user_id: ID пользователя
            limit: Лимит записей
            offset: Смещение
            
        Returns:
            List[ImageGeneration]: Список генераций
        """
        try:
            async with get_session() as session:
                from sqlalchemy import select
                from sqlalchemy.orm import selectinload
                
                stmt = (
                    select(ImageGeneration)
                    .options(
                        selectinload(ImageGeneration.template),
                        selectinload(ImageGeneration.avatar)
                    )
                    .where(ImageGeneration.user_id == user_id)
                    .order_by(ImageGeneration.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
                
                result = await session.execute(stmt)
                generations = result.scalars().all()
                
                logger.info(f"Получено {len(generations)} генераций для пользователя {user_id}")
                return list(generations)
                
        except Exception as e:
            logger.exception(f"Ошибка получения генераций пользователя {user_id}: {e}")
            return []
    
    async def get_generation_by_id(self, generation_id: UUID) -> Optional[ImageGeneration]:
        """
        Получает генерацию по ID
        
        Args:
            generation_id: ID генерации
            
        Returns:
            Optional[ImageGeneration]: Генерация или None
        """
        try:
            async with get_session() as session:
                from sqlalchemy import select
                from sqlalchemy.orm import selectinload
                
                stmt = (
                    select(ImageGeneration)
                    .options(
                        selectinload(ImageGeneration.template),
                        selectinload(ImageGeneration.avatar)
                    )
                    .where(ImageGeneration.id == generation_id)
                )
                
                result = await session.execute(stmt)
                generation = result.scalar_one_or_none()
                
                return generation
                
        except Exception as e:
            logger.exception(f"Ошибка получения генерации {generation_id}: {e}")
            return None
    
    async def toggle_favorite(self, generation_id: UUID, user_id: UUID) -> bool:
        """
        Переключает статус избранного для генерации
        
        Args:
            generation_id: ID генерации
            user_id: ID пользователя
            
        Returns:
            bool: Новый статус избранного
        """
        try:
            async with get_session() as session:
                from sqlalchemy import select
                
                stmt = select(ImageGeneration).where(
                    ImageGeneration.id == generation_id,
                    ImageGeneration.user_id == user_id
                )
                
                result = await session.execute(stmt)
                generation = result.scalar_one_or_none()
                
                if generation:
                    generation.is_favorite = not generation.is_favorite
                    await session.commit()
                    
                    logger.info(f"Генерация {generation_id} {'добавлена в' if generation.is_favorite else 'удалена из'} избранное")
                    return generation.is_favorite
                
                return False
                
        except Exception as e:
            logger.exception(f"Ошибка переключения избранного для генерации {generation_id}: {e}")
            return False
    
    async def _get_avatar(self, avatar_id: UUID, user_id: UUID) -> Optional[Avatar]:
        """Получает аватар пользователя"""
        try:
            async with get_session() as session:
                from sqlalchemy import select, and_
                
                stmt = select(Avatar).where(
                    and_(
                        Avatar.id == avatar_id,
                        Avatar.user_id == user_id
                    )
                )
                
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.exception(f"Ошибка получения аватара {avatar_id}: {e}")
            return None
    
    def _build_final_prompt(self, original_prompt: str, avatar: Avatar) -> str:
        """
        Строит финальный промпт с триггерными словами аватара
        
        Args:
            original_prompt: Оригинальный промпт
            avatar: Аватар
            
        Returns:
            str: Финальный промпт
        """
        trigger_word = avatar.trigger_word or "TOK"
        
        # Добавляем триггерное слово в начало промпта
        final_prompt = f"{trigger_word}, {original_prompt}"
        
        # Добавляем информацию о поле
        if avatar.gender:
            gender_word = "woman" if avatar.gender.value == "female" else "man"
            final_prompt = f"{gender_word}, {final_prompt}"
        
        return final_prompt
    
    async def _save_generation(self, generation: ImageGeneration):
        """Сохраняет генерацию в БД"""
        try:
            async with get_session() as session:
                session.add(generation)
                await session.commit()
                await session.refresh(generation)
                
        except Exception as e:
            logger.exception(f"Ошибка сохранения генерации: {e}")
            raise
    
    async def _update_generation(self, generation: ImageGeneration):
        """Обновляет генерацию в БД"""
        try:
            async with get_session() as session:
                await session.merge(generation)
                await session.commit()
                
        except Exception as e:
            logger.exception(f"Ошибка обновления генерации {generation.id}: {e}")
            raise
    
    async def _process_generation(self, generation: ImageGeneration):
        """
        Обрабатывает генерацию изображения
        
        Args:
            generation: Объект генерации
        """
        try:
            # Обновляем статус
            generation.status = GenerationStatus.PROCESSING
            await self._update_generation(generation)
            
            # Получаем аватар
            avatar = await self._get_avatar(generation.avatar_id, generation.user_id)
            if not avatar:
                raise ValueError(f"Аватар {generation.avatar_id} не найден")
            
            # Проверяем готовность аватара к генерации
            if not self._is_avatar_ready_for_generation(avatar):
                error_msg = self._get_avatar_status_message(avatar)
                raise ValueError(error_msg)
            
            # Настройки генерации
            config = self._get_generation_config(
                generation.quality_preset,
                generation.aspect_ratio,
                generation.num_images
            )
            
            # Извлекаем negative prompt из метаданных если есть
            negative_prompt = None
            if hasattr(generation, 'prompt_metadata') and generation.prompt_metadata:
                negative_prompt = generation.prompt_metadata.get('prompt_processing', {}).get('negative_prompt')
            
            # Добавляем negative prompt в конфигурацию
            if negative_prompt:
                config['negative_prompt'] = negative_prompt
                logger.info(f"Добавлен negative prompt: {len(negative_prompt)} символов")
                logger.debug(f"Negative prompt: {negative_prompt[:100]}...")
            
            start_time = time.time()
            
            # Генерируем изображения
            if generation.num_images == 1:
                image_url = await self.fal_service.generate_avatar_image(
                    avatar=avatar,
                    prompt=generation.final_prompt,
                    generation_config=config
                )
                fal_urls = [image_url] if image_url else []
            else:
                prompts = [generation.final_prompt] * generation.num_images
                fal_urls = await self.fal_service.generate_multiple_images(
                    avatar=avatar,
                    prompts=prompts,
                    generation_config=config
                )
                fal_urls = [url for url in fal_urls if url]
            
            # КРИТИЧЕСКИ ВАЖНО: Сохраняем изображения в MinIO
            if fal_urls:
                saved_urls = await self._save_images_to_minio(generation, fal_urls)
                result_urls = saved_urls if saved_urls else fal_urls  # Fallback к FAL URLs
            else:
                result_urls = []
            
            generation_time = time.time() - start_time
            
            # Обновляем результат
            generation.status = GenerationStatus.COMPLETED
            generation.result_urls = result_urls
            generation.generation_time = generation_time
            generation.completed_at = datetime.utcnow()
            
            await self._update_generation(generation)
            
            # Отправляем уведомление пользователю
            await self._notify_user(generation)
            
            logger.info(f"Генерация {generation.id} завершена успешно за {generation_time:.1f}с")
            logger.info(f"Сохранено {len(result_urls)} изображений в MinIO")
            
        except Exception as e:
            logger.exception(f"Ошибка генерации {generation.id}: {e}")
            
            # В случае ошибки возвращаем баланс
            await self._refund_generation(generation)
            
            generation.status = GenerationStatus.FAILED
            generation.error_message = str(e)
            await self._update_generation(generation)
            
            # Уведомляем об ошибке
            await self._notify_error(generation)
    
    async def _refund_generation(self, generation: ImageGeneration):
        """
        Возвращает баланс за неудачную генерацию
        
        Args:
            generation: Объект генерации
        """
        try:
            refund_amount = GENERATION_COST * generation.num_images
            async with self._get_user_service() as user_service:
                await user_service.add_coins(generation.user_id, refund_amount)
            
            logger.info(f"Возвращено {refund_amount} единиц баланса за неудачную генерацию {generation.id}")
            
        except Exception as e:
            logger.exception(f"Ошибка возврата баланса за генерацию {generation.id}: {e}")
    
    def _get_generation_config(self, quality_preset: str, aspect_ratio: str, num_images: int) -> dict:
        """
        Получает конфигурацию генерации
        
        Args:
            quality_preset: Пресет качества
            aspect_ratio: Соотношение сторон
            num_images: Количество изображений
            
        Returns:
            dict: Конфигурация генерации
        """
        # Базовая конфигурация
        config = {
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "num_images": num_images,
            "enable_safety_checker": True,
            "output_format": "jpeg",
            "output_quality": 95
        }
        
        # Настройки качества
        quality_settings = {
            "fast": {
                "num_inference_steps": 20,
                "guidance_scale": 3.0
            },
            "balanced": {
                "num_inference_steps": 28,
                "guidance_scale": 3.5
            },
            "high": {
                "num_inference_steps": 35,
                "guidance_scale": 4.0
            },
            "ultra": {
                "num_inference_steps": 50,
                "guidance_scale": 4.5,
                "output_quality": 100
            }
        }
        
        if quality_preset in quality_settings:
            config.update(quality_settings[quality_preset])
        
        # Настройки соотношения сторон
        aspect_ratio_settings = {
            "1:1": {"width": 1024, "height": 1024},
            "3:4": {"width": 768, "height": 1024},
            "4:3": {"width": 1024, "height": 768},
            "16:9": {"width": 1344, "height": 768},
            "9:16": {"width": 768, "height": 1344}
        }
        
        if aspect_ratio in aspect_ratio_settings:
            config.update(aspect_ratio_settings[aspect_ratio])
        
        return config
    
    async def _notify_user(self, generation: ImageGeneration):
        """
        Отправляет уведомление пользователю о завершении генерации
        
        Args:
            generation: Объект генерации
        """
        # TODO: Реализовать отправку уведомления через бота
        pass
    
    async def _notify_error(self, generation: ImageGeneration):
        """
        Отправляет уведомление об ошибке генерации
        
        Args:
            generation: Объект генерации
        """
        # TODO: Реализовать отправку уведомления об ошибке
        pass
    
    def _is_avatar_ready_for_generation(self, avatar: Avatar) -> bool:
        """
        Проверяет готовность аватара к генерации
        
        Args:
            avatar: Аватар для проверки
            
        Returns:
            bool: True если аватар готов
        """
        from app.database.models import AvatarStatus
        return avatar.status == AvatarStatus.COMPLETED
    
    def _get_avatar_status_message(self, avatar: Avatar) -> str:
        """
        Возвращает понятное сообщение о статусе аватара
        
        Args:
            avatar: Аватар
            
        Returns:
            str: Сообщение об ошибке для пользователя
        """
        from app.database.models import AvatarStatus
        
        status_messages = {
            AvatarStatus.DRAFT: f"Аватар '{avatar.name}' еще не готов - находится в статусе черновика",
            AvatarStatus.PHOTOS_UPLOADING: f"Аватар '{avatar.name}' еще загружает фотографии",
            AvatarStatus.READY_FOR_TRAINING: f"Аватар '{avatar.name}' готов к обучению, но обучение еще не запущено",
            AvatarStatus.TRAINING: f"Аватар '{avatar.name}' в процессе обучения. Попробуйте позже",
            AvatarStatus.ERROR: f"При обучении аватара '{avatar.name}' произошла ошибка",
            AvatarStatus.CANCELLED: f"Обучение аватара '{avatar.name}' было отменено",
        }
        
        return status_messages.get(
            avatar.status, 
            f"Аватар '{avatar.name}' не готов к генерации (статус: {avatar.status})"
        )
    
    async def _save_images_to_minio(self, generation: ImageGeneration, fal_urls: List[str]) -> List[str]:
        """
        Сохраняет изображения из FAL AI в MinIO для постоянного хранения
        
        Args:
            generation: Объект генерации
            fal_urls: Список URL изображений из FAL AI
            
        Returns:
            List[str]: Список URL сохраненных изображений в MinIO
        """
        try:
            from app.services.storage.minio import MinioStorage
            storage = MinioStorage()
            saved_urls = []
            
            for i, fal_url in enumerate(fal_urls):
                try:
                    # Скачиваем изображение с FAL AI
                    async with aiohttp.ClientSession() as session:
                        async with session.get(fal_url) as response:
                            if response.status == 200:
                                image_data = await response.read()
                            else:
                                logger.warning(f"Ошибка скачивания изображения {fal_url}: {response.status}")
                                continue
                    
                    # Генерируем путь для сохранения в MinIO
                    date_str = datetime.now().strftime("%Y/%m/%d")
                    filename = f"{generation.id}_{i+1:02d}.jpg"
                    object_path = f"generated/{date_str}/{filename}"
                    
                    # Сохраняем в MinIO
                    bucket = "generated"  # Или settings.MINIO_BUCKETS.get("generated", "generated")
                    
                    # Загружаем файл
                    success = await storage.upload_file(
                        bucket=bucket,
                        object_name=object_path,
                        data=image_data,
                        content_type="image/jpeg"
                    )
                    
                    if success:
                        # Генерируем presigned URL для доступа
                        minio_url = await storage.generate_presigned_url(
                            bucket=bucket,
                            object_name=object_path,
                            expires=7*24*3600  # 7 дней
                        )
                        
                        if minio_url:
                            saved_urls.append(minio_url)
                            logger.info(f"Изображение {i+1} сохранено в MinIO: {object_path}")
                        else:
                            logger.warning(f"Не удалось получить URL для {object_path}")
                    else:
                        logger.warning(f"Не удалось загрузить изображение {i+1} в MinIO")
                        
                except Exception as e:
                    logger.exception(f"Ошибка сохранения изображения {i+1} в MinIO: {e}")
                    continue
            
            if saved_urls:
                logger.info(f"Успешно сохранено {len(saved_urls)}/{len(fal_urls)} изображений в MinIO")
            else:
                logger.warning("Не удалось сохранить ни одного изображения в MinIO")
                
            return saved_urls
            
        except Exception as e:
            logger.exception(f"Критическая ошибка сохранения в MinIO: {e}")
            return [] 