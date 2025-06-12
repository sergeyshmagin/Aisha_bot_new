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
            
            # Извлекаем информацию об окружении из анализа
            environment_text = self._extract_environment_from_analysis(base_description, vision_prompt)
            
            # Интегрируем пользовательский промпт если есть
            if user_prompt:
                integrated_prompt = f"{vision_prompt}, {user_prompt}"
            else:
                integrated_prompt = vision_prompt
            
            # 6. Применяем кинематографические улучшения с environment_text
            cinematic_result = await self.cinematic_service.create_cinematic_prompt(
                user_prompt=integrated_prompt,
                avatar_type=avatar_type,
                style_preset="photorealistic",
                environment_text=environment_text
            )
            
            logger.info(f"[Image Analysis] Создан кинематографический промпт: {len(cinematic_result['processed'])} символов")
            
            # Добавляем негативный промпт с улучшениями для глаз
            from app.services.generation.prompt.enhancement.prompt_enhancer import PromptEnhancer
            enhancer = PromptEnhancer()
            negative_prompt = enhancer.get_negative_prompt(avatar_type)
            
            return {
                "analysis": base_description,
                "prompt": cinematic_result["processed"],
                "negative_prompt": negative_prompt,
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
🎯 USER REQUEST INTEGRATION:
User added text request: "{user_prompt}"

IMPORTANT: Combine visual composition from photo with user request content.
- PRESERVE: shot type, pose, lighting, atmosphere from photo
- INTEGRATE: request content (suit, scene, character, style)"""
        
        return f"""You are an expert in image analysis for creating CINEMATIC prompts in professional 8K photography style.

TASK: Analyze the image and create a prompt in example style with maximum detail.{user_integration}

🎬 PROMPT STYLE (like examples):
Must include ALL elements:
1. **Technical specs**: "high-quality, cinematic, ultra-realistic", "8K resolution", "professional camera"
2. **Shot type**: "close-up portrait"/"full-body portrait"/"medium portrait" 
3. **Lighting**: "warm directional side lighting during golden hour" / "professional studio lighting"
4. **Composition**: "expertly framed with subject positioned centrally"
5. **Detailed subject description**: appearance, clothing, style, expression
6. **Pose and angle**: exact body position, gaze direction, gestures
7. **Environment**: detailed background description, atmosphere, context
8. **Technical parameters**: "shot with 85mm lens", "depth of field", "razor-sharp focus"
9. **Color palette**: "rich warm tones, deep golds, luxurious ambers"
10. **Quality**: "natural skin texture", "well-defined eyes", "authentic detail"

📐 SHOT TYPE DETERMINATION (CRITICALLY IMPORTANT):
- Are person's legs visible? → FULL-BODY PORTRAIT
- Torso visible to waist? → HALF-BODY PORTRAIT  
- Only head and shoulders? → CLOSE-UP PORTRAIT

🔍 ANALYSIS BY BLOCKS:

**COMPOSITION AND FRAME:**
- What exact shot type (full body/half body/close-up)?
- How is subject positioned in frame?
- Shooting angles and perspective

**LIGHTING:**
- Lighting type (studio/natural/golden hour/dramatic)
- Light direction and shadows
- Atmosphere and mood

**SUBJECT:**
- Detailed appearance description
- Clothing and style (colors, textures, details)
- Facial expression and emotions

**POSE AND BODY LANGUAGE:**
- Exact body position
- Gaze direction
- Gestures and hand positions

**ENVIRONMENT:**
- Detailed background description
- Context and location
- Interior/exterior elements
- Identify recognizable cities or landmarks if possible, specify them in analysis

**TECHNICAL DETAILS:**
- Depth of field
- Focus
- Image quality

JSON RESPONSE FORMAT:
```json
{{
  "analysis": "Detailed analysis of each composition block",
  "prompt": "Ready cinematic prompt in example style"
}}
```

EXAMPLE PROMPT STYLE:
"A high-quality, cinematic, ultra-realistic close-up portrait photograph, captured by professional medium-format digital camera, in style of super-detailed 8K resolution imagery, featuring warm directional side lighting during golden hour. The composition is expertly framed with subject positioned centrally, featuring a confident man with contemporary styling, positioned with natural elegance and authentic body language, gazing directly at camera with engaging intensity. Set in sophisticated modern environment with clean architectural lines, captured by professional medium-format digital camera, shot with 85mm portrait lens at f/2.8 for optimal sharpness, The depth of field is exceptional ensuring razor-sharp focus on subject, professional bokeh with smooth background transition. The color palette emphasizes rich warm tones and deep golds creating sophisticated atmospheric mood, beautiful detailed eyes with sharp pupils, clean eyelashes, realistic reflection, well-defined eyes with natural catchlight and authentic iris detail, natural skin texture with fine detail and visible pores, sharp focus with optimal detail retention, high-end editorial photography style with cinematic quality."

Create prompt EXACTLY in this style with maximum detail!"""
    
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
            
            user_message_text = "Analyze this image and create cinematic prompt in example style. Response in JSON format."
            if user_prompt:
                user_message_text = f"""Analyze image and create cinematic prompt, INTEGRATING user request.

USER REQUEST: "{user_prompt}"

Combine EXACT photo composition with REQUEST content. Response in JSON format."""
            
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
        
        # Создаем негативный промпт
        from app.services.generation.prompt.enhancement.prompt_enhancer import PromptEnhancer
        enhancer = PromptEnhancer()
        negative_prompt = enhancer.get_negative_prompt(avatar_type)
        
        if user_prompt:
            # Создаем кинематографический промпт на базе пользовательского запроса
            cinematic_result = await self.cinematic_service.create_cinematic_prompt(
                user_prompt=user_prompt,
                avatar_type=avatar_type,
                style_preset="photorealistic",
                environment_text=None  # В fallback режиме environment_text недоступен
            )
            
            return {
                "analysis": f"Базовый анализ: {user_prompt}",
                "prompt": cinematic_result["processed"],
                "negative_prompt": negative_prompt,
                "cinematic_enhancement": True,
                "style": "cinematic_fallback"
            }
        else:
            # Базовый кинематографический промпт
            base_prompt = "professional portrait"
            cinematic_result = await self.cinematic_service.create_cinematic_prompt(
                user_prompt=base_prompt,
                avatar_type=avatar_type,
                style_preset="photorealistic",
                environment_text=None  # В fallback режиме environment_text недоступен
            )
            
            return {
                "analysis": "Базовый анализ портрета",
                "prompt": cinematic_result["processed"],
                "negative_prompt": negative_prompt,
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

    def _extract_environment_from_analysis(self, analysis: str, prompt: str) -> Optional[str]:
        """Извлекает информацию об окружении из анализа GPT Vision"""
        import re
        
        # Объединяем анализ и промпт для поиска
        combined_text = f"{analysis} {prompt}".lower()
        
        # Паттерны для поиска описаний окружения
        environment_patterns = [
            # Ищем упоминания известных мест
            r'(?:dubai|burj khalifa|дубай|бурдж халифа)',
            r'(?:moscow|red square|москва|красная площадь)',
            r'(?:new york|times square|нью[-\s]?йорк|таймс[-\s]?сквер)',
            r'(?:london|big ben|лондон|биг[-\s]?бен)',
            r'(?:paris|eiffel tower|париж|эйфелева башня)',
            
            # Ищем описания типов локаций
            r'(?:office|офис|business|деловой)',
            r'(?:studio|студия|photography studio)',
            r'(?:restaurant|cafe|ресторан|кафе)',
            r'(?:urban|city|городской|город)',
            r'(?:nature|forest|park|природа|лес|парк)',
            r'(?:modern architecture|современная архитектура)',
            r'(?:skyscraper|небоскреб)',
            r'(?:interior|интерьер)',
            r'(?:exterior|экстерьер)',
        ]
        
        found_environments = []
        
        for pattern in environment_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                found_environments.extend(matches)
        
        # Если найдены упоминания окружения, создаем описание
        if found_environments:
            # Удаляем дубликаты и сортируем
            unique_environments = list(set(found_environments))
            
            # Специальная обработка для известных мест
            if any('dubai' in env.lower() or 'дубай' in env.lower() for env in unique_environments):
                return ("Set against the iconic Dubai skyline with the magnificent Burj Khalifa towering in the background, "
                       "featuring the architectural marvel rendered with atmospheric perspective and soft focus, "
                       "showcasing the grandeur of modern urban achievement with warm desert lighting")
                       
            elif any('office' in env.lower() or 'офис' in env.lower() for env in unique_environments):
                return ("Set in a sophisticated modern office environment with clean architectural lines, "
                       "contemporary interior design elements visible in the professionally blurred background, "
                       "featuring warm ambient lighting and luxurious furnishings that convey success and professionalism")
                       
            elif any('studio' in env.lower() or 'студия' in env.lower() for env in unique_environments):
                return ("In a professional photography studio setting with seamless backdrop and controlled environment, "
                       "featuring expertly positioned lighting equipment and neutral tones, "
                       "creating optimal conditions for maximum image quality and focus on the subject")
                       
            elif any(env.lower() in ['urban', 'city', 'городской', 'город'] for env in unique_environments):
                return ("Against an urban landscape backdrop with sophisticated architectural elements softly blurred, "
                       "featuring metropolitan atmosphere with natural depth and environmental context, "
                       "showcasing the dynamic relationship between subject and contemporary cityscape")
                       
            elif any(env.lower() in ['nature', 'forest', 'park', 'природа', 'лес', 'парк'] for env in unique_environments):
                return ("Surrounded by natural landscape with organic textures and soft environmental elements, "
                       "featuring lush background with perfect depth of field and natural color harmony, "
                       "creating serene connection with the natural world and organic beauty")
                       
            elif any(env.lower() in ['restaurant', 'cafe', 'ресторан', 'кафе'] for env in unique_environments):
                return ("Set in an elegant dining establishment with sophisticated interior design, "
                       "featuring warm ambient lighting and luxurious decor elements softly blurred in the background, "
                       "conveying refined taste and upscale lifestyle atmosphere")
        
        return None 