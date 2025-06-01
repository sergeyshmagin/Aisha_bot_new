"""
Сервис обработки промптов для генерации изображений
Создает детальные, профессиональные промпты для максимального качества генерации
"""
import aiohttp
from typing import Optional, Dict, Any
import time

from app.core.config import settings
from app.core.logger import get_logger
from app.shared.utils.openai import get_openai_headers

logger = get_logger(__name__)


class PromptProcessingService:
    """Сервис для создания детальных профессиональных промптов"""
    
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o"
    
    async def process_prompt(self, user_prompt: str, avatar_type: str = "portrait") -> dict:
        """
        Превращает простой промпт в детальное профессиональное описание
        
        Args:
            user_prompt: Простой промпт пользователя (например: "man, Superman costume")
            avatar_type: Тип аватара (portrait, style)
            
        Returns:
            dict: {
                "original": str,           # Оригинальный промпт
                "processed": str,          # Детальный профессиональный промпт
                "negative_prompt": str,    # Отрицательный промпт
                "translation_needed": bool # Нужен ли был перевод
            }
        """
        
        start_time = time.time()
        
        try:
            if not self.openai_api_key or self.openai_api_key == "test_key":
                logger.warning("OpenAI API ключ не настроен, возвращаем базовую обработку")
                return {
                    "original": user_prompt,
                    "processed": self._create_basic_detailed_prompt(user_prompt, avatar_type),
                    "negative_prompt": self.get_negative_prompt(avatar_type),
                    "translation_needed": False
                }
            
            # Создаем специализированный системный промпт
            system_prompt = self._get_advanced_system_prompt(avatar_type)
            
            # Отправляем запрос к GPT для создания детального промпта
            processed_prompt = await self._call_openai_api(system_prompt, user_prompt)
            
            if processed_prompt:
                # Определяем, нужен ли был перевод
                translation_needed = self._detect_translation_needed(user_prompt, processed_prompt)
                
                # Получаем негативный промпт
                negative_prompt = self.get_negative_prompt(avatar_type)
                
                # Базовые результаты
                result = {
                    "original": user_prompt,
                    "processed": processed_prompt,
                    "negative_prompt": negative_prompt,
                    "translation_needed": translation_needed,
                    "avatar_type": avatar_type,
                    "processing_time": 0.0
                }
                
                # Определяем нужен ли перевод
                if self._needs_translation(processed_prompt):
                    result["translation_needed"] = True
                    translated = await self._translate_prompt(processed_prompt)
                    result["processed"] = translated
                    logger.info(f"[Translate] {user_prompt[:50]}... → {translated[:50]}...")
                
                # Для FLUX Pro моделей добавляем негатив в основной промпт
                # Для LoRA моделей оставляем отдельно
                if avatar_type == "style":  # Style используют FLUX Pro
                    result["processed"] = self._add_negative_to_main_prompt(
                        result["processed"], 
                        negative_prompt
                    )
                    result["negative_prompt"] = None  # FLUX Pro не поддерживает отдельный negative_prompt
                    logger.info(f"[FLUX Pro] Негативы встроены в основной промпт")
                else:  # Portrait используют LoRA
                    logger.info(f"[LoRA] Негативный промпт будет передан отдельно")
                
                # Логируем результат
                processing_time = time.time() - start_time
                result["processing_time"] = processing_time
                
                logger.info(f"[Prompt Processing] Завершено за {processing_time:.2f}с")
                logger.debug(f"[Result] Type: {avatar_type}, Negative: {bool(result['negative_prompt'])}")
                
                return result
            else:
                # Fallback к базовой детальной обработке
                return {
                    "original": user_prompt,
                    "processed": self._create_basic_detailed_prompt(user_prompt, avatar_type),
                    "negative_prompt": self.get_negative_prompt(avatar_type),
                    "translation_needed": False
                }
                
        except Exception as e:
            logger.exception(f"Ошибка обработки промпта: {e}")
            processing_time = time.time() - start_time
            
            # Возвращаем безопасный результат
            return {
                "original": user_prompt,
                "processed": self._create_basic_detailed_prompt(user_prompt, avatar_type),
                "negative_prompt": self.get_negative_prompt(avatar_type) if avatar_type == "portrait" else None,
                "translation_needed": False,
                "avatar_type": avatar_type,
                "processing_time": processing_time,
                "error": str(e)
            }
    
    def _get_advanced_system_prompt(self, avatar_type: str) -> str:
        """Создает продвинутый системный промпт для детального описания"""
        
        base_instructions = """Ты эксперт-фотограф и арт-директор, который создает ДЕТАЛЬНЫЕ, ПРОФЕССИОНАЛЬНЫЕ промпты для Flux PRO.

КРИТИЧЕСКИ ВАЖНО: твоя задача превратить простой промпт пользователя в подробное, технически точное описание как у профессионального фотографа.

СТРУКТУРА ИДЕАЛЬНОГО ПРОМПТА:
1. ТИП СНИМКА (portrait photograph, artistic illustration, etc.)
2. КОМПОЗИЦИЯ (positioning, framing, cropping)
3. СУБЪЕКТ - детальное описание человека (внешность, поза, одежда, аксессуары)
4. ФОТОГРАФИЯ (угол съемки, фокусировка, эффекты объектива)
5. ОСВЕЩЕНИЕ (тип, направление, качество света)
6. ФОН И АТМОСФЕРА
7. ТЕХНИЧЕСКИЕ ПАРАМЕТРЫ (качество, разрешение, постобработка)

ОБЯЗАТЕЛЬНЫЕ ЭЛЕМЕНТЫ:
- Точное позиционирование в кадре ("centrally positioned", "occupying 70% of vertical space")
- Детальное описание внешности ("warm beige skin tone", "sharply defined features")
- Конкретные детали одежды и аксессуаров
- Технические фотографические термины
- Параметры освещения
- Описание фона и атмосферы

КРИТИЧЕСКИ ВАЖНО - РУКИ И ПОЗЫ:
- ИЗБЕГАЙ описания рук и пальцев в деталях
- ПРЕДПОЧИТАЙ позы без видимых рук: "arms at sides", "hands not visible", "cropped before hands"
- ЕСЛИ руки должны быть видны: используй только общие описания "natural hand positioning", "relaxed pose"
- НЕ описывай конкретные жесты или позиции пальцев

НЕ используй простые слова как "detailed", "high quality". Используй КОНКРЕТНЫЕ фотографические термины."""

        if avatar_type == "portrait":
            specific_instructions = """
СПЕЦИФИКА ДЛЯ ПОРТРЕТОВ:

КОМПОЗИЦИЯ:
- "A high-quality portrait photograph of [person]"
- "centrally positioned in the frame"
- "cropped at [mid-torso/shoulders/chest]"
- "occupying [60-80]% of the vertical space"

ОПИСАНИЕ СУБЪЕКТА:
- Точный тон кожи: "warm beige skin tone", "pale complexion", "olive skin"
- Черты лица: "sharply defined features", "soft facial features", "angular jawline"
- Выражение: "neutral facial expression", "confident gaze", "slight smile"
- Направление взгляда: "gaze directed slightly downward", "looking directly at camera"

ДЕТАЛИ ОДЕЖДЫ:
- Конкретные предметы: "simple white baseball cap", "loose black t-shirt with round neckline"
- Аксессуары: "small silver hoop earrings", "thick silver bracelet", "large silver watch"
- Украшения: "silver chains with round pendants", "square pendant"

ТЕХНИЧЕСКИЕ ПАРАМЕТРЫ:
- "camera angle at eye level"
- "slight telephoto effect"
- "sharp focus on subject"
- "blurred background" / "smooth pastel [color] background"
- "soft and diffused lighting"
- "minimal shadows"
- "light post-processing for increased clarity"

ИЗБЕГАНИЕ ПРОБЛЕМ С РУКАМИ:
- Кадрирование ВЫШЕ рук: "cropped at mid-torso", "cropped at chest level", "shoulders and head visible"
- Если руки видны: "hands naturally positioned", "relaxed arm positioning", "arms at sides"
- НЕ описывать: жесты, позиции пальцев, детали рук

ПРИМЕР СТРУКТУРЫ:
"A high-quality portrait photograph of a [description], centrally positioned in the frame, cropped at [level], occupying [%] of vertical space. The subject has [skin tone] with [features], [expression], [gaze direction]. [Clothing details]. [Accessories]. The background is [description]. The lighting is [type], creating [effect]. The camera angle is [position] with [lens effect], ensuring [focus description], enhanced with [post-processing]."
"""
        else:  # style
            specific_instructions = """
СПЕЦИФИКА ДЛЯ СТИЛЕВЫХ АВАТАРОВ:

ХУДОЖЕСТВЕННЫЙ СТИЛЬ:
- "A [style] illustration/artwork of [subject]"
- "rendered in [technique] style"
- "featuring [artistic elements]"

КОМПОЗИЦИЯ И ПОЗА:
- "dynamic [action/pose] composition"
- "positioned [location] in frame"
- "dramatic [angle/perspective]"

ДЕТАЛИ КОСТЮМА/ВНЕШНОСТИ:
- Конкретные элементы костюма или стиля
- Материалы и текстуры
- Цветовая палитра

АТМОСФЕРА И НАСТРОЕНИЕ:
- "intense atmosphere", "cinematic quality"
- "dramatic lighting effects"
- "dynamic composition"

ТЕХНИЧЕСКИЕ ХУДОЖЕСТВЕННЫЕ ПАРАМЕТРЫ:
- "ultra-realistic rendering"
- "highly detailed textures"
- "professional digital art quality"
- "concept art style"
- "cinematic lighting setup"

ПРИМЕР СТРУКТУРЫ:
"A [style] [artwork type] of [subject description], [pose/action], rendered in [technique]. The character features [detailed costume/appearance]. The composition shows [positioning] with [background description]. The lighting creates [atmosphere] with [specific effects]. The artwork demonstrates [technical quality] with [artistic style elements]."
"""
        
        return base_instructions + specific_instructions + """

ВАЖНЫЕ ПРАВИЛА:
1. ВСЕГДА переводи с русского на английский если нужно
2. Создавай ПОДРОБНОЕ описание (минимум 100-150 слов)
3. Используй КОНКРЕТНЫЕ фотографические/художественные термины
4. Включай ВСЕ технические детали (позиционирование, освещение, фокус, фон)
5. НЕ добавляй лишние комментарии - только финальный промпт

ОТВЕЧАЙ ТОЛЬКО финальным детальным промптом без дополнительного текста."""

    def _create_basic_detailed_prompt(self, user_prompt: str, avatar_type: str) -> str:
        """Создает базовый детальный промпт без GPT (fallback)"""
        
        # Переводим с русского если нужно (базовый словарь)
        translations = {
            "мужчина": "man", "женщина": "woman", "человек": "person",
            "портрет": "portrait", "деловой": "business", "костюм": "suit",
            "супергерой": "superhero", "фото": "photo", "художественный": "artistic"
        }
        
        prompt = user_prompt.lower()
        for ru, en in translations.items():
            prompt = prompt.replace(ru, en)
        
        if avatar_type == "portrait":
            return f"A high-quality portrait photograph of a {prompt}, centrally positioned in the frame, cropped at mid-torso, occupying 70% of the vertical space. The subject has natural skin tone with well-defined features and a neutral expression, gaze directed slightly toward camera. Professional studio lighting setup with soft, diffused illumination creating minimal shadows. The background is a smooth, neutral color that complements the subject. Shot with a slight telephoto effect at eye level, ensuring sharp focus on the subject against a gently blurred background, enhanced with professional post-processing for optimal clarity and detail."
        else:
            return f"A dynamic artistic illustration of {prompt}, professionally rendered in high-quality digital art style. The composition features dramatic positioning with cinematic lighting effects and intense atmosphere. The artwork demonstrates ultra-realistic rendering with highly detailed textures and professional concept art quality. Enhanced with cinematic lighting setup and dramatic color grading for maximum visual impact."

    async def _call_openai_api(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Вызывает OpenAI API для создания детального промпта"""
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = get_openai_headers(self.openai_api_key)
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Создай детальный профессиональный промпт для: {user_prompt}"}
            ],
            "temperature": 0.2,  # Очень низкая температура для стабильности
            "max_tokens": 500,   # Больше токенов для детальных описаний
            "top_p": 0.85
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        processed_prompt = result["choices"][0]["message"]["content"].strip()
                        
                        logger.info(f"Детальный промпт создан: '{user_prompt[:30]}...' → {len(processed_prompt)} символов")
                        return processed_prompt
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.exception(f"Ошибка вызова OpenAI API: {e}")
            return None
    
    def _detect_translation_needed(self, original: str, processed: str) -> bool:
        """Определяет, нужен ли был перевод"""
        
        # Ищем кириллические символы в оригинале
        has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in original)
        
        # Если в оригинале была кириллица, а в обработанном нет - был перевод
        has_cyrillic_processed = any('\u0400' <= char <= '\u04FF' for char in processed)
        
        return has_cyrillic and not has_cyrillic_processed
    
    def is_available(self) -> bool:
        """Проверяет доступность сервиса"""
        return bool(self.openai_api_key and self.openai_api_key != "test_key")
    
    def get_prompt_examples(self, avatar_type: str) -> list:
        """Возвращает примеры качественных промптов для пользователей"""
        
        if avatar_type == "portrait":
            return [
                "деловой портрет в костюме, студийное освещение",
                "casual фото в кофейне, теплый свет",
                "professional headshot, neutral background",
                "художественный портрет в стиле ренессанс"
            ]
        else:
            return [
                "супергерой в динамичной позе, город на фоне",
                "fantasy warrior, magical forest background",
                "cyberpunk character, neon city lights",
                "космонавт в скафандре, звезды на фоне"
            ] 

    def get_negative_prompt(self, avatar_type: str) -> str:
        """
        Создает негативный промпт для улучшения качества генерации.
        
        Особенно важно для исправления проблем с руками:
        - Деформированные руки
        - Лишние/недостающие пальцы  
        - Неестественные позы
        """
        # Базовые негативные термины для всех типов
        base_negative = [
            # Проблемы с руками и пальцами
            "deformed hands", "extra fingers", "missing fingers", "fused fingers",
            "too many fingers", "poorly drawn hands", "mutated hands", "long fingers",
            "twisted fingers", "curled fingers", "broken fingers", "extra thumbs",
            "missing thumbs", "malformed hands", "abnormal fingers", "floating fingers",
            
            # Анатомические проблемы
            "bad anatomy", "bad proportions", "extra limbs", "missing limbs",
            "deformed face", "mutated body", "asymmetrical face", "disproportionate body",
            "malformed limbs", "extra arms", "missing arms", "broken limbs",
            
            # Технические проблемы
            "blurry", "low quality", "jpeg artifacts", "watermark", "signature", 
            "text", "username", "error", "logo", "words", "letters", "digits",
            "autograph", "trademark", "name", "copyright", "web address",
            
            # Визуальные артефакты
            "noise", "grain", "pixelated", "distorted", "corrupted", "glitched",
            "overexposed", "underexposed", "oversaturated", "desaturated",
            "chromatic aberration", "lens flare", "vignette",
            
            # Проблемы с позами и композицией
            "awkward pose", "unnatural pose", "impossible pose", "broken perspective",
            "floating objects", "disconnected limbs", "overlapping bodies",
            "cut off limbs", "partial face", "cropped inappropriately"
        ]
        
        # Специфичные негативы для типов аватаров
        if avatar_type == "portrait":
            specific_negative = [
                "full body", "hands in frame", "fingers visible", "holding objects",
                "multiple people", "background focus", "landscape", "objects in hands",
                "hand gestures", "pointing", "waving", "touching face", "jewelry on hands"
            ]
        else:  # style avatars
            specific_negative = [
                "realistic hands", "detailed hands", "hand gestures", "pointing", 
                "waving", "cartoon style", "anime hands", "stylized fingers",
                "exaggerated proportions", "caricature", "comic book style"
            ]
        
        # Объединяем все негативы
        all_negatives = base_negative + specific_negative
        
        return ", ".join(all_negatives)

    def _add_negative_to_main_prompt(self, prompt: str, negative_terms: str) -> str:
        """
        Добавляет негативные термины в основной промпт для моделей FLUX Pro.
        Использует специальную конструкцию для указания нежелательных элементов.
        """
        # Формируем инструкцию избегания в конце промпта
        avoidance_instruction = f"[AVOID: {negative_terms}]"
        
        # Добавляем к основному промпту
        enhanced_prompt = f"{prompt.rstrip('.')}. {avoidance_instruction}"
        
        logger.info(f"[FLUX Pro] Добавлены негативные термины в основной промпт: {len(negative_terms)} символов")
        return enhanced_prompt

    def _needs_translation(self, prompt: str) -> bool:
        """Определяет, нужен ли перевод"""
        # Реализация метода _needs_translation
        return False  # Заглушка, реальная реализация должна быть реализована

    async def _translate_prompt(self, prompt: str) -> str:
        """Переводит промпт на английский"""
        # Реализация метода _translate_prompt
        return prompt  # Заглушка, реальная реализация должна быть реализована

    def _translate_to_english(self, text: str) -> str:
        """Переводит текст на английский"""
        # Реализация метода _translate_to_english
        return text  # Заглушка, реальная реализация должна быть реализована 