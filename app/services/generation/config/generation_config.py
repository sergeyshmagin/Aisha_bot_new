"""
Модуль конфигурации генерации изображений
"""
from typing import Dict
from app.core.logger import get_logger

logger = get_logger(__name__)


class GenerationConfig:
    """Управление конфигурацией генерации"""
    
    @staticmethod
    def get_generation_config(quality_preset: str, aspect_ratio: str, num_images: int) -> Dict:
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
            "output_quality": 95,
            "aspect_ratio": aspect_ratio
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
        
        logger.info(f"[Generation Config] aspect_ratio={aspect_ratio}, config содержит: aspect_ratio={config.get('aspect_ratio')}")
        
        return config 