"""
Сервис генерации изображений с FAL AI
"""
import asyncio
import os
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
        self.api_key = settings.effective_fal_api_key
        # Используем настройки из конфигурации вместо принудительного тестового режима
        self.test_mode = settings.AVATAR_TEST_MODE
        
        # Настраиваем FAL клиент - устанавливаем переменную окружения FAL_KEY
        if self.api_key and not self.test_mode:
            try:
                # FAL клиент ищет переменную окружения FAL_KEY
                os.environ['FAL_KEY'] = self.api_key
                logger.info(f"🚀 FAL_KEY установлен для продакшн генерации: {self.api_key[:20]}...")
            except Exception as e:
                logger.warning(f"Ошибка настройки FAL клиента: {e}, переключение в тестовый режим")
                self.test_mode = True
        else:
            if self.test_mode:
                logger.info("🧪 Тестовый режим генерации включен - будет использоваться симуляция")
            else:
                logger.warning("FAL_API_KEY не установлен, автоматическое включение тестового режима")
                self.test_mode = True

    async def generate_avatar_image(
        self,
        avatar: Avatar,
        prompt: str,
        generation_config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Генерирует изображение с обученным аватаром
        СТРОГИЕ ПРАВИЛА:
        - Style аватары → finetune_id → FLUX1.1 [pro] ultra Fine-tuned
        - Portrait аватары → LoRA файл → flux-lora
        
        Args:
            avatar: Модель аватара с данными обучения
            prompt: Промпт для генерации
            generation_config: Дополнительные параметры генерации
            
        Returns:
            Optional[str]: URL сгенерированного изображения
            
        Raises:
            ValueError: При отсутствии обученной модели или неправильных данных
            RuntimeError: При ошибках генерации
        """
        try:
            if self.test_mode:
                logger.info(f"[FAL TEST MODE] Симуляция генерации для аватара {avatar.id}")
                return await self._simulate_generation(avatar, prompt)
            
            # Проверяем что аватар обучен
            if not self._is_avatar_trained(avatar):
                raise ValueError(f"Аватар {avatar.id} не обучен или имеет неправильные данные")
            
            # ✅ СТРОГОЕ РАЗДЕЛЕНИЕ ПО ТИПАМ АВАТАРОВ
            
            if avatar.training_type == AvatarTrainingType.PORTRAIT:
                # Портретные аватары используют LoRA файлы + flux-lora API
                logger.info(f"👤 Portrait аватар: используем flux-lora для {avatar.id}")
                return await self._generate_with_lora_legacy(avatar, prompt, generation_config)
            elif avatar.training_type == AvatarTrainingType.STYLE:
                # STYLE аватары больше не поддерживаются (LEGACY)
                logger.error(f"🚫 STYLE аватар {avatar.id} больше не поддерживается")
                raise ValueError(f"STYLE аватары больше не поддерживаются. Пожалуйста, создайте новый портретный аватар.")
            else:
                # Неизвестные типы не поддерживаются
                raise ValueError(f"Неподдерживаемый тип аватара: {avatar.training_type}")
                
        except Exception as e:
            logger.exception(f"[FAL AI] Ошибка генерации изображения для аватара {avatar.id}: {e}")
            raise

    async def _generate_with_lora_legacy(
        self,
        avatar: Avatar,
        prompt: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Генерация с LoRA файлом через flux-lora endpoint
        ТОЛЬКО для портретных аватаров с LoRA файлами
        
        Args:
            avatar: Портретный аватар с LoRA файлом
            prompt: Промпт для генерации
            config: Дополнительные параметры
            
        Returns:
            Optional[str]: URL сгенерированного изображения
        """
        # СТРОГАЯ ПРОВЕРКА: только для портретных аватаров
        if avatar.training_type != AvatarTrainingType.PORTRAIT:
            raise ValueError(f"LoRA API предназначен только для портретных аватаров. Аватар {avatar.id} имеет тип {avatar.training_type}")
        
        if not avatar.diffusers_lora_file_url:
            raise ValueError(f"Портретный аватар {avatar.id} должен иметь LoRA файл")
        
        if avatar.finetune_id:
            logger.warning(f"⚠️ Портретный аватар {avatar.id} содержит finetune_id, но должен использовать только LoRA файл")
        
        # Определяем триггер (для портретных используем trigger_phrase)
        trigger = avatar.trigger_phrase or avatar.trigger_word
        logger.info(f"[FAL AI] 👤 Portrait аватар: lora_url={avatar.diffusers_lora_file_url}, trigger='{trigger}'")
        
        # Формируем промпт с триггерной фразой
        full_prompt = self._build_prompt_with_trigger(prompt, trigger)
        logger.info(f"[FAL AI] 👤 Итоговый промпт с триггером: '{full_prompt}'")
        
        # Настройки генерации для LoRA - ИСПРАВЛЕНО согласно документации FAL AI
        generation_args = {
            "prompt": full_prompt,
            # ✅ ИСПРАВЛЕНО: используем loras массив согласно документации FAL AI
            "loras": [
                {
                    "path": avatar.diffusers_lora_file_url,
                    "scale": config.get("lora_scale", 1.15) if config else 1.15  # 🎯 ОПТИМАЛЬНОЕ: 1.15 из тестирования
                }
            ],
            "num_images": config.get("num_images", 1) if config else 1,
            "num_inference_steps": config.get("num_inference_steps", 28) if config else 28,
            "guidance_scale": config.get("guidance_scale", 3.5) if config else 3.5,
            "enable_safety_checker": config.get("enable_safety_checker", True) if config else True,
        }
        
        # Добавляем image_size или aspect_ratio в зависимости от конфигурации
        if config and config.get("aspect_ratio"):
            # Для FAL AI flux-lora используем image_size вместо aspect_ratio
            aspect_ratio = config.get("aspect_ratio")
            if aspect_ratio == "9:16":
                generation_args["image_size"] = "portrait_4_3"  # Ближайший портретный формат
            elif aspect_ratio == "16:9":
                generation_args["image_size"] = "landscape_4_3"  # Ближайший альбомный формат
            elif aspect_ratio == "1:1":
                generation_args["image_size"] = "square_hd"
            else:
                generation_args["image_size"] = "square_hd"  # По умолчанию как в Playground
            logger.info(f"[FAL AI] 🖼️ Преобразование aspect_ratio {aspect_ratio} в image_size: {generation_args['image_size']}")
        else:
            generation_args["image_size"] = config.get("image_size", "square_hd") if config else "square_hd"  # 🎯 Default как в Playground
        
        # Добавляем negative_prompt если есть в конфигурации для LoRA
        if config and config.get("negative_prompt"):
            generation_args["negative_prompt"] = config.get("negative_prompt")
            logger.info(f"[FAL AI] ✅ Добавлен negative prompt для LoRA: {len(config['negative_prompt'])} символов")
            logger.debug(f"[FAL AI] LoRA negative prompt: {config['negative_prompt'][:200]}...")
        else:
            if avatar.training_type == AvatarTrainingType.PORTRAIT:
                logger.warning(f"[FAL AI] ⚠️ Negative prompt НЕ ПЕРЕДАН для LoRA аватара {avatar.id}")
            else:
                logger.info(f"[FAL AI] ℹ️ Negative prompt встроен в основной промпт для FLUX Pro аватара {avatar.id}")
        
        # Добавляем seed если указан
        if config and config.get("seed"):
            generation_args["seed"] = config.get("seed")
        
        logger.info(f"[FAL AI] 🚀 FLUX LoRA для портретного аватара {avatar.id}")
        logger.info(f"[FAL AI] 🎯 Параметры LoRA: scale={generation_args['loras'][0]['scale']}, steps={generation_args['num_inference_steps']}, guidance={generation_args['guidance_scale']}")
        logger.info(f"[FAL AI] 🖼️ Размер изображения: {generation_args['image_size']}")
        logger.debug(f"[FAL AI] LoRA args: {generation_args}")
        
        try:
            result = fal_client.subscribe(
                "fal-ai/flux-lora",
                arguments=generation_args,
                with_logs=True
            )
            
            logger.info(f"[FAL AI] ✅ Генерация LoRA завершена успешно")
            logger.debug(f"[FAL AI] LoRA result: {result}")
            
            # Извлекаем URL изображения из результата
            if isinstance(result, dict) and "images" in result:
                images = result["images"]
                if images and len(images) > 0:
                    image_url = images[0]["url"] if isinstance(images[0], dict) else images[0]
                    logger.info(f"[FAL AI] LoRA изображение готово: {image_url}")
                    return image_url
                else:
                    logger.error(f"[FAL AI] LoRA результат не содержит изображений: {result}")
                    return None
            else:
                logger.error(f"[FAL AI] LoRA неожиданный формат результата: {result}")
                return None
            
        except Exception as e:
            logger.error(f"[FAL AI] ❌ Ошибка генерации LoRA: {e}")
            raise

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
        СТРОГИЕ ПРАВИЛА:
        - Style аватары ДОЛЖНЫ иметь finetune_id
        - Portrait аватары ДОЛЖНЫ иметь diffusers_lora_file_url
        
        Args:
            avatar: Аватар для проверки
            
        Returns:
            bool: True если аватар готов к генерации
        """
        from ...database.models import AvatarStatus
        
        # Проверяем статус
        if avatar.status != "completed":
            logger.warning(f"Аватар {avatar.id} не готов к генерации. Статус: {avatar.status}")
            return False
        
        # Определяем фактический тип аватара по наличию данных обучения
        has_lora = bool(avatar.diffusers_lora_file_url)
        has_finetune = bool(avatar.finetune_id)
        
        logger.info(f"Диагностика аватара {avatar.id}: "
                   f"training_type={avatar.training_type}, "
                   f"has_lora={has_lora}, has_finetune={has_finetune}")
        
        # СТРОГАЯ ПРОВЕРКА: каждый тип должен иметь правильные данные
        
        if avatar.training_type == AvatarTrainingType.PORTRAIT:
            if has_lora and not has_finetune:
                logger.info(f"✅ Портретный аватар {avatar.id} готов к генерации (имеет LoRA файл)")
                return True
            else:
                if has_finetune and not has_lora:
                    logger.error(
                        f"❌ ОШИБКА ДАННЫХ: Портретный аватар {avatar.id} имеет finetune_id вместо LoRA файла! "
                        f"Портретные аватары должны использовать LoRA файлы."
                    )
                elif not has_lora:
                    logger.error(f"❌ Портретный аватар {avatar.id} не имеет LoRA файла")
                else:
                    logger.error(f"❌ Портретный аватар {avatar.id} имеет и LoRA и finetune - конфликт данных")
                return False
        elif avatar.training_type == AvatarTrainingType.STYLE:
            # STYLE аватары - LEGACY, больше не поддерживаются
            logger.error(f"❌ STYLE аватар {avatar.id} больше не поддерживается (LEGACY). Используйте только портретные аватары.")
            return False
        else:
            # Любой другой тип не поддерживается
            logger.error(f"❌ Аватар {avatar.id} имеет неподдерживаемый тип обучения: {avatar.training_type}")
            return False

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
        Возвращает предустановленные конфигурации генерации для FLUX1.1 [pro] ultra Fine-tuned
        
        Returns:
            Dict[str, Dict[str, Any]]: Словарь с пресетами
        """
        return {
            "fast": {
                "finetune_strength": 0.8,
                "aspect_ratio": "1:1",
                "output_format": "jpeg",
                "enable_safety_checker": True,
                "safety_tolerance": 2,
                "raw": False,
            },
            "balanced": {
                "finetune_strength": 1.0,
                "aspect_ratio": "1:1",
                "output_format": "jpeg",
                "enable_safety_checker": True,
                "safety_tolerance": 2,
                "raw": False,
            },
            "quality": {
                "finetune_strength": 1.2,
                "aspect_ratio": "1:1",
                "output_format": "jpeg",
                "enable_safety_checker": True,
                "safety_tolerance": 3,
                "raw": False,
            },
            "ultra": {
                "finetune_strength": 1.3,
                "aspect_ratio": "1:1",
                "output_format": "jpeg", 
                "enable_safety_checker": True,
                "safety_tolerance": 3,
                "raw": False,
            },
            "portrait": {
                "finetune_strength": 1.1,
                "aspect_ratio": "3:4",
                "output_format": "jpeg",
                "enable_safety_checker": True,
                "safety_tolerance": 2,
                "raw": False,
            },
            "landscape": {
                "finetune_strength": 1.0,
                "aspect_ratio": "4:3",
                "output_format": "jpeg",
                "enable_safety_checker": True,
                "safety_tolerance": 2,
                "raw": False,
            },
            "wide": {
                "finetune_strength": 1.0,
                "aspect_ratio": "16:9",
                "output_format": "jpeg",
                "enable_safety_checker": True,
                "safety_tolerance": 2,
                "raw": False,
            },
            "square_hd": {
                "finetune_strength": 1.1,
                "aspect_ratio": "1:1",
                "output_format": "jpeg",
                "enable_safety_checker": True,
                "safety_tolerance": 2,
                "raw": False,
            },
            "artistic": {
                "finetune_strength": 1.4,
                "aspect_ratio": "1:1",
                "output_format": "jpeg",
                "enable_safety_checker": True,
                "safety_tolerance": 4,
                "raw": True,
            },
            "photorealistic": {
                "finetune_strength": 1.0,
                "aspect_ratio": "1:1", 
                "output_format": "jpeg",
                "enable_safety_checker": True,
                "safety_tolerance": 2,
                "raw": False,
            },
            "photorealistic_max": {
                "finetune_strength": 1.0,
                "aspect_ratio": "1:1", 
                "output_format": "jpeg",
                "enable_safety_checker": True,
                "safety_tolerance": 1,
                "raw": False,
                "num_images": 1,
                "description": "Максимальный фотореализм с finetune_strength=1.0"
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
            "supported_types": ["portrait"],
            "primary_model": "fal-ai/flux-pro/v1.1-ultra-finetuned",
            "supported_models": [
                "fal-ai/flux-pro/v1.1-ultra-finetuned",  # Основная модель для всех типов
            ],
            "presets": list(self.get_generation_config_presets().keys()),
            "features": {
                "ultra_quality": True,
                "lora_support": True,
                "finetune_support": True,
                "safety_checker": True,
                "multiple_formats": True,
                "custom_aspect_ratios": True,
                "2k_resolution": True,
                "10x_faster": True,
                "commercial_use": True
            },
            "aspect_ratios": [
                "21:9", "16:9", "4:3", "3:2", "1:1", 
                "2:3", "3:4", "9:16", "9:21"
            ],
            "max_resolution": "2048x2048",
            "performance": "10x faster than previous versions"
        } 