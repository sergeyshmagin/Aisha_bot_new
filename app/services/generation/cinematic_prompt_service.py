"""
Кинематографический сервис генерации промтов для максимального фотореализма
Создает детальные промпты в стиле профессиональной фотографии
"""
import re
import random
import aiohttp
from typing import Optional, Dict, Any, List

from app.core.config import settings
from app.core.logger import get_logger
from app.shared.utils.openai import get_openai_headers

logger = get_logger(__name__)


class CinematicPromptService:
    """
    Сервис для создания кинематографических детальных промтов
    
    Создает промпты в стиле:
    - Профессиональной фотографии 8K качества
    - Детального описания сцены, позы, ракурса, света
    - Технических параметров съемки
    - Цветовой палитры и атмосферы
    """
    
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o"
    
    async def create_cinematic_prompt(
        self, 
        user_prompt: str, 
        avatar_type: str = "portrait",
        style_preset: str = "photorealistic",
        environment_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создает кинематографический детальный промпт
        
        Args:
            user_prompt: Исходный промпт от пользователя
            avatar_type: Тип аватара ("portrait")
            style_preset: Стилевая предустановка
            environment_text: Текст описания окружения (извлеченный из анализа)
            
        Returns:
            Dict с обработанным промптом и метаданными
        """
        try:
            logger.info(f"[Cinematic Prompt] Создание детального промпта: '{user_prompt[:50]}...'")
            
            # 1. Переводим промпт если нужно
            if self._needs_translation(user_prompt):
                translated_prompt = await self._translate_with_gpt(user_prompt)
                logger.info(f"[Translation] '{user_prompt}' → '{translated_prompt}'")
            else:
                translated_prompt = user_prompt
            
            # 2. Проверяем длину промпта и нужно ли улучшение
            if len(translated_prompt) > 300:
                logger.info(f"[Cinematic] Промпт длинный ({len(translated_prompt)} символов), пропускаем оптимизацию")
                final_prompt = self._ensure_tok_prefix(translated_prompt, avatar_type)
                return {
                    "original": user_prompt,
                    "processed": final_prompt,
                    "enhancement_applied": False,
                    "style": "long_prompt_no_optimization"
                }
            
            if self._is_already_cinematic(translated_prompt):
                logger.info(f"[Cinematic] Промпт уже детальный, добавляем только TOK")
                final_prompt = self._ensure_tok_prefix(translated_prompt, avatar_type)
                return {
                    "original": user_prompt,
                    "processed": final_prompt,
                    "enhancement_applied": False,
                    "style": "already_detailed"
                }
            
            # 3. Создаем кинематографический промпт с environment_text
            cinematic_prompt = await self._build_cinematic_prompt(translated_prompt, avatar_type, environment_text)
            
            # 4. Финальная оптимизация
            optimized_prompt = self._optimize_prompt(cinematic_prompt)
            
            logger.info(f"[Cinematic] Создан промпт: {len(optimized_prompt)} символов")
            
            return {
                "original": user_prompt,
                "processed": optimized_prompt,
                "enhancement_applied": True,
                "style": "cinematic_detailed",
                "word_count": len(optimized_prompt.split()),
                "technical_level": "professional"
            }
            
        except Exception as e:
            logger.exception(f"[Cinematic] Ошибка создания промпта: {e}")
            # Fallback к базовому улучшению
            return {
                "original": user_prompt,
                "processed": self._ensure_tok_prefix(user_prompt, avatar_type),
                "enhancement_applied": False,
                "style": "fallback"
            }
    
    async def _build_cinematic_prompt(self, base_prompt: str, avatar_type: str, environment_text: Optional[str] = None) -> str:
        """Строит кинематографический промпт по блокам с приоритетом композиции"""
        
        prompt_lower = base_prompt.lower()
        components = []
        
        # 1. Префикс TOK для портретных аватаров
        if avatar_type == "portrait":
            components.append("TOK")
        
        # 🎯 2. КРИТИЧЕСКИ ВАЖНО: Тип кадра и композиция СРАЗУ после TOK
        shot_type = self._determine_shot_type(prompt_lower)
        components.append(shot_type)
        
        # 3. Дополнительные композиционные уточнения для полного роста
        if any(word in prompt_lower for word in [
            'full body', 'standing', 'walking', 'полный рост', 'стоя', 'в полный рост',
            'по пояс', 'торс', 'до пояса', 'весь рост', 'целиком'
        ]):
            # Усиливаем композиционное требование
            if 'full' in shot_type or 'полный' in prompt_lower or 'в полный рост' in prompt_lower:
                components.append("showing the entire figure from head to feet, complete body composition")
            elif 'half' in shot_type or 'по пояс' in prompt_lower:
                components.append("framed from waist up, upper body composition")
        
        # 3.5. Дополнительные композиционные усилители для точного соблюдения требований
        composition_enhancers = self._enhance_composition_requirements(prompt_lower)
        if composition_enhancers:
            # Добавляем только самые важные усилители, чтобы не перегружать промпт
            components.extend(composition_enhancers[:2])  # Берем максимум 2 усилителя
        
        # 4. Технические характеристики изображения (после композиции)
        tech_specs = self._build_technical_specifications()
        components.extend(tech_specs)
        
        # 5. Описание освещения
        lighting = self._create_lighting_description(prompt_lower)
        components.append(lighting)
        
        # 6. Детальная композиция и фрейминг
        composition = self._create_composition_description(prompt_lower)
        components.append(composition)
        
        # 7. Детальное описание субъекта
        subject_description = self._enhance_subject_description(base_prompt, prompt_lower)
        components.append(subject_description)
        
        # 8. Поза и язык тела
        pose_description = self._create_pose_description(prompt_lower)
        components.append(pose_description)
        
        # 9. Окружение и фон (с поддержкой переданного environment_text)
        environment = self._create_environment_description(prompt_lower, environment_text)
        if environment:
            components.append(environment)
        
        # 10. Технические параметры камеры
        camera_tech = self._create_camera_specifications()
        components.extend(camera_tech)
        
        # 11. Цветовая палитра
        color_palette = self._create_color_palette(prompt_lower)
        components.append(color_palette)
        
        # 12. Финальные детали качества
        quality_specs = self._create_quality_specifications()
        components.extend(quality_specs)
        
        # Объединяем компоненты
        return ", ".join(components)
    
    def _build_technical_specifications(self) -> List[str]:
        """Создает технические характеристики изображения"""
        return [
            "A high-quality",
            "cinematic", 
            "ultra-realistic",
            "8K resolution imagery"
        ]
    
    def _determine_shot_type(self, prompt_lower: str) -> str:
        """Определяет тип кадра с детальным описанием и приоритетом композиции"""
        
        # Полный рост - максимальный приоритет
        if any(word in prompt_lower for word in [
            'full body', 'full-body', 'full-length', 'full length', 'standing', 'walking', 
            'полный рост', 'стоя', 'в полный рост', 'весь рост', 'целиком', 
            'от головы до ног', 'во весь рост', 'полностью', 'с ног до головы', 
            'целая фигура', 'вся фигура', 'entire figure', 'complete body'
        ]):
            return "full-body portrait photograph"
        
        # По пояс / до пояса
        elif any(word in prompt_lower for word in [
            'half body', 'half-body', 'waist up', 'по пояс', 'торс', 'до пояса',
            'upper body', 'от пояса', 'половина тела', 'грудь и плечи'
        ]):
            return "half-body portrait photograph"
        
        # Крупный план / голова и плечи
        elif any(word in prompt_lower for word in [
            'close-up', 'close up', 'headshot', 'head shot', 'крупный план', 'голова',
            'лицо крупно', 'только лицо', 'голова и плечи', 'портрет лица'
        ]):
            return "close-up portrait photograph"
        
        # Средний план - если ничего конкретного не указано
        else:
            return "medium portrait photograph"
    
    def _create_lighting_description(self, prompt_lower: str) -> str:
        """Создает профессиональное описание освещения"""
        if any(word in prompt_lower for word in ['sunset', 'evening', 'закат', 'вечер', 'golden']):
            return "featuring warm, directional side lighting during the golden hour"
        elif any(word in prompt_lower for word in ['studio', 'студия', 'professional']):
            return "featuring professional studio lighting with controlled shadows and soft key light"
        elif any(word in prompt_lower for word in ['office', 'indoor', 'офис', 'помещение']):
            return "featuring natural window light with soft directional shadows and balanced ambient lighting"
        elif any(word in prompt_lower for word in ['outdoor', 'natural', 'улица', 'natural light']):
            return "featuring natural diffused daylight with optimal exposure and gentle shadows"
        elif any(word in prompt_lower for word in ['dramatic', 'contrast', 'драматический']):
            return "featuring dramatic directional lighting with strong contrasts and deep shadows"
        else:
            return "featuring professional photography lighting with balanced exposure and natural shadows"
    
    def _create_composition_description(self, prompt_lower: str) -> str:
        """Создает описание композиции и фрейминга"""
        compositions = [
            "The composition is expertly framed with the subject positioned optimally in the frame",
            "The framing follows professional photography principles with balanced visual weight",
            "The composition centers around the subject with perfect proportional spacing"
        ]
        return random.choice(compositions)
    
    def _enhance_subject_description(self, original_prompt: str, prompt_lower: str) -> str:
        """Улучшает описание субъекта"""
        
        # Определяем пол для корректного описания
        if any(word in prompt_lower for word in ['man', 'male', 'мужчина', 'парень']):
            gender_prefix = "a confident man"
        elif any(word in prompt_lower for word in ['woman', 'female', 'женщина', 'девушка']):
            gender_prefix = "an elegant woman"  
        else:
            gender_prefix = "a charismatic person"
        
        # Базовое описание из оригинального промпта
        enhanced_description = f"{gender_prefix}, {original_prompt}"
        
        # Добавляем детали внешности
        details = []
        
        # Добавляем качественное описание глаз для всех промптов
        details.append("with beautiful detailed eyes, sharp pupils, clean eyelashes, realistic reflection")
        
        if not any(word in prompt_lower for word in ['hair', 'волосы']):
            details.append("with expertly styled hair showing natural texture and contemporary cut")
        
        if not any(word in prompt_lower for word in ['skin', 'кожа']):
            details.append("showcasing natural skin tone with authentic detail and healthy complexion")
        
        if any(word in prompt_lower for word in ['formal', 'suit', 'business', 'деловой', 'костюм']):
            details.append("dressed in impeccably tailored formal attire with refined fabric textures")
        elif any(word in prompt_lower for word in ['casual', 'relaxed', 'повседневный']):
            details.append("wearing stylish contemporary clothing with modern design elements")
        
        if details:
            enhanced_description += ", " + ", ".join(details)
        
        return enhanced_description
    
    def _create_pose_description(self, prompt_lower: str) -> str:
        """Создает детальное описание позы"""
        if any(word in prompt_lower for word in ['confident', 'strong', 'уверенный', 'сильный']):
            poses = [
                "positioned with confident body language and assertive stance, gazing directly at the camera with engaging intensity and natural charisma",
                "displaying confident posture with strong shoulders and direct eye contact, conveying leadership and professional presence",
                "standing with powerful presence and authentic confidence, creating compelling visual narrative through body positioning"
            ]
        elif any(word in prompt_lower for word in ['relaxed', 'casual', 'natural', 'расслабленный']):
            poses = [
                "in a relaxed, natural pose with authentic body positioning and genuine expression, creating approachable and warm atmosphere",
                "displaying casual elegance with natural weight distribution and effortless positioning, conveying comfort and authenticity",
                "positioned naturally with relaxed shoulders and genuine smile, creating inviting and personable presence"
            ]
        elif any(word in prompt_lower for word in ['professional', 'business', 'formal', 'деловой']):
            poses = [
                "maintaining professional posture with polished presentation and authoritative stance, projecting competence and reliability",
                "positioned with executive presence and refined body language, conveying leadership and business acumen",
                "displaying corporate professionalism through precise positioning and confident bearing"
            ]
        else:
            poses = [
                "positioned with natural elegance and authentic body language, creating compelling visual narrative and emotional connection",
                "displaying perfect balance between confidence and approachability through thoughtful positioning and genuine expression",
                "maintaining optimal posture with engaging presence and natural charisma, creating memorable photographic impact"
            ]
        
        return random.choice(poses)
    
    def _create_environment_description(self, prompt_lower: str, environment_text: Optional[str] = None) -> Optional[str]:
        """Создает детальное описание окружения с учетом композиционных требований"""
        if environment_text:
            return environment_text
        
        # Дубай и знаменитые места
        if any(word in prompt_lower for word in ['dubai', 'burj khalifa', 'дубай', 'бурдж халифа']):
            return ("Set against the iconic Dubai skyline with the magnificent Burj Khalifa towering in the background, "
                   "featuring the architectural marvel rendered with atmospheric perspective and soft focus, "
                   "showcasing the grandeur of modern urban achievement with warm desert lighting")
        
        # Офис и деловая среда
        elif any(word in prompt_lower for word in ['office', 'business', 'офис', 'деловой', 'корпоративный']):
            return ("Set in a sophisticated modern office environment with clean architectural lines, "
                   "contemporary interior design elements visible in the professionally blurred background, "
                   "featuring warm ambient lighting and luxurious furnishings that convey success and professionalism")
        
        # Студия фотографическая
        elif any(word in prompt_lower for word in ['studio', 'студия', 'фотостудия']):
            return ("In a professional photography studio setting with seamless backdrop and controlled environment, "
                   "featuring expertly positioned lighting equipment and neutral tones, "
                   "creating optimal conditions for maximum image quality and focus on the subject")
        
        # Улица и городская среда
        elif any(word in prompt_lower for word in ['outdoor', 'street', 'city', 'улица', 'город', 'на улице', 'городской']):
            return ("Against an urban landscape backdrop with sophisticated architectural elements softly blurred, "
                   "featuring metropolitan atmosphere with natural depth and environmental context, "
                   "showcasing the dynamic relationship between subject and contemporary cityscape")
        
        # Природа и парки
        elif any(word in prompt_lower for word in ['nature', 'forest', 'park', 'природа', 'лес', 'парк', 'зелень']):
            return ("Surrounded by natural landscape with organic textures and soft environmental elements, "
                   "featuring lush background with perfect depth of field and natural color harmony, "
                   "creating serene connection with the natural world and organic beauty")
        
        # Ресторан и кафе
        elif any(word in prompt_lower for word in ['restaurant', 'cafe', 'ресторан', 'кафе', 'бар']):
            return ("Set in an elegant dining establishment with sophisticated interior design, "
                   "featuring warm ambient lighting and luxurious decor elements softly blurred in the background, "
                   "conveying refined taste and upscale lifestyle atmosphere")
        
        # Дом и интерьер
        elif any(word in prompt_lower for word in ['home', 'interior', 'дом', 'интерьер', 'комната', 'квартира']):
            return ("In a beautifully designed interior space with tasteful decor and warm, inviting atmosphere, "
                   "featuring elegant furnishings and soft ambient lighting that creates a comfortable domestic setting")
        
        # Море и пляж
        elif any(word in prompt_lower for word in ['beach', 'sea', 'ocean', 'пляж', 'море', 'океан']):
            return ("Against a stunning coastal backdrop with the ocean stretching to the horizon, "
                   "featuring natural lighting and the serene beauty of the seaside environment")
        
        # Горы и возвышенности
        elif any(word in prompt_lower for word in ['mountain', 'hill', 'гора', 'горы', 'холм', 'возвышенность']):
            return ("Set against majestic mountain scenery with dramatic natural landscape in the background, "
                   "featuring atmospheric perspective and the grandeur of natural elevation")
        
        # Фон и задний план (общие указания)
        elif any(word in prompt_lower for word in ['фон', 'background', 'задний план', 'backdrop']):
            return ("With carefully composed background elements that complement the subject, "
                   "featuring professional depth of field and balanced environmental context")
        
        return None
    
    def _create_camera_specifications(self) -> List[str]:
        """Создает технические характеристики камеры"""
        camera_specs = [
            "captured by a professional medium-format digital camera",
            "shot with 85mm portrait lens at f/2.8 for optimal sharpness",
            "The depth of field is exceptional, ensuring razor-sharp focus on the subject",
            "professional bokeh with smooth background transition"
        ]
        
        return camera_specs
    
    def _create_color_palette(self, prompt_lower: str) -> str:
        """Создает описание цветовой палитры"""
        if any(word in prompt_lower for word in ['warm', 'golden', 'sunset', 'теплый', 'золотой']):
            return ("The color palette emphasizes rich warm tones, deep golds, and luxurious ambers, "
                   "creating an inviting and sophisticated atmospheric mood with perfect color harmony")
        
        elif any(word in prompt_lower for word in ['cool', 'blue', 'modern', 'холодный', 'синий']):
            return ("The color palette features sophisticated cool tones, deep blues, and crisp whites, "
                   "conveying contemporary elegance and professional refinement with balanced saturation")
        
        elif any(word in prompt_lower for word in ['dramatic', 'contrast', 'black', 'драматический']):
            return ("The color palette utilizes dramatic contrasts between deep shadows and bright highlights, "
                   "featuring rich blacks, pristine whites, and selective color accents for maximum visual impact")
        
        elif any(word in prompt_lower for word in ['natural', 'earth', 'green', 'природный']):
            return ("The color palette draws from natural earth tones, featuring organic greens, warm browns, "
                   "and soft beiges that create perfect harmony with environmental elements")
        
        else:
            return ("The color palette is expertly balanced with rich, saturated colors and subtle tonal variations, "
                   "creating visual depth and emotional resonance throughout the entire composition")
    
    def _create_quality_specifications(self) -> List[str]:
        """Создает спецификации качества изображения"""
        return [
            "beautiful detailed eyes with sharp pupils, clean eyelashes, realistic reflection",
            "well-defined eyes with natural catchlight and authentic iris detail",
            "natural skin texture with fine detail and visible pores",
            "authentic facial features with realistic proportions",
            "sharp focus with optimal detail retention",
            "no facial deformation, no duplicate features",
            "high-end editorial photography style with cinematic quality"
        ]
    
    def _needs_translation(self, text: str) -> bool:
        """Проверяет, нужен ли перевод"""
        # Простая проверка наличия кириллицы
        return bool(re.search(r'[а-яё]', text.lower()))
    
    async def _translate_with_gpt(self, russian_text: str) -> str:
        """Переводит промпт через GPT API"""
        if not self.openai_api_key:
            logger.warning("[Translation] Нет API ключа OpenAI, используем локальный перевод")
            return self._simple_translate(russian_text)
        
        system_prompt = """You are a professional prompt translator for AI image generation.

TASK: Accurately translate Russian/Kazakh prompts to English for creating photorealistic images.

RULES:
1. Preserve all photography technical terms
2. Translate place names accurately (Дубай → Dubai, Бурдж Халифа → Burj Khalifa)
3. Maintain structure and meaning
4. DO NOT add extra details, only accurate translation
5. Preserve style and emotionality

EXAMPLES:
• "мужчина в костюме на фоне Бурдж Халифа" → "man in suit against Burj Khalifa backdrop"
• "деловой портрет в офисе" → "business portrait in office"
• "уверенный вид" → "confident appearance"

RESPONSE: only translated prompt without explanations."""

        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = get_openai_headers(self.openai_api_key)
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": russian_text}
                ],
                "temperature": 0.1,
                "max_tokens": 300
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        translated = result["choices"][0]["message"]["content"].strip()
                        return translated
                    else:
                        logger.error(f"[Translation] GPT API error: {response.status}")
                        return self._simple_translate(russian_text)
        
        except Exception as e:
            logger.error(f"[Translation] Ошибка: {e}")
            return self._simple_translate(russian_text)
    
    def _simple_translate(self, text: str) -> str:
        """Простой словарный перевод"""
        translations = {
            'мужчина': 'man', 'женщина': 'woman', 'парень': 'man', 'девушка': 'woman',
            'портрет': 'portrait', 'в костюме': 'in suit', 'деловой': 'business',
            'уверенный': 'confident', 'стоя': 'standing', 'полный рост': 'full body',
            'офис': 'office', 'улица': 'street', 'дубай': 'Dubai', 
            'бурдж халифа': 'Burj Khalifa', 'на фоне': 'against backdrop of'
        }
        
        result = text.lower()
        for ru, en in translations.items():
            result = result.replace(ru, en)
        
        return result
    
    def _is_already_cinematic(self, prompt: str) -> bool:
        """Проверяет, является ли промпт уже кинематографическим"""
        cinematic_indicators = [
            'cinematic', 'ultra-realistic', '8K resolution', 'professional camera',
            'golden hour', 'directional lighting', 'depth of field', 'razor-sharp',
            'color palette', 'editorial photography', 'medium-format', 'bokeh'
        ]
        
        found_indicators = sum(1 for indicator in cinematic_indicators 
                              if indicator.lower() in prompt.lower())
        
        return found_indicators >= 3 and len(prompt) > 300
    
    def _ensure_tok_prefix(self, prompt: str, avatar_type: str) -> str:
        """Обеспечивает наличие TOK префикса для портретных аватаров"""
        if avatar_type == "portrait" and not prompt.startswith("TOK"):
            return f"TOK, {prompt}"
        return prompt
    
    def _optimize_prompt(self, prompt: str) -> str:
        """Оптимизирует финальный промпт"""
        # Удаляем лишние пробелы и повторения
        optimized = re.sub(r'\s+', ' ', prompt)
        optimized = re.sub(r',\s*,', ',', optimized)
        optimized = optimized.strip()
        
        # Убираем дублирующиеся фразы
        parts = optimized.split(', ')
        unique_parts = []
        seen = set()
        
        for part in parts:
            key_words = set(part.lower().split()[:3])  # Первые 3 слова как ключ
            key = tuple(sorted(key_words))
            if key not in seen:
                unique_parts.append(part)
                seen.add(key)
        
        return ', '.join(unique_parts)
    
    def _enhance_composition_requirements(self, prompt_lower: str) -> List[str]:
        """
        Создает дополнительные композиционные усилители для четкого соблюдения требований
        Эти фразы помогают модели точно соблюдать указанную композицию
        """
        enhancements = []
        
        # Усилители для полного роста
        if any(word in prompt_lower for word in [
            'full body', 'full-body', 'full-length', 'full length', 'standing', 'walking',
            'полный рост', 'в полный рост', 'весь рост', 'целиком', 'от головы до ног', 
            'во весь рост', 'полностью', 'с ног до головы', 'целая фигура', 'вся фигура',
            'entire figure', 'complete body'
        ]):
            enhancements.extend([
                "complete figure visible from head to toes",
                "entire body composition with full height",
                "no cropping of limbs or body parts",
                "full-length portrait showing complete anatomy"
            ])
        
        # Усилители для съемки по пояс
        elif any(word in prompt_lower for word in [
            'half body', 'half-body', 'по пояс', 'торс', 'до пояса', 'upper body', 'от пояса'
        ]):
            enhancements.extend([
                "framed from waist up",
                "upper torso and head composition",
                "waist-level framing"
            ])
        
        # Усилители для указанного фона
        if any(word in prompt_lower for word in [
            'фон', 'background', 'на фоне', 'против фона', 'backdrop', 'задний план'
        ]):
            enhancements.append("with clearly visible background environment")
        
        # Усилители для указанного окружения
        if any(word in prompt_lower for word in [
            'в', 'на', 'среди', 'возле', 'рядом с', 'около', 'у'
        ]):
            enhancements.append("positioned within the specified environment")
        
        return enhancements 