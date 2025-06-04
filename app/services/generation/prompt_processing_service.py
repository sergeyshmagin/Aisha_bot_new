"""
Сервис обработки промптов для генерации изображений (рефакторинг)
Модульная архитектура для лучшей поддержки и читаемости
"""
import time
from typing import Dict, Any

from app.core.config import settings
from app.core.logger import get_logger
from app.services.generation.cinematic_prompt_service import CinematicPromptService
from app.services.generation.prompt.translation.translator import PromptTranslator
from app.services.generation.prompt.enhancement.prompt_enhancer import PromptEnhancer
from app.services.generation.prompt.analysis.prompt_analyzer import PromptAnalyzer

logger = get_logger(__name__)


class PromptProcessingService:
    """
    Главный сервис обработки промптов
    Координирует работу всех модулей обработки промптов
    """
    
    def __init__(self):
        self.translator = PromptTranslator()
        self.enhancer = PromptEnhancer()
        self.analyzer = PromptAnalyzer()
        self.cinematic_service = CinematicPromptService()
        self.openai_api_key = settings.OPENAI_API_KEY
    
    async def process_prompt(self, user_prompt: str, avatar_type: str) -> Dict[str, Any]:
        """
        Обрабатывает пользовательский промпт создавая кинематографический детальный промпт
        
        Args:
            user_prompt: Промпт от пользователя
            avatar_type: Тип аватара (portrait)
            
        Returns:
            dict: Результат обработки с кинематографическим промптом и negative prompt
        """
        start_time = time.time()
        
        try:
            logger.info(f"[Prompt Processing] Начата кинематографическая обработка: '{user_prompt[:50]}...'")
            
            # Используем кинематографический сервис
            cinematic_result = await self.cinematic_service.create_cinematic_prompt(
                user_prompt=user_prompt,
                avatar_type=avatar_type,
                style_preset="photorealistic"
            )
            
            # Создаем negative prompt
            negative_prompt = self.enhancer.get_negative_prompt(avatar_type)
            
            processing_time = time.time() - start_time
            
            # Формируем результат
            result = {
                "original": user_prompt,
                "processed": cinematic_result["processed"],
                "negative_prompt": negative_prompt,
                "translation_needed": cinematic_result.get("translation_applied", False),
                "cinematic_enhancement": cinematic_result.get("enhancement_applied", False),
                "style": cinematic_result.get("style", "cinematic"),
                "processing_time": processing_time,
                "word_count": cinematic_result.get("word_count", 0),
                "technical_level": cinematic_result.get("technical_level", "professional")
            }
            
            logger.info(f"[Prompt Processing] Кинематографическая обработка завершена за {processing_time:.2f}с")
            logger.info(f"[Cinematic] Создан промпт: {len(result['processed'])} символов, стиль: {result['style']}")
            
            return result
            
        except Exception as e:
            logger.exception(f"[Prompt Processing] Ошибка кинематографической обработки: {e}")
            # Fallback к базовой обработке
            return await self._fallback_processing(user_prompt, avatar_type, start_time)
    
    async def _fallback_processing(self, user_prompt: str, avatar_type: str, start_time: float) -> Dict[str, Any]:
        """
        Резервная обработка промпта при ошибке основной обработки
        
        Args:
            user_prompt: Исходный промпт
            avatar_type: Тип аватара
            start_time: Время начала обработки
            
        Returns:
            dict: Результат резервной обработки
        """
        try:
            # Проверяем нужен ли перевод
            translated_prompt = user_prompt
            translation_needed = False
            
            if self.translator.needs_translation(user_prompt):
                translated_prompt = await self.translator.translate_with_gpt(user_prompt)
                translation_needed = True
            
            # Создаем детальный промпт
            enhanced_prompt = self.enhancer.create_enhanced_detailed_prompt(translated_prompt, avatar_type)
            
            # Создаем negative prompt
            negative_prompt = self.enhancer.get_negative_prompt(avatar_type)
            
            processing_time = time.time() - start_time
            
            return {
                "original": user_prompt,
                "processed": enhanced_prompt,
                "negative_prompt": negative_prompt,
                "translation_needed": translation_needed,
                "cinematic_enhancement": True,
                "style": "enhanced_fallback",
                "processing_time": processing_time,
                "word_count": len(enhanced_prompt.split()),
                "technical_level": "professional"
            }
            
        except Exception as e:
            logger.exception(f"[Fallback Processing] Ошибка резервной обработки: {e}")
            # Минимальная обработка
            fallback_prompt = f"TOK, {user_prompt}" if avatar_type == "portrait" else user_prompt
            
            return {
                "original": user_prompt,
                "processed": fallback_prompt,
                "negative_prompt": self.enhancer.get_negative_prompt(avatar_type),
                "translation_needed": False,
                "cinematic_enhancement": False,
                "style": "minimal_fallback",
                "processing_time": time.time() - start_time,
                "word_count": len(fallback_prompt.split()),
                "technical_level": "basic"
            }
    
    # Методы делегирования к модулям для обратной совместимости
    async def translate_with_gpt(self, russian_text: str) -> str:
        """Переводит промпт через GPT API"""
        return await self.translator.translate_with_gpt(russian_text)
    
    async def create_enhanced_detailed_prompt(self, base_prompt: str, avatar_type: str) -> str:
        """Создает детальный улучшенный промпт"""
        return self.enhancer.create_enhanced_detailed_prompt(base_prompt, avatar_type)
    
    def needs_translation(self, text: str) -> bool:
        """Проверяет нужен ли перевод"""
        return self.translator.needs_translation(text)
    
    def translate_to_english(self, text: str) -> str:
        """Локальный перевод"""
        return self.translator.translate_to_english(text)
    
    def is_already_detailed(self, prompt: str) -> bool:
        """Проверяет детальность промпта"""
        return self.analyzer.is_already_detailed(prompt)
    
    def get_negative_prompt(self, avatar_type: str) -> str:
        """Получает negative prompt"""
        return self.enhancer.get_negative_prompt(avatar_type)
    
    def clean_and_optimize_prompt(self, prompt: str) -> str:
        """Очищает и оптимизирует промпт"""
        return self.analyzer.clean_and_optimize_prompt(prompt)
    
    def is_available(self) -> bool:
        """Проверяет доступность сервиса"""
        return bool(self.openai_api_key) 