"""
Модуль анализа и классификации промптов
"""
import re
from typing import Dict, List

from app.core.logger import get_logger

logger = get_logger(__name__)


class PromptAnalyzer:
    """Анализатор промптов для определения характеристик"""
    
    def __init__(self):
        pass
    
    def is_already_detailed(self, prompt: str) -> bool:
        """
        Проверяет является ли промпт уже детальным
        
        Args:
            prompt: Промпт для проверки
            
        Returns:
            bool: True если промпт уже детальный
        """
        detailed_indicators = [
            "cinematic", "ultra-realistic", "professional", "high-quality",
            "depth of field", "bokeh", "detailed", "8K", "4K",
            "professional photography", "medium format", "lighting",
            "composition", "shallow depth"
        ]
        
        prompt_lower = prompt.lower()
        indicator_count = sum(1 for indicator in detailed_indicators if indicator in prompt_lower)
        
        return indicator_count >= 3
    
    def determine_shot_type(self, prompt_lower: str) -> str:
        """
        Определяет тип кадра на основе промпта
        
        Args:
            prompt_lower: Промпт в нижнем регистре
            
        Returns:
            str: Тип кадра
        """
        if any(term in prompt_lower for term in ["полный рост", "full body", "в полный рост"]):
            return "full-body portrait"
        elif any(term in prompt_lower for term in ["крупный план", "close-up", "лицо"]):
            return "close-up portrait" 
        elif any(term in prompt_lower for term in ["средний план", "medium shot", "по пояс"]):
            return "medium shot portrait"
        else:
            return "portrait"
    
    def analyze_lighting(self, prompt_lower: str) -> str:
        """
        Анализирует и улучшает описание освещения
        
        Args:
            prompt_lower: Промпт в нижнем регистре
            
        Returns:
            str: Описание освещения
        """
        if any(term in prompt_lower for term in ["студия", "studio", "студийный"]):
            return "with professional studio lighting setup, featuring key light, fill light, and rim light for dimensional modeling"
        elif any(term in prompt_lower for term in ["золотой час", "golden hour", "закат", "рассвет"]):
            return "bathed in warm golden hour lighting with soft, directional sunlight creating beautiful rim lighting"
        elif any(term in prompt_lower for term in ["окно", "window", "естественный свет"]):
            return "illuminated by soft, diffused natural window light creating gentle shadows and even skin tones"
        elif any(term in prompt_lower for term in ["вечер", "ночь", "night", "evening"]):
            return "with dramatic evening lighting featuring warm ambient light and strategic highlights"
        else:
            return "with professionally balanced lighting that accentuates facial features and creates depth"
    
    def create_composition_description(self, prompt_lower: str) -> str:
        """
        Создает описание композиции
        
        Args:
            prompt_lower: Промпт в нижнем регистре
            
        Returns:
            str: Описание композиции
        """
        if any(term in prompt_lower for term in ["центр", "center", "по центру"]):
            return "The subject is perfectly centered in the frame with balanced composition following the rule of thirds"
        else:
            return "The composition follows professional portrait guidelines with the subject positioned for optimal visual impact"
    
    def create_detailed_pose_description(self, prompt_lower: str) -> str:
        """
        Создает детальное описание позы
        
        Args:
            prompt_lower: Промпт в нижнем регистре
            
        Returns:
            str: Описание позы
        """
        if any(term in prompt_lower for term in ["стоит", "standing", "стоя"]):
            return "standing in a confident, natural pose with relaxed shoulders and authentic body language"
        elif any(term in prompt_lower for term in ["сидит", "sitting", "сидя"]):
            return "seated in a comfortable, professional pose with natural hand placement and confident posture"
        else:
            return "posed naturally with confident body language and professional positioning"
    
    def create_detailed_environment(self, prompt_lower: str) -> str:
        """
        Создает детальное описание окружения
        
        Args:
            prompt_lower: Промпт в нижнем регистре
            
        Returns:
            str: Описание окружения
        """
        environments = {
            "офис": "in a modern, professional office environment with clean lines, contemporary furniture, and sophisticated business atmosphere",
            "office": "in a modern, professional office environment with clean lines, contemporary furniture, and sophisticated business atmosphere",
            "улица": "on a beautifully composed urban street with interesting architectural elements and natural depth in the background",
            "street": "on a beautifully composed urban street with interesting architectural elements and natural depth in the background",
            "студия": "in a professional photography studio with seamless backdrop and controlled lighting environment",
            "studio": "in a professional photography studio with seamless backdrop and controlled lighting environment",
            "дом": "in an elegantly designed interior space with tasteful decor and warm, inviting atmosphere",
            "home": "in an elegantly designed interior space with tasteful decor and warm, inviting atmosphere",
            "парк": "in a lush, natural park setting with beautiful foliage and organic background elements",
            "park": "in a lush, natural park setting with beautiful foliage and organic background elements",
        }
        
        for keyword, description in environments.items():
            if keyword in prompt_lower:
                return description
        
        return "in a carefully chosen environment that complements the subject and enhances the overall composition"
    
    def determine_color_palette(self, prompt_lower: str) -> str:
        """
        Определяет цветовую палитру
        
        Args:
            prompt_lower: Промпт в нижнем регистре
            
        Returns:
            str: Описание цветовой палитры
        """
        if any(term in prompt_lower for term in ["черно-белый", "black and white", "monochrome"]):
            return "Rich monochromatic tones with deep blacks, crisp whites, and beautiful grayscale gradations"
        elif any(term in prompt_lower for term in ["теплый", "warm", "золотой"]):
            return "Warm color palette featuring golden tones, rich ambers, and inviting earth colors"
        elif any(term in prompt_lower for term in ["холодный", "cool", "синий"]):
            return "Cool color palette with sophisticated blues, elegant teals, and calming tones"
        else:
            return "Naturally balanced color palette with authentic skin tones and harmonious environmental colors"
    
    def enhance_environmental_context(self, prompt_lower: str) -> List[str]:
        """
        Улучшает контекст окружения
        
        Args:
            prompt_lower: Промпт в нижнем регистре
            
        Returns:
            List[str]: Список улучшений контекста
        """
        enhancements = []
        
        # Городская среда
        if any(term in prompt_lower for term in ["город", "city", "urban", "улица"]):
            enhancements.extend([
                "urban sophistication with modern architectural elements",
                "city energy captured through careful background composition",
                "metropolitan atmosphere with contemporary design elements"
            ])
        
        # Природная среда
        elif any(term in prompt_lower for term in ["природа", "nature", "лес", "forest", "парк"]):
            enhancements.extend([
                "natural beauty with organic textures and flowing lines",
                "harmonious integration with the natural environment",
                "peaceful outdoor setting with authentic natural lighting"
            ])
        
        # Интерьер
        elif any(term in prompt_lower for term in ["дом", "home", "комната", "room", "интерьер"]):
            enhancements.extend([
                "sophisticated interior design with attention to detail",
                "warm, inviting atmosphere with tasteful furnishings",
                "elegant indoor environment with professional styling"
            ])
        
        return enhancements
    
    def clean_and_optimize_prompt(self, prompt: str) -> str:
        """
        Очищает и оптимизирует промпт
        
        Args:
            prompt: Исходный промпт
            
        Returns:
            str: Очищенный промпт
        """
        # Убираем лишние пробелы
        cleaned = re.sub(r'\s+', ' ', prompt)
        
        # Убираем повторяющиеся запятые
        cleaned = re.sub(r',\s*,', ',', cleaned)
        
        # Убираем двойные точки
        cleaned = re.sub(r'\.\s*\.', '.', cleaned)
        
        # Убираем пробелы перед знаками препинания
        cleaned = re.sub(r'\s+([,.!?])', r'\1', cleaned)
        
        # Добавляем пробел после знаков препинания если его нет
        cleaned = re.sub(r'([,.!?])([^\s])', r'\1 \2', cleaned)
        
        return cleaned.strip() 