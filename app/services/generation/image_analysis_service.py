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
from .cinematic_prompt_service import CinematicPromptService

logger = get_logger(__name__)


class ImageAnalysisService:
    """Сервис для анализа изображений и создания промптов"""
    
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o"  # GPT-4 с Vision
        self.max_image_size = 2048  # Максимальный размер изображения для API
        self.cinematic_service = CinematicPromptService()
    
    async def analyze_image_for_prompt(
        self, 
        image_data: bytes, 
        avatar_type: str = "portrait",
        user_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Анализирует изображение и создает кинематографический промпт
        
        Args:
            image_data: Данные изображения
            avatar_type: Тип аватара ("portrait")
            user_prompt: Дополнительный промпт от пользователя для интеграции
            
        Returns:
            Dict с анализом и готовым промптом
        """
        try:
            logger.info(f"[Image Analysis] Начат анализ изображения ({len(image_data)} байт)")
            
            if not self.openai_api_key:
                logger.warning("[Image Analysis] Нет API ключа OpenAI, используем базовый промпт")
                return await self._fallback_analysis(user_prompt, avatar_type)
            
            # 1. Подготавливаем изображение
            processed_image = await self._prepare_image(image_data)
            if not processed_image:
                return await self._fallback_analysis(user_prompt, avatar_type)
            
            # 2. Кодируем в base64
            image_base64 = base64.b64encode(processed_image).decode('utf-8')
            
            # 3. Создаем системный промпт для анализа
            system_prompt = self._create_cinematic_analysis_prompt(avatar_type, user_prompt)
            
            # 4. Анализируем изображение через GPT Vision
            analysis_result = await self._call_vision_api(system_prompt, image_base64, user_prompt)
            
            if not analysis_result or not analysis_result.get("prompt"):
                logger.warning("[Image Analysis] Нет результата от Vision API, используем fallback")
                return await self._fallback_analysis(user_prompt, avatar_type)
            
            # 5. Создаем кинематографический промпт на базе анализа
            base_description = analysis_result.get("analysis", "")
            vision_prompt = analysis_result.get("prompt", "")
            
            # Интегрируем пользовательский промпт если есть
            if user_prompt:
                integrated_prompt = f"{vision_prompt}, {user_prompt}"
            else:
                integrated_prompt = vision_prompt
            
            # 6. Применяем кинематографические улучшения
            cinematic_result = await self.cinematic_service.create_cinematic_prompt(
                user_prompt=integrated_prompt,
                avatar_type=avatar_type,
                style_preset="photorealistic"
            )
            
            logger.info(f"[Image Analysis] Создан кинематографический промпт: {len(cinematic_result['processed'])} символов")
            
            return {
                "analysis": base_description,
                "prompt": cinematic_result["processed"],
                "original_vision_prompt": vision_prompt,
                "cinematic_enhancement": cinematic_result.get("enhancement_applied", False),
                "user_prompt_integrated": bool(user_prompt),
                "style": "cinematic_photorealistic"
            }
                
        except Exception as e:
            logger.exception(f"[Image Analysis] Ошибка анализа: {e}")
            return await self._fallback_analysis(user_prompt, avatar_type)
    
    def _create_cinematic_analysis_prompt(self, avatar_type: str, user_prompt: str = None) -> str:
        """Создает системный промпт для кинематографического анализа"""
        
        user_integration = ""
        if user_prompt:
            user_integration = f"""
🎯 ИНТЕГРАЦИЯ ПОЛЬЗОВАТЕЛЬСКОГО ЗАПРОСА:
Пользователь добавил текстовый запрос: "{user_prompt}"

ВАЖНО: Объедини визуальную композицию фото с содержанием пользовательского запроса.
- СОХРАНЯЙ: тип кадра, позу, освещение, атмосферу с фото
- ИНТЕГРИРУЙ: содержание запроса (костюм, сцена, персонаж, стиль)"""
        
        return f"""Ты эксперт по анализу изображений для создания КИНЕМАТОГРАФИЧЕСКИХ промптов в стиле профессиональной фотографии 8K качества.

ЗАДАЧА: Проанализируй изображение и создай промпт в стиле ваших примеров с максимальной детализацией.{user_integration}

🎬 СТИЛЬ ПРОМПТА (как в примерах):
Должен включать ВСЕ элементы:
1. **Технические характеристики**: "high-quality, cinematic, ultra-realistic", "8K resolution", "professional camera"
2. **Тип кадра**: "close-up portrait"/"full-body portrait"/"medium portrait" 
3. **Освещение**: "warm directional side lighting during golden hour" / "professional studio lighting"
4. **Композицию**: "expertly framed with subject positioned centrally"
5. **Детальное описание субъекта**: внешность, одежда, стиль, выражение
6. **Позу и ракурс**: точное описание положения тела, взгляда, жестов
7. **Окружение**: детальное описание фона, атмосферы, контекста
8. **Технические параметры**: "shot with 85mm lens", "depth of field", "razor-sharp focus"
9. **Цветовую палитру**: "rich warm tones, deep golds, luxurious ambers"
10. **Качество**: "natural skin texture", "well-defined eyes", "authentic detail"

📐 ОПРЕДЕЛЕНИЕ ТИПА КАДРА (КРИТИЧЕСКИ ВАЖНО):
- Видны ли ноги человека? → FULL-BODY PORTRAIT
- Видно туловище до пояса? → HALF-BODY PORTRAIT  
- Только голова и плечи? → CLOSE-UP PORTRAIT

🔍 АНАЛИЗ ПО БЛОКАМ:

**КОМПОЗИЦИЯ И КАДР:**
- Какой точно тип кадра (полный рост/по пояс/крупный план)?
- Как расположен субъект в кадре?
- Углы съемки и перспектива

**ОСВЕЩЕНИЕ:**
- Тип освещения (студийное/естественное/золотой час/драматическое)
- Направление света и тени
- Атмосфера и настроение

**СУБЪЕКТ:**
- Детальное описание внешности
- Одежда и стиль (цвета, фактуры, детали)
- Выражение лица и эмоции

**ПОЗА И ЯЗЫК ТЕЛА:**
- Точное положение тела
- Направление взгляда
- Жесты и положение рук

**ОКРУЖЕНИЕ:**
- Детальное описание фона
- Контекст и локация
- Элементы интерьера/экстерьера

**ТЕХНИЧЕСКИЕ ДЕТАЛИ:**
- Глубина резкости
- Фокусировка
- Качество изображения

ФОРМАТ ОТВЕТА JSON:
```json
{{
  "analysis": "Детальный анализ каждого блока композиции",
  "prompt": "Готовый кинематографический промпт в стиле примеров"
}}
```

ПРИМЕР СТИЛЯ ПРОМПТА:
"A high-quality, cinematic, ultra-realistic close-up portrait photograph, captured by professional medium-format digital camera, in style of super-detailed 8K resolution imagery, featuring warm directional side lighting during golden hour. The composition is expertly framed with subject positioned centrally, featuring a confident man with contemporary styling, positioned with natural elegance and authentic body language, gazing directly at camera with engaging intensity. Set in sophisticated modern environment with clean architectural lines, captured by professional medium-format digital camera, shot with 85mm portrait lens at f/2.8 for optimal sharpness, The depth of field is exceptional ensuring razor-sharp focus on subject, professional bokeh with smooth background transition. The color palette emphasizes rich warm tones and deep golds creating sophisticated atmospheric mood, well-defined eyes with natural catchlight and authentic iris detail, natural skin texture with fine detail and visible pores, sharp focus with optimal detail retention, high-end editorial photography style with cinematic quality."

Создай промпт ТОЧНО в таком стиле с максимальной детализацией!"""
    
    async def _prepare_image(self, image_data: bytes) -> Optional[bytes]:
        """Подготавливает изображение для анализа"""
        try:
            # Открываем изображение
            image = Image.open(io.BytesIO(image_data))
            
            # Конвертируем в RGB если нужно
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Изменяем размер если нужно
            if max(image.size) > self.max_image_size:
                ratio = self.max_image_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"[Image Analysis] Изображение изменено до {new_size}")
            
            # Сохраняем в байты
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"[Image Analysis] Ошибка подготовки изображения: {e}")
            return None
    
    async def _call_vision_api(self, system_prompt: str, image_base64: str, user_prompt: str = None) -> Dict[str, Any]:
        """Вызывает OpenAI Vision API"""
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = get_openai_headers(self.openai_api_key)
            
            user_message_text = "Проанализируй это изображение и создай кинематографический промпт в стиле примеров. Ответ в JSON формате."
            if user_prompt:
                user_message_text = f"""Проанализируй изображение и создай кинематографический промпт, ИНТЕГРИРУЯ пользовательский запрос.

ПОЛЬЗОВАТЕЛЬСКИЙ ЗАПРОС: "{user_prompt}"

Объедини ТОЧНУЮ композицию фото с СОДЕРЖАНИЕМ запроса. Ответ в JSON формате."""
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_message_text},
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
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result["choices"][0]["message"]["content"]
                        
                        # Парсим JSON ответ
                        try:
                            import json
                            parsed_result = json.loads(content)
                            return parsed_result
                        except json.JSONDecodeError:
                            # Если не JSON, пытаемся извлечь JSON из markdown блока
                            logger.warning("[Vision API] Ответ не в JSON, извлекаем из markdown")
                            
                            # Пробуем извлечь JSON из markdown блока ```json...```
                            import re
                            json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
                            if json_match:
                                try:
                                    json_content = json_match.group(1)
                                    parsed_result = json.loads(json_content)
                                    logger.info(f"[Vision API] JSON успешно извлечен из markdown блока")
                                    return parsed_result
                                except json.JSONDecodeError:
                                    logger.warning("[Vision API] Не удалось парсить JSON из markdown")
                            
                            # Если и это не работает, пытаемся извлечь промпт из текста
                            # Ищем строку с "prompt": "..."
                            prompt_match = re.search(r'"prompt":\s*"([^"]+)"', content)
                            if prompt_match:
                                extracted_prompt = prompt_match.group(1)
                                return {
                                    "analysis": "Анализ изображения выполнен",
                                    "prompt": extracted_prompt
                                }
                            
                            # Последняя попытка - используем весь контент как промпт
                            return {
                                "analysis": "Анализ изображения выполнен", 
                                "prompt": content.strip()
                            }
                    else:
                        error_text = await response.text()
                        logger.error(f"[Vision API] Ошибка {response.status}: {error_text}")
                        return {}
                        
        except Exception as e:
            logger.error(f"[Vision API] Ошибка вызова API: {e}")
            return {}
    
    async def _fallback_analysis(self, user_prompt: Optional[str], avatar_type: str) -> Dict[str, Any]:
        """Fallback анализ без GPT Vision"""
        logger.info("[Image Analysis] Использование fallback анализа")
        
        if user_prompt:
            # Создаем кинематографический промпт на базе пользовательского запроса
            cinematic_result = await self.cinematic_service.create_cinematic_prompt(
                user_prompt=user_prompt,
                avatar_type=avatar_type,
                style_preset="photorealistic"
            )
            
            return {
                "analysis": f"Базовый анализ: {user_prompt}",
                "prompt": cinematic_result["processed"],
                "cinematic_enhancement": True,
                "style": "cinematic_fallback"
            }
        else:
            # Базовый кинематографический промпт
            base_prompt = "professional portrait"
            cinematic_result = await self.cinematic_service.create_cinematic_prompt(
                user_prompt=base_prompt,
                avatar_type=avatar_type,
                style_preset="photorealistic"
            )
            
            return {
                "analysis": "Базовый анализ портрета",
                "prompt": cinematic_result["processed"],
                "cinematic_enhancement": True,
                "style": "cinematic_default"
            } 

    def is_available(self) -> bool:
        """
        Проверяет доступность сервиса анализа изображений
            
        Returns:
            bool: True если сервис доступен (есть OpenAI API ключ), False если работает в fallback режиме
        """
        # Сервис всегда доступен, но режим зависит от наличия API ключа
        is_vision_available = bool(self.openai_api_key)
        
        if is_vision_available:
            logger.debug("[Image Analysis] Сервис доступен с GPT-4 Vision API")
        else:
            logger.debug("[Image Analysis] Сервис доступен в fallback режиме (без Vision API)")
        
        return True  # Сервис всегда доступен (fallback в случае отсутствия API ключа) 