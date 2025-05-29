"""
Сервис генерации изображений с FAL AI
"""
import asyncio
from typing import Dict, List, Optional, Any
from uuid import UUID

import fal_client

from ...core.config import settings
from ...core.logger import get_logger
from ...database.models import Avatar, AvatarTrainingType

logger = get_logger(__name__)


class FALGenerationService:
    """
    Сервис для генерации изображений с обученными моделями FAL AI.
    
    Поддерживает:
    - Портретные аватары (LoRA файлы)
    - Стилевые аватары (finetune_id)
    - Тестовый режим
    """

    def __init__(self):
        self.api_key = settings.FAL_API_KEY
        self.test_mode = settings.AVATAR_TEST_MODE
        
        # Настраиваем FAL клиент
        if self.api_key:
            fal_client.api_key = self.api_key
        else:
            logger.debug("FAL_API_KEY не установлен, работа в тестовом режиме")

    async def generate_avatar_image(
        self,
        avatar: Avatar,
        prompt: str,
        generation_config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Генерирует изображение с обученным аватаром
        
        Args:
            avatar: Модель аватара с данными обучения
            prompt: Промпт для генерации
            generation_config: Дополнительные параметры генерации
            
        Returns:
            Optional[str]: URL сгенерированного изображения
            
        Raises:
            ValueError: При отсутствии обученной модели
            RuntimeError: При ошибках генерации
        """
        try:
            if self.test_mode:
                logger.info(f"[FAL TEST MODE] Симуляция генерации для аватара {avatar.id}")
                return await self._simulate_generation(avatar, prompt)
            
            # Проверяем что аватар обучен
            if not self._is_avatar_trained(avatar):
                raise ValueError(f"Аватар {avatar.id} не обучен или обучение не завершено")
            
            # Выбираем метод генерации в зависимости от типа аватара
            if avatar.training_type == AvatarTrainingType.PORTRAIT:
                return await self._generate_with_lora(avatar, prompt, generation_config)
            else:
                return await self._generate_with_finetune(avatar, prompt, generation_config)
                
        except Exception as e:
            logger.exception(f"[FAL AI] Ошибка генерации изображения для аватара {avatar.id}: {e}")
            raise

    async def _generate_with_lora(
        self,
        avatar: Avatar,
        prompt: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Генерация с LoRA файлом (для портретных аватаров)
        
        Args:
            avatar: Портретный аватар с LoRA файлом
            prompt: Промпт для генерации
            config: Дополнительные параметры
            
        Returns:
            Optional[str]: URL сгенерированного изображения
        """
        if not avatar.diffusers_lora_file_url:
            raise ValueError(f"LoRA файл не найден для аватара {avatar.id}")
        
        # Формируем промпт с триггерной фразой
        full_prompt = self._build_prompt_with_trigger(prompt, avatar.trigger_phrase)
        
        # Настройки генерации по умолчанию для LoRA
        generation_args = {
            "prompt": full_prompt,
            "lora_url": avatar.diffusers_lora_file_url,
            "lora_scale": config.get("lora_scale", 1.0) if config else 1.0,
            "num_images": config.get("num_images", 1) if config else 1,
            "image_size": config.get("image_size", "square_hd") if config else "square_hd",
            "num_inference_steps": config.get("num_inference_steps", 28) if config else 28,
            "guidance_scale": config.get("guidance_scale", 3.5) if config else 3.5,
            "enable_safety_checker": config.get("enable_safety_checker", True) if config else True,
        }
        
        logger.info(f"[FAL AI] Генерация с LoRA для аватара {avatar.id}: {generation_args}")
        
        # Запускаем генерацию
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: fal_client.subscribe(
                "fal-ai/flux-lora",
                arguments=generation_args
            )
        )
        
        # Извлекаем URL изображения
        images = result.get("images", [])
        if images and len(images) > 0:
            image_url = images[0].get("url")
            logger.info(f"[FAL AI] LoRA генерация завершена: {image_url}")
            return image_url
        
        logger.warning(f"[FAL AI] Не получено изображений в результате LoRA генерации")
        return None

    async def _generate_with_finetune(
        self,
        avatar: Avatar,
        prompt: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Генерация с finetune_id (для художественных аватаров)
        
        Args:
            avatar: Художественный аватар с finetune_id
            prompt: Промпт для генерации
            config: Дополнительные параметры
            
        Returns:
            Optional[str]: URL сгенерированного изображения
        """
        if not avatar.finetune_id:
            raise ValueError(f"Finetune ID не найден для аватара {avatar.id}")
        
        # Проверяем, нужно ли использовать Ultra модель
        use_ultra = config and config.get("use_ultra", False) if config else False
        
        if use_ultra:
            return await self._generate_with_finetune_ultra(avatar, prompt, config)
        else:
            return await self._generate_with_finetune_standard(avatar, prompt, config)

    async def _generate_with_finetune_standard(
        self,
        avatar: Avatar,
        prompt: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Генерация с стандартной FLUX.1 [pro] finetuned моделью
        """
        # Формируем промпт с триггерным словом
        full_prompt = self._build_prompt_with_trigger(prompt, avatar.trigger_word)
        
        # Настройки генерации по умолчанию для finetune
        generation_args = {
            "prompt": full_prompt,
            "finetune_id": avatar.finetune_id,  # ИСПРАВЛЕНО: используем finetune_id вместо model
            "finetune_strength": config.get("finetune_strength", 1.0) if config else 1.0,
            "num_images": config.get("num_images", 1) if config else 1,
            "image_size": config.get("image_size", "square_hd") if config else "square_hd",
            "num_inference_steps": config.get("num_inference_steps", 28) if config else 28,
            "guidance_scale": config.get("guidance_scale", 3.5) if config else 3.5,
            "safety_tolerance": config.get("safety_tolerance", "2") if config else "2",
            "output_format": config.get("output_format", "jpeg") if config else "jpeg",
        }
        
        logger.info(f"[FAL AI] Генерация с finetune для аватара {avatar.id}: {generation_args}")
        
        # Запускаем генерацию с правильным endpoint
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: fal_client.subscribe(
                "fal-ai/flux-pro/finetuned",  # ИСПРАВЛЕНО: правильный endpoint
                arguments=generation_args
            )
        )
        
        # Извлекаем URL изображения
        images = result.get("images", [])
        if images and len(images) > 0:
            image_url = images[0].get("url")
            logger.info(f"[FAL AI] Finetune генерация завершена: {image_url}")
            return image_url
        
        logger.warning(f"[FAL AI] Не получено изображений в результате finetune генерации")
        return None

    async def _generate_with_finetune_ultra(
        self,
        avatar: Avatar,
        prompt: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Генерация с FLUX.1 [pro] v1.1-ultra-finetuned моделью
        
        Args:
            avatar: Художественный аватар с finetune_id
            prompt: Промпт для генерации
            config: Дополнительные параметры
            
        Returns:
            Optional[str]: URL сгенерированного изображения
        """
        # Формируем промпт с триггерным словом
        full_prompt = self._build_prompt_with_trigger(prompt, avatar.trigger_word)
        
        # Настройки для Ultra модели
        generation_args = {
            "prompt": full_prompt,
            "finetune_id": avatar.finetune_id,
            "finetune_strength": config.get("finetune_strength", 1.1) if config else 1.1,
            "aspect_ratio": config.get("aspect_ratio", "1:1") if config else "1:1",
            "num_images": config.get("num_images", 1) if config else 1,
            "output_format": config.get("output_format", "jpeg") if config else "jpeg",
            "enable_safety_checker": config.get("enable_safety_checker", True) if config else True,
            "raw": config.get("raw", False) if config else False,
        }
        
        logger.info(f"[FAL AI] Ultra генерация для аватара {avatar.id}: {generation_args}")
        
        # Запускаем генерацию с Ultra endpoint
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: fal_client.subscribe(
                "fal-ai/flux-pro/v1.1-ultra-finetuned",
                arguments=generation_args
            )
        )
        
        # Извлекаем URL изображения
        images = result.get("images", [])
        if images and len(images) > 0:
            image_url = images[0].get("url")
            logger.info(f"[FAL AI] Ultra генерация завершена: {image_url}")
            return image_url
        
        logger.warning(f"[FAL AI] Не получено изображений в результате Ultra генерации")
        return None

    async def _simulate_generation(
        self,
        avatar: Avatar,
        prompt: str
    ) -> str:
        """
        Симуляция генерации для тестового режима
        
        Args:
            avatar: Аватар
            prompt: Промпт
            
        Returns:
            str: Тестовый URL изображения
        """
        # Имитируем задержку генерации
        await asyncio.sleep(2)
        
        # Возвращаем тестовый URL с параметрами
        test_url = (
            f"https://picsum.photos/1024/1024?random={avatar.id}&"
            f"type={avatar.training_type.value}&prompt={hash(prompt) % 1000}"
        )
        
        logger.info(f"🧪 [FAL TEST MODE] Симуляция генерации завершена: {test_url}")
        return test_url

    def _is_avatar_trained(self, avatar: Avatar) -> bool:
        """
        Проверяет что аватар обучен и готов к генерации
        
        Args:
            avatar: Аватар для проверки
            
        Returns:
            bool: True если аватар готов к генерации
        """
        from ...database.models import AvatarStatus
        
        # Проверяем статус
        if avatar.status != AvatarStatus.COMPLETED:
            return False
        
        # Проверяем наличие обученной модели
        if avatar.training_type == AvatarTrainingType.PORTRAIT:
            return bool(avatar.diffusers_lora_file_url)
        else:
            return bool(avatar.finetune_id)

    def _build_prompt_with_trigger(
        self,
        prompt: str,
        trigger: Optional[str]
    ) -> str:
        """
        Добавляет триггерную фразу/слово к промпту
        
        Args:
            prompt: Исходный промпт
            trigger: Триггерная фраза или слово
            
        Returns:
            str: Промпт с триггером
        """
        if not trigger:
            return prompt
        
        # Проверяем что триггер еще не в промпте
        if trigger.lower() in prompt.lower():
            return prompt
        
        # Добавляем триггер в начало промпта
        return f"{trigger} {prompt}"

    async def generate_multiple_images(
        self,
        avatar: Avatar,
        prompts: List[str],
        generation_config: Optional[Dict[str, Any]] = None
    ) -> List[Optional[str]]:
        """
        Генерирует несколько изображений для одного аватара
        
        Args:
            avatar: Аватар для генерации
            prompts: Список промптов
            generation_config: Конфигурация генерации
            
        Returns:
            List[Optional[str]]: Список URL изображений
        """
        results = []
        
        for i, prompt in enumerate(prompts):
            try:
                logger.info(f"[FAL AI] Генерация {i+1}/{len(prompts)} для аватара {avatar.id}")
                
                image_url = await self.generate_avatar_image(
                    avatar=avatar,
                    prompt=prompt,
                    generation_config=generation_config
                )
                
                results.append(image_url)
                
                # Небольшая задержка между генерациями
                if i < len(prompts) - 1:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.exception(f"[FAL AI] Ошибка генерации {i+1}: {e}")
                results.append(None)
        
        logger.info(
            f"[FAL AI] Завершена пакетная генерация для аватара {avatar.id}: "
            f"{len([r for r in results if r])}/{len(prompts)} успешно"
        )
        
        return results

    def get_generation_config_presets(self) -> Dict[str, Dict[str, Any]]:
        """
        Возвращает предустановленные конфигурации генерации
        
        Returns:
            Dict[str, Dict[str, Any]]: Словарь с пресетами
        """
        return {
            "fast": {
                "num_inference_steps": 20,
                "guidance_scale": 3.0,
                "image_size": "square",
                "lora_scale": 0.8,
                "finetune_strength": 0.8,
                "safety_tolerance": "2",
            },
            "balanced": {
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "image_size": "square_hd",
                "lora_scale": 1.0,
                "finetune_strength": 1.0,
                "safety_tolerance": "2",
            },
            "quality": {
                "num_inference_steps": 50,
                "guidance_scale": 4.0,
                "image_size": "square_hd",
                "lora_scale": 1.2,
                "finetune_strength": 1.2,
                "safety_tolerance": "2",
            },
            "ultra": {
                "use_ultra": True,
                "finetune_strength": 1.1,
                "aspect_ratio": "1:1",
                "num_images": 1,
                "output_format": "jpeg",
                "enable_safety_checker": True,
                "raw": False,
                "safety_tolerance": "2",
            },
            "portrait": {
                "num_inference_steps": 35,
                "guidance_scale": 3.5,
                "image_size": "portrait_4_3",
                "lora_scale": 1.1,
                "finetune_strength": 1.1,
                "safety_tolerance": "2",
            },
            "landscape": {
                "num_inference_steps": 30,
                "guidance_scale": 3.5,
                "image_size": "landscape_4_3",
                "lora_scale": 1.0,
                "finetune_strength": 1.0,
                "safety_tolerance": "2",
            },
            "artistic": {
                "num_inference_steps": 35,
                "guidance_scale": 4.0,
                "image_size": "square_hd",
                "lora_scale": 1.3,
                "finetune_strength": 1.3,
                "safety_tolerance": "3",
            },
            "photorealistic": {
                "num_inference_steps": 40,
                "guidance_scale": 3.5,
                "image_size": "square_hd",
                "lora_scale": 0.9,
                "finetune_strength": 0.9,
                "safety_tolerance": "2",
            }
        }

    def is_available(self) -> bool:
        """
        Проверяет доступность сервиса генерации
        
        Returns:
            bool: True если сервис доступен
        """
        if self.test_mode:
            return True
            
        return bool(self.api_key)

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Возвращает сводку конфигурации сервиса
        
        Returns:
            Dict[str, Any]: Конфигурация сервиса
        """
        return {
            "test_mode": self.test_mode,
            "api_key_set": bool(self.api_key),
            "available": self.is_available(),
            "supported_types": ["portrait", "style"],
            "supported_models": [
                "fal-ai/flux-lora",  # Портретные аватары
                "fal-ai/flux-pro/finetuned",  # Художественные аватары
                "fal-ai/flux-pro/v1.1-ultra-finetuned"  # Ultra качество
            ],
            "presets": list(self.get_generation_config_presets().keys()),
            "features": {
                "lora_generation": True,
                "finetune_generation": True,
                "ultra_quality": True,
                "safety_checker": True,
                "multiple_formats": True,
                "custom_sizes": True
            }
        } 