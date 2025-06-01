"""
Сервис обработки промптов для генерации изображений
Создает детальные, профессиональные промпты для максимального качества генерации
"""
import aiohttp
from typing import Optional

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
                
                return {
                    "original": user_prompt,
                    "processed": processed_prompt,
                    "negative_prompt": self.get_negative_prompt(avatar_type),
                    "translation_needed": translation_needed
                }
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
            return {
                "original": user_prompt,
                "processed": self._create_basic_detailed_prompt(user_prompt, avatar_type),
                "negative_prompt": self.get_negative_prompt(avatar_type),
                "translation_needed": False
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
        Создает отрицательный промпт для исправления проблем с руками, пальцами и анатомией
        
        Args:
            avatar_type: Тип аватара (portrait, style)
            
        Returns:
            str: Детальный отрицательный промпт
        """
        
        # Базовые проблемы для всех типов аватаров
        base_negative = [
            # Проблемы с руками и пальцами
            "deformed hands", "extra fingers", "missing fingers", "fused fingers", 
            "too many fingers", "poorly drawn hands", "mutated hands", "malformed hands",
            "extra hands", "missing hands", "floating hands", "disconnected hands",
            "long fingers", "thin fingers", "thick fingers", "bent fingers",
            "twisted fingers", "curled fingers", "overlapping fingers",
            
            # Проблемы с лицом и головой
            "deformed face", "disfigured face", "ugly face", "bad anatomy", 
            "poorly drawn face", "mutated face", "extra eyes", "missing eyes",
            "cropped head", "out of frame head", "tilted head", "floating head",
            "extra heads", "double face", "multiple faces",
            
            # Общие анатомические проблемы
            "bad proportions", "extra limbs", "missing limbs", "floating limbs",
            "disconnected limbs", "mutated body", "deformed body", "twisted body",
            "extra arms", "missing arms", "three arms", "four arms",
            "extra legs", "missing legs", "three legs",
            
            # Технические проблемы
            "blurry", "low quality", "worst quality", "jpeg artifacts", 
            "watermark", "signature", "text", "logo", "username",
            "duplicate", "morbid", "mutilated", "extra nipples",
            
            # Неестественные позы и композиция
            "awkward pose", "unnatural pose", "strange pose", "impossible pose",
            "broken perspective", "wrong perspective", "distorted perspective"
        ]
        
        if avatar_type == "portrait":
            # Дополнительные ограничения для портретов
            portrait_negative = [
                "full body", "whole body", "legs visible", "feet visible",
                "hands in frame", "fingers visible", "holding objects",
                "multiple people", "crowd", "group photo",
                "side view", "back view", "profile view extreme",
                "looking away from camera", "eyes closed", "sunglasses"
            ]
            
            all_negative = base_negative + portrait_negative
            
        else:  # style avatars
            # Дополнительные ограничения для стилевых аватаров  
            style_negative = [
                "realistic hands", "detailed hands", "visible hands",
                "hand gestures", "pointing", "waving", "holding",
                "cartoon style", "anime style", "chibi style",
                "low detail", "simple drawing", "sketch style"
            ]
            
            all_negative = base_negative + style_negative
        
        # Соединяем все элементы через запятую
        negative_prompt = ", ".join(all_negative)
        
        logger.info(f"Создан отрицательный промпт для {avatar_type}: {len(negative_prompt)} символов")
        return negative_prompt 