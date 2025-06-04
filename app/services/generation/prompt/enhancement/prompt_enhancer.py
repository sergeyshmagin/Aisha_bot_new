"""
Модуль улучшения и детализации промптов
"""
from typing import List

from app.core.logger import get_logger
from app.services.generation.prompt.analysis.prompt_analyzer import PromptAnalyzer

logger = get_logger(__name__)


class PromptEnhancer:
    """Улучшитель промптов для максимального качества генерации"""
    
    def __init__(self):
        self.analyzer = PromptAnalyzer()
    
    def create_enhanced_detailed_prompt(self, base_prompt: str, avatar_type: str) -> str:
        """
        Создает кинематографические детальные промпты в стиле профессиональных фотографий
        
        Args:
            base_prompt: Базовый промпт
            avatar_type: Тип аватара
            
        Returns:
            str: Улучшенный детальный промпт
        """
        prompt_lower = base_prompt.lower()
        
        # Проверяем: если промпт уже очень детальный - возвращаем как есть
        if len(base_prompt) > 400 and self.analyzer.is_already_detailed(base_prompt):
            logger.info(f"[Detailed Mode] Промпт уже детальный ({len(base_prompt)} символов) - возвращаем как есть")
            # Добавляем только TOK если его нет
            if not base_prompt.startswith("TOK"):
                return f"TOK, {base_prompt}"
            return base_prompt
        
        # Анализируем контекст и создаем кинематографический промпт
        
        # 1. Начинаем с TOK для портретных аватаров
        if avatar_type == "portrait":
            enhanced_parts = ["TOK"]
        else:
            enhanced_parts = []
        
        # 2. Добавляем технические характеристики фото
        tech_specs = [
            "A high-quality, cinematic, ultra-realistic",
            self.analyzer.determine_shot_type(prompt_lower),
            "photograph, captured by a professional medium-format digital camera",
            "in style of super-detailed 8K resolution imagery"
        ]
        
        # 3. Определяем и добавляем описание освещения
        lighting_desc = self.analyzer.analyze_lighting(prompt_lower)
        tech_specs.append(lighting_desc)
        
        enhanced_parts.extend(tech_specs)
        
        # 4. Добавляем композицию и центрирование
        composition = self.analyzer.create_composition_description(prompt_lower)
        enhanced_parts.append(composition)
        
        # 5. Детальное описание персонажа
        character_desc = self._enhance_character_description(base_prompt, prompt_lower)
        enhanced_parts.append(character_desc)
        
        # 6. Описание позы и ракурса
        pose_desc = self.analyzer.create_detailed_pose_description(prompt_lower)
        enhanced_parts.append(pose_desc)
        
        # 7. Детальное описание окружения и фона
        environment_desc = self.analyzer.create_detailed_environment(prompt_lower)
        if environment_desc:
            enhanced_parts.append(environment_desc)
        
        # 8. Технические параметры камеры и фокуса
        camera_details = [
            "The depth of field is exceptional, ensuring sharp focus on the subject",
            "while creating beautiful bokeh in the background, shot with professional equipment",
            "delivering crystal-clear detail and exceptional image quality"
        ]
        enhanced_parts.extend(camera_details)
        
        # 9. Цветовая палитра и общее качество
        color_palette = self.analyzer.determine_color_palette(prompt_lower)
        enhanced_parts.append(color_palette)
        
        # 10. Дополнительный контекст окружения
        environmental_enhancements = self.analyzer.enhance_environmental_context(prompt_lower)
        enhanced_parts.extend(environmental_enhancements)
        
        # 11. Финальные качественные характеристики
        quality_specs = [
            "The image exhibits professional-grade quality with impeccable attention to detail",
            "featuring rich textures, natural proportions, and photorealistic rendering",
            "captured with perfect exposure and professional color grading"
        ]
        enhanced_parts.extend(quality_specs)
        
        # Собираем все части
        final_prompt = ". ".join(enhanced_parts) + "."
        
        # Очищаем и оптимизируем
        final_prompt = self.analyzer.clean_and_optimize_prompt(final_prompt)
        
        logger.info(f"[Enhanced Prompt] Создан детальный промпт: {len(final_prompt)} символов")
        return final_prompt
    
    def _enhance_character_description(self, original_prompt: str, prompt_lower: str) -> str:
        """
        Улучшает описание персонажа
        
        Args:
            original_prompt: Оригинальный промпт
            prompt_lower: Промпт в нижнем регистре
            
        Returns:
            str: Улучшенное описание персонажа
        """
        # Извлекаем основную часть описания персонажа из оригинального промпта
        character_base = original_prompt
        
        # Добавляем детали на основе анализа
        enhancements = []
        
        if any(term in prompt_lower for term in ["мужчина", "man", "парень", "guy"]):
            enhancements.append("featuring authentic masculine characteristics and natural expression")
        elif any(term in prompt_lower for term in ["женщина", "woman", "девушка", "girl"]):
            enhancements.append("featuring authentic feminine characteristics and natural expression")
        
        if any(term in prompt_lower for term in ["костюм", "suit", "деловой"]):
            enhancements.append("dressed in professional business attire with attention to fabric details and fitting")
        elif any(term in prompt_lower for term in ["платье", "dress"]):
            enhancements.append("wearing an elegant dress with beautiful fabric draping and styling")
        
        # Добавляем общие улучшения
        enhancements.extend([
            "with natural skin texture and realistic facial features",
            "displaying authentic human proportions and lifelike details"
        ])
        
        if enhancements:
            return f"{character_base}, {', '.join(enhancements)}"
        else:
            return character_base
    
    def get_negative_prompt(self, avatar_type: str) -> str:
        """
        Получает negative prompt для улучшения качества генерации
        
        Args:
            avatar_type: Тип аватара
            
        Returns:
            str: Negative prompt
        """
        base_negative = [
            "bad quality", "blurry", "low resolution", "pixelated", "artifacts",
            "distorted face", "extra limbs", "missing limbs", "deformed",
            "unrealistic proportions", "cartoon", "anime", "painted",
            "artificial", "fake", "plastic", "doll-like", "uncanny valley"
        ]
        
        if avatar_type == "portrait":
            portrait_negative = [
                "multiple faces", "split face", "asymmetrical face",
                "wrong eye count", "mismatched eyes", "floating hair",
                "neck artifacts", "shoulder issues"
            ]
            base_negative.extend(portrait_negative)
        
        return ", ".join(base_negative) 