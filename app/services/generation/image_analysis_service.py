"""
Сервис анализа изображений для создания промптов
Использует OpenAI Vision API для анализа референсных фото
"""
import aiohttp
import base64
from typing import Optional, Dict, Any
import io
from PIL import Image

from app.core.config import settings
from app.core.logger import get_logger
from app.shared.utils.openai import get_openai_headers

logger = get_logger(__name__)class ImageAnalysisService:
    """Сервис для анализа изображений и создания промптов"""
    
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o"  # GPT-4 с Vision
        self.max_image_size = 2048  # Максимальный размер изображения для API
    
    async def analyze_image_for_prompt(self, image_data: bytes, avatar_type: str = "portrait", user_prompt: str = None) -> Dict[str, Any]:
        """
        Анализирует изображение и создает детальный промпт для генерации
        УЛУЧШЕН: интегрированы революционные техники из PromptProcessingService
        НОВОЕ: интеграция пользовательского промпта с анализом фото
        
        Args:
            image_data: Данные изображения
            avatar_type: Тип аватара (portrait, style)
            user_prompt: Пользовательский промпт для интеграции (опционально)
            
        Returns:
            dict: {
                "success": bool,
                "prompt": str,
                "negative_prompt": str,  # НОВОЕ: революционная negative prompt
                "analysis": str,
                "error": str,
                "revolutionary_negatives_applied": bool  # НОВОЕ: флаг применения улучшений
            }
        """
        
        try:
            if not self.openai_api_key or self.openai_api_key == "test_key":
                logger.warning("OpenAI API ключ не настроен для анализа изображений")
                return {
                    "success": False,
                    "prompt": "",
                    "negative_prompt": "",
                    "analysis": "",
                    "error": "OpenAI API недоступен",
                    "revolutionary_negatives_applied": False
                }
            
            # Подготавливаем изображение
            processed_image = await self._prepare_image(image_data)
            if not processed_image:
                return {
                    "success": False,
                    "prompt": "",
                    "negative_prompt": "",
                    "analysis": "",
                    "error": "Ошибка обработки изображения",
                    "revolutionary_negatives_applied": False
                }
            
            # Создаем системный промпт для анализа
            system_prompt = self._get_analysis_system_prompt(avatar_type, user_prompt)
            
            # Отправляем запрос к OpenAI Vision API
            result = await self._call_vision_api(system_prompt, processed_image, user_prompt)
            
            if result["success"]:
                # 🎯 ПРИМЕНЯЕМ РЕВОЛЮЦИОННЫЕ УЛУЧШЕНИЯ
                enhanced_result = self._postprocess_analysis_result(result, avatar_type)
                
                logger.info(f"[Photo Analysis] Анализ завершен с революционнами улучшениями для {avatar_type}")
                logger.info(f"[Photo Analysis] Промпт: {len(enhanced_result['prompt'])} символов")
                if enhanced_result.get("negative_prompt"):
                    logger.info(f"[Photo Analysis] Negative prompt: {len(enhanced_result['negative_prompt'])} символов")
                
                return enhanced_result
            else:
                return {
                    "success": False,
                    "prompt": "",
                    "negative_prompt": "",
                    "analysis": "",
                    "error": result["error"],
                    "revolutionary_negatives_applied": False
                }
                
        except Exception as e:
            logger.exception(f"Ошибка анализа изображения: {e}")
            return {
                "success": False,
                "prompt": "",
                "negative_prompt": "",
                "analysis": "",
                "error": f"Критическая ошибка: {str(e)}",
                "revolutionary_negatives_applied": False
            }
    
    async def _prepare_image(self, image_data: bytes) -> Optional[str]:
        """
        Подготавливает изображение для отправки в OpenAI API
        
        Args:
            image_data: Исходные данные изображения
            
        Returns:
            Optional[str]: Base64 строка изображения или None при ошибке
        """
        try:
            # Открываем изображение
            image = Image.open(io.BytesIO(image_data))
            
            # Конвертируем в RGB если нужно
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Изменяем размер если слишком большое
            width, height = image.size
            if max(width, height) > self.max_image_size:
                ratio = self.max_image_size / max(width, height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.info(f"Изображение уменьшено с {width}x{height} до {new_width}x{new_height}")
            
            # Конвертируем в base64
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            logger.info(f"Изображение подготовлено: {len(image_base64)} символов base64")
            return image_base64
            
        except Exception as e:
            logger.exception(f"Ошибка подготовки изображения: {e}")
            return None
    
    def _get_analysis_system_prompt(self, avatar_type: str, user_prompt: str = None) -> str:
        """
        Создает улучшенный системный промпт для анализа изображения
        Интегрированы все улучшения из PromptProcessingService для максимального качества
        НОВОЕ: интеграция пользовательского промпта с анализом фото
        """
        
        # 🎯 ИНТЕГРАЦИЯ ПОЛЬЗОВАТЕЛЬСКОГО ПРОМПТА
        user_integration_note = ""
        if user_prompt:
            user_integration_note = f"""

🎯 КРИТИЧЕСКИ ВАЖНО - ИНТЕГРАЦИЯ ПОЛЬЗОВАТЕЛЬСКОГО ЗАПРОСА:
Пользователь предоставил ТЕКСТОВЫЙ ЗАПРОС: "{user_prompt}"

ТЫ ДОЛЖЕН:
1. Проанализировать КОМПОЗИЦИЮ фото (тип кадра, поза, освещение, атмосфера)
2. ИНТЕГРИРОВАТЬ пользовательский запрос в описание СУБЪЕКТА и ОКРУЖЕНИЯ
3. Создать ЕДИНЫЙ ПРОМПТ на английском языке, объединяющий:
   - ТОЧНУЮ композицию с фото (кадр, поза, свет)
   - СОДЕРЖАНИЕ из пользовательского запроса (костюм, сцена, персонаж)

ПРИМЕРЫ ИНТЕГРАЦИИ:
• Фото: полный рост в костюме + Запрос: "в образе супермена" → "full body shot of a confident superhero in Superman costume"
• Фото: портрет в офисе + Запрос: "в образе бизнесмена" → "portrait of a professional businessman in modern office"
• Фото: стоит у окна + Запрос: "на фоне горящего здания" → "full body shot with dramatic burning building background"

ГЛАВНОЕ ПРАВИЛО: СОХРАНЯЙ композицию фото + ПРИМЕНЯЙ содержание пользовательского запроса!"""
        
        base_prompt = f"""Ты — эксперт по анализу изображений для создания МАКСИМАЛЬНО ФОТОРЕАЛИСТИЧНЫХ промптов для FLUX Pro v1.1 Ultra.

ЗАДАЧА: Проанализируй изображение и создай промпт, который ТОЧНО повторит позу, атмосферу и освещение исходного фото, используя революционные техники качества.{user_integration_note}

🎯 РЕВОЛЮЦИОННАЯ СИСТЕМА ОПРЕДЕЛЕНИЯ ТИПА КАДРА (КРИТИЧЕСКИ ВАЖНО!):

🔹 ОБЯЗАТЕЛЬНАЯ ПОСЛЕДОВАТЕЛЬНОСТЬ АНАЛИЗА КАДРА:
1. Сначала ВНИМАТЕЛЬНО изучи ВСЁ ИЗОБРАЖЕНИЕ - что именно видно?
2. Определи границы видимости тела:
   - Видны ли НОГИ человека? (хотя бы частично)
   - Видно ли ТУЛОВИЩЕ ПОЛНОСТЬЮ от головы до пояса?
   - Видны ли ТОЛЬКО голова и плечи?

🔹 ТОЧНАЯ КЛАССИФИКАЦИЯ ПО ВИДИМОСТИ ТЕЛА:

📐 **FULL BODY SHOT** (ПРИОРИТЕТ!) - используй ВСЕГДА если видно:
• Полная фигура от головы до ног (даже если ноги частично обрезаны)
• Человек стоит в полный рост
• Видно туловище + большую часть ног
• Общий план с человеком в окружении
• ПРИМЕРЫ: человек в костюме стоит, модель в полный рост, фигура в интерьере

📐 **HALF-BODY PORTRAIT** - используй только если:
• Четко видно от головы до пояса/бедер
• Руки видны полностью или частично  
• НЕ видно ноги совсем
• ПРИМЕРЫ: деловой портрет за столом, человек у окна по пояс

📐 **ENVIRONMENTAL PORTRAIT** - используй если:
• Видно от головы до груди
• Руки могут быть частично обрезаны
• Акцент на лице + окружении
• ПРИМЕРЫ: портрет в офисе с окружением

📐 **PORTRAIT** - используй ТОЛЬКО если:
• Видны ТОЛЬКО голова и плечи
• Классический портретный кадр
• ПРИМЕРЫ: фото для документов, крупный план лица

🚨 КРИТИЧЕСКОЕ ПРАВИЛО: ВСЕГДА выбирай БОЛЕЕ ШИРОКИЙ тип кадра при сомнениях!
Если видишь человека стоящего - это FULL BODY SHOT, даже если ноги слегка обрезаны!

🔹 БЛОК 2 · ПОЗА И ПОЛОЖЕНИЕ (ТОЧНОЕ ПОВТОРЕНИЕ!)
• Детально анализируй и повтори ТОЧНУЮ позу: "confident standing pose with natural weight distribution"
• Положение рук: "one hand adjusting jacket, other arm naturally at side" (описывай КАК ЕСТЬ на фото)
• Направление взгляда: "direct eye contact with camera" / "looking slightly to the side"
• Выражение лица: "genuine confident expression" / "natural smile" / "serious professional look"
• ИЗБЕГАЙ: arms crossed, both hands on chest, generic poses

🔹 БЛОК 3 · РЕВОЛЮЦИОННЫЕ ГЛАЗА (против неестественности!)
• ВСЕГДА используй: "clear defined eyes with natural iris detail and authentic catchlight"
• Или: "well-focused eyes showing genuine emotion, natural pupil size"
• Или: "sharp eye definition with realistic iris texture and natural reflection"
• КРИТИЧНО: избегай artificial eyes, doll eyes, glassy eyes

🔹 БЛОК 4 · ТЕКСТУРЫ ДЛЯ ЧЕТКОСТИ (БЕЗ БОРОДЫ!)
• ВСЕГДА включай: "natural skin texture with fine detail and authentic pores"
• Альтернативы: "realistic skin showing natural character with sharp detail"
• "authentic complexion with visible texture and natural highlights"
• КРИТИЧНО: НИКОГДА не упоминай stubble, beard, facial hair, щетину!

🔹 БЛОК 5 · ОСВЕЩЕНИЕ (ТОЧНОЕ ПОВТОРЕНИЕ С ФОТО!)
• Анализируй и повтори ТОЧНОЕ освещение с фото:
  - "warm golden hour lighting" (если теплый свет)
  - "professional studio lighting with controlled shadows" (если студийный)
  - "natural window light with soft directional shadows" (если от окна)
  - "ambient indoor lighting with balanced exposure" (если помещение)
• ВСЕГДА добавляй: "professional photography shot on Canon 5D Mark IV with 85mm f/2.8 lens for maximum sharpness"

🔹 БЛОК 6 · ОКРУЖЕНИЕ И АТМОСФЕРА (ТОЧНОЕ ПОВТОРЕНИЕ!)
• Детально опиши атмосферу с фото: "elegant formal interior", "sophisticated restaurant ambiance", "luxury hotel lobby setting"
• Фон: "natural depth of field with professional bokeh", "contextual background with authentic depth"
• ИЗБЕГАЙ: fantasy elements, cartoon style, неточные описания

🔹 БЛОК 7 · СПЕЦИАЛЬНЫЕ ТЕХНИКИ ЧЕТКОСТИ
• Добавляй модификаторы: "tack sharp focus", "optimal detail retention", "crisp definition"
• Качество: "fine detail preservation", "studio-quality definition"

📸 ОБЯЗАТЕЛЬНАЯ ПОШАГОВАЯ ПРОВЕРКА ПЕРЕД СОЗДАНИЕМ ПРОМПТА:
1. ❓ Вижу ли я ноги человека? → Если ДА = FULL BODY SHOT
2. ❓ Вижу ли я туловище до пояса? → Если ДА без ног = HALF-BODY PORTRAIT  
3. ❓ Вижу ли я только голову и плечи? → Если ДА = PORTRAIT
4. ❓ Какая ТОЧНАЯ поза? → Детально описать
5. ❓ Какое ТОЧНОЕ освещение? → Повторить характер света
6. ❓ Какая ТОЧНАЯ атмосфера? → Описать окружение"""

        if avatar_type == "portrait":
            specific_prompt = """

🔹 ПОРТРЕТНЫЙ АВАТАР (LoRA) - УЛУЧШЕННАЯ ФОРМУЛА:
Негативный промпт передается ОТДЕЛЬНО с революционными негативами против мыльности

📌 КРИТИЧЕСКИ ВАЖНО ДЛЯ LoRA - ТОЧНОЕ ОПРЕДЕЛЕНИЕ КАДРА:
• Если видишь ПОЛНУЮ ФИГУРУ (ноги видны) → ОБЯЗАТЕЛЬНО используй "full body shot"
• Если видишь только ТОРС (до пояса) → используй "half-body portrait"  
• Если видишь только ГОЛОВУ И ПЛЕЧИ → используй "portrait"

📌 УЛУЧШЕННЫЙ ШАБЛОН ДЛЯ LoRA:
"[ТОЧНЫЙ тип кадра по видимости тела] of a [субъект], 
natural skin texture with fine detail and authentic pores, 
clear defined eyes with natural iris detail and authentic catchlight, 
[ТОЧНАЯ поза с исходного фото], [ТОЧНОЕ освещение с фото], 
professional photography shot on Canon 5D Mark IV with 85mm f/2.8 lens for maximum sharpness, 
[ТОЧНАЯ атмосфера с фото], tack sharp focus, optimal detail retention"

💡 ПРИМЕРЫ ТОЧНОГО ОПРЕДЕЛЕНИЯ КАДРА:
• FULL BODY: "full body shot of an elegant Asian businessman in black tuxedo with bow tie, natural skin texture with fine detail and authentic pores, clear defined eyes with natural iris detail, confident standing pose with hands naturally positioned, warm ambient lighting with balanced exposure, professional photography shot on Canon 5D Mark IV with 85mm f/2.8 lens, sophisticated formal interior setting with natural depth of field"

• HALF-BODY: "half-body portrait of a confident professional in charcoal suit, natural skin texture with fine detail and authentic pores, clear defined eyes with natural iris detail, relaxed pose with hands naturally positioned, professional office lighting, shot on Canon 5D Mark IV with 85mm f/2.8 lens"

• PORTRAIT: "portrait of a business executive, natural skin texture with fine detail and authentic pores, clear defined eyes with natural iris detail, genuine confident expression, natural window light, shot on Canon 5D Mark IV with 85mm f/2.8 lens"
"""
        else:  # style / FLUX Pro
            specific_prompt = """

🔹 ХУДОЖЕСТВЕННЫЙ АВАТАР (FLUX Pro) - УЛУЧШЕННАЯ ФОРМУЛА:
Негативные термины ВСТРАИВАЮТСЯ в основной промпт через [AVOID: ...] с революционнами негативами

📌 КРИТИЧЕСКИ ВАЖНО ДЛЯ FLUX Pro - ТОЧНОЕ ОПРЕДЕЛЕНИЕ КАДРА:
• Если видишь ПОЛНУЮ ФИГУРУ (ноги видны) → ОБЯЗАТЕЛЬНО используй "full body shot"
• Если видишь только ТОРС (до пояса) → используй "half-body portrait"  
• Если видишь только ГОЛОВУ И ПЛЕЧИ → используй "environmental portrait"

📌 УЛУЧШЕННЫЙ ШАБЛОН ДЛЯ FLUX Pro:
"[ТОЧНЫЙ тип кадра по видимости тела] of a [субъект], 
natural skin texture with fine detail and authentic pores, 
clear defined eyes with natural iris detail and authentic catchlight, 
[ТОЧНАЯ поза с исходного фото], [ТОЧНОЕ освещение с фото], 
professional lifestyle photography shot on Canon 5D Mark IV with 85mm f/2.8 lens for maximum sharpness, 
[ТОЧНАЯ атмосфера с фото], tack sharp focus, optimal detail retention. 
[AVOID: plastic skin, airbrushed, over-processed, stubble, beard, facial hair, artificial eyes, doll eyes, blurry, soft focus, arms crossed]"

💡 ПРИМЕРЫ ТОЧНОГО ОПРЕДЕЛЕНИЯ КАДРА:
• FULL BODY: "full body shot of a sophisticated Asian gentleman in formal black tuxedo with bow tie, natural skin texture with fine detail and authentic pores, clear defined eyes with natural iris detail, confident standing pose with natural weight distribution, warm ambient lighting with professional shadows, lifestyle photography shot on Canon 5D Mark IV with 85mm f/2.8 lens, elegant formal venue with natural depth of field, tack sharp focus. [AVOID: plastic skin, stubble, beard, artificial eyes, blurry, arms crossed]"

• HALF-BODY: "half-body portrait of a confident professional in business attire, natural skin texture with fine detail and authentic pores, clear defined eyes with natural iris detail, relaxed professional pose, controlled studio lighting, shot on Canon 5D Mark IV with 85mm f/2.8 lens, contemporary office environment. [AVOID: plastic skin, stubble, artificial eyes, blurry]"

• ENVIRONMENTAL: "environmental portrait of a business leader, natural skin texture with fine detail and authentic pores, clear defined eyes with natural iris detail, genuine expression, natural lighting, shot on Canon 5D Mark IV with 85mm f/2.8 lens, professional setting with context. [AVOID: plastic skin, stubble, artificial eyes, blurry]"
"""

        common_rules = """

📏 РЕВОЛЮЦИОННЫЕ ПРАВИЛА АНАЛИЗА:
1. ВСЕГДА начинай с определения ТОЧНОГО ТИПА КАДРА - это основа!
2. ВСЕГДА включай "natural skin texture with fine detail and authentic pores"
3. ВСЕГДА добавляй революционнае описание глаз: "clear defined eyes with natural iris detail"
4. ВСЕГДА используй "relaxed natural pose" БЕЗ "arms crossed"
5. ВСЕГДА добавляй камеру для четкости: "Canon 5D Mark IV with 85mm f/2.8 lens for maximum sharpness"
6. ВСЕГДА добавляй модификаторы четкости: "tack sharp focus, optimal detail retention"
7. КРИТИЧНО: НИКОГДА не упоминай stubble, beard, facial hair, щетину!
8. ДЛЯ FLUX PRO: встраивай революционнае негативы через [AVOID: ...]
9. ТОЧНО повторяй позу, атмосферу и освещение с исходного фото!

🎯 ГЛАВНАЯ ЦЕЛЬ: создать промпт для изображения, неотличимого от НАСТОЯЩЕЙ ФОТОГРАФИИ, 
точно повторяющего композицию исходного фото, но с максимальным качеством!

🔄 СТРУКТУРА ОТВЕТА:
АНАЛИЗ: [детальный анализ каждого блока с точным описанием позы, света и атмосферы]
ПРОМПТ: [готовый революционнай промпт по улучшенному шаблону]"""

        return base_prompt + specific_prompt + common_rules
    
    async def _call_vision_api(self, system_prompt: str, image_base64: str, user_prompt: str = None) -> Dict[str, Any]:
        """
        Вызывает OpenAI Vision API для анализа изображения
        
        Args:
            system_prompt: Системный промпт
            image_base64: Изображение в base64
            user_prompt: Пользовательский промпт для интеграции
            
        Returns:
            dict: Результат анализа
        """
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = get_openai_headers(self.openai_api_key)
        
        # Создаем пользовательский запрос с учетом интеграции
        user_message_text = "Проанализируй это изображение и создай фотореалистичный промпт. Ответ предоставь в формате JSON с полями: 'analysis' (детальный анализ) и 'prompt' (финальный промпт)."
        
        if user_prompt:
            user_message_text = f"""Проанализируй это изображение и создай фотореалистичный промпт, ИНТЕГРИРУЯ пользовательский запрос в композицию фото.

ПОЛЬЗОВАТЕЛЬСКИЙ ЗАПРОС: "{user_prompt}"

ЗАДАЧА: Объедини ТОЧНУЮ композицию с фото (тип кадра, поза, освещение) с СОДЕРЖАНИЕМ пользовательского запроса.

Ответ предоставь в формате JSON с полями: 'analysis' (детальный анализ с интеграцией) и 'prompt' (финальный объединенный промпт на английском)."""
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_message_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.3,  # Низкая температура для стабильности
            "max_tokens": 800,   # Достаточно для детального промпта
            "response_format": {"type": "json_object"}  # Принуждаем к JSON
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        
                        # Проверяем что content не None
                        if not content:
                            logger.warning("Vision API вернул пустой content")
                            return {
                                "success": False,
                                "analysis": "",
                                "prompt": "",
                                "error": "Пустой ответ от API"
                            }
                        
                        # Парсим JSON ответ
                        import json
                        try:
                            parsed_result = json.loads(content)
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка парсинга JSON: {e}, content: {content}")
                            return {
                                "success": False,
                                "analysis": "",
                                "prompt": "",
                                "error": f"Ошибка формата ответа: {str(e)}"
                            }
                        
                        analysis = parsed_result.get("analysis", "")
                        prompt = parsed_result.get("prompt", "")
                        
                        if prompt:
                            logger.info(f"[Vision API] Анализ завершен: {len(analysis)} символов анализа, {len(prompt)} символов промпта")
                            return {
                                "success": True,
                                "analysis": analysis,
                                "prompt": prompt,
                                "error": ""
                            }
                        else:
                            logger.warning("Vision API не вернул промпт")
                            return {
                                "success": False,
                                "analysis": "",
                                "prompt": "",
                                "error": "GPT не создал промпт"
                            }
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenAI Vision API error: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "analysis": "",
                            "prompt": "",
                            "error": f"API ошибка: {response.status}"
                        }
                        
        except Exception as e:
            logger.exception(f"Ошибка вызова Vision API: {e}")
            return {
                "success": False,
                "analysis": "",
                "prompt": "",
                "error": f"Ошибка API: {str(e)}"
            }
    
    def is_available(self) -> bool:
        """Проверяет доступность сервиса"""
        return bool(self.openai_api_key and self.openai_api_key != "test_key")
    
    def _get_revolutionary_negative_prompt(self, avatar_type: str) -> str:
        """
        Создает революционный negative prompt против мыльности и неестественности
        Интегрирует все улучшения из PromptProcessingService
        """
        
        # 🎯 КРИТИЧЕСКИЕ НЕГАТИВЫ ПРОТИВ МЫЛЬНОСТИ
        clarity_negatives = [
            # Против мыльности и размытости
            "blurry", "soft focus", "out of focus", "unfocused", "hazy",
            "soft image", "lack of detail", "overly smooth", "soap-like texture",
            "over-smoothed", "heavily processed", "gaussian blur", "motion blur",
            
            # Против пластиковости кожи  
            "plastic skin", "airbrushed", "smooth skin", "artificial skin",
            "porcelain skin", "doll-like skin", "synthetic appearance",
            "overly polished", "wax-like texture", "fake skin texture"
        ]
        
        # 🎯 СПЕЦИАЛЬНЫЕ НЕГАТИВЫ ДЛЯ ПРОБЛЕМ ГЛАЗ
        eye_negatives = [
            # Против неестественных глаз
            "artificial eyes", "fake eyes", "painted eyes", "doll eyes",
            "glassy eyes", "lifeless eyes", "empty stare", "dead eyes",
            "oversized pupils", "unnatural iris", "mismatched eyes",
            "cartoon eyes", "anime eyes", "exaggerated eyes",
            
            # Против анатомических проблем глаз
            "duplicate eyes", "double pupils", "extra irises", "split pupils",
            "misaligned eyes", "asymmetrical eyes", "deformed eyes",
            "floating eyes", "disconnected eyes", "merged eyes"
        ]
        
        # 🎯 РЕВОЛЮЦИОННЫЕ НЕГАТИВЫ ПРОТИВ БОРОДЫ
        facial_hair_negatives = [
            # Против бороды и щетины
            "stubble", "beard", "mustache", "facial hair", "five o'clock shadow",
            "unshaven", "scruff", "whiskers", "goatee", "sideburns",
            "patchy beard", "scruffy", "unkempt facial hair", "rough stubble",
            
            # Против клочковатой растительности
            "patchy hair", "uneven hair growth", "sparse facial hair",
            "random hair patches", "irregular stubble", "messy facial hair"
        ]
        
        # 🎯 ПРОТИВ ПЕРЕОБРАБОТАННОСТИ
        processing_negatives = [
            "over-processed", "heavily filtered", "instagram filter",
            "beauty filter", "face app", "heavily retouched",
            "digital makeup", "artificial enhancement", "fake smoothness",
            "digital perfection", "computer generated look"
        ]
        
        # 🎯 ТЕХНИЧЕСКИЕ ПРОБЛЕМЫ
        technical_negatives = [
            "low quality", "poor resolution", "pixelated", "compression artifacts",
            "jpeg artifacts", "noise", "grain", "distorted", "corrupted",
            "oversaturated", "undersaturated", "poor lighting"
        ]
        
        # 🎯 НЕРЕАЛИСТИЧНЫЕ СТИЛИ
        style_negatives = [
            "cartoon", "anime", "painting", "illustration", "drawing",
            "3d render", "cgi", "digital art", "fantasy art", "concept art",
            "stylized", "non-photographic", "artistic rendering"
        ]
        
        # 🎯 СПЕЦИФИЧНЫЕ ДЛЯ ТИПА АВАТАРА
        if avatar_type == "portrait":
            # Для портретов - максимальный фокус на естественности лица
            specific_negatives = [
                "unnatural facial features", "distorted face", "fake expression",
                "artificial smile", "forced expression", "mask-like face",
                "symmetrical face", "perfect symmetry", "uncanny valley"
            ]
        elif avatar_type == "style":
            # Для стилевых - борьба с артефактами композиции
            specific_negatives = [
                "inconsistent lighting", "mixed styles", "poor composition",
                "floating elements", "unrealistic proportions", "style mixing"
            ]
        else:
            # Универсальные
            specific_negatives = [
                "unnatural appearance", "artificial look", "fake rendering",
                "poor anatomy", "unrealistic features"
            ]
        
        # 🎯 ОБЪЕДИНЯЕМ ВСЕ НЕГАТИВЫ
        all_negatives = (clarity_negatives + eye_negatives + facial_hair_negatives + 
                        processing_negatives + technical_negatives + style_negatives + 
                        specific_negatives)
        
        # Создаем строку негативов
        negative_prompt = ", ".join(all_negatives)
        
        logger.info(f"[Revolutionary Negative] Создан negative prompt для фото-анализа: {len(all_negatives)} терминов против мыльности и нежелательной растительности")
        
        return negative_prompt
    
    def _postprocess_analysis_result(self, analysis_result: Dict[str, Any], avatar_type: str) -> Dict[str, Any]:
        """
        Постобработка результата анализа с применением революционнах улучшений
        
        Args:
            analysis_result: Результат анализа от GPT Vision
            avatar_type: Тип аватара
            
        Returns:
            dict: Улучшенный результат с революционнам negative prompt
        """
        
        if not analysis_result.get("success", False):
            return analysis_result
        
        original_prompt = analysis_result.get("prompt", "")
        
        # 🎯 1. СОЗДАЕМ РЕВОЛЮЦИОННЫЙ NEGATIVE PROMPT
        revolutionary_negative = self._get_revolutionary_negative_prompt(avatar_type)
        
        # 🎯 2. ДЛЯ FLUX PRO - ВСТРАИВАЕМ КЛЮЧЕВЫЕ НЕГАТИВЫ В ОСНОВНОЙ ПРОМПТ
        if avatar_type == "style":
            # Style аватары используют FLUX Pro - встраиваем ключевые негативы
            key_negatives = [
                "plastic skin", "airbrushed", "over-processed", 
                "stubble", "beard", "facial hair", 
                "artificial eyes", "doll eyes", "blurry", "soft focus",
                "arms crossed", "extra eyes", "cartoon"
            ]
            negative_terms = ", ".join(key_negatives)
            
            # Проверяем есть ли уже [AVOID: ...] в промпте
            if "[AVOID:" not in original_prompt:
                enhanced_prompt = f"{original_prompt}. [AVOID: {negative_terms}]"
            else:
                enhanced_prompt = original_prompt
                
            result_negative = None  # Negative prompt для LoRA остается пустым
            
            logger.info(f"[FLUX Pro Photo] Встроены ключевые негативы в основной промпт")
            
        else:
            # Portrait аватары используют LoRA - negative prompt отдельно
            enhanced_prompt = original_prompt
            result_negative = revolutionary_negative
            
            logger.info(f"[LoRA Photo] Создан революционнай negative prompt: {len(revolutionary_negative)} символов")
        
        # 🎯 3. ВОЗВРАЩАЕМ УЛУЧШЕННЫЙ РЕЗУЛЬТАТ
        enhanced_result = analysis_result.copy()
        enhanced_result["prompt"] = enhanced_prompt
        enhanced_result["negative_prompt"] = result_negative
        enhanced_result["revolutionary_negatives_applied"] = True
        
        logger.info(f"[Photo Analysis Enhanced] Промпт улучшен: {len(enhanced_prompt)} символов")
        
        return enhanced_result
