"""
Сервис обработки промптов для генерации изображений
Создает детальные, профессиональные промпты для максимального качества генерации
"""
import aiohttp
from typing import Optional, Dict, Any
import time
import random
import re
import json

from app.core.config import settings
from app.core.logger import get_logger
from app.shared.utils.openai import get_openai_headers
from .cinematic_prompt_service import CinematicPromptService

logger = get_logger(__name__)


class PromptProcessingService:
    """Сервис для создания детальных профессиональных промптов"""
    
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o"
        self.cinematic_service = CinematicPromptService()
    
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
            
            # Используем новый кинематографический сервис
            cinematic_result = await self.cinematic_service.create_cinematic_prompt(
                user_prompt=user_prompt,
                avatar_type=avatar_type,
                style_preset="photorealistic"
            )
            
            # Создаем negative prompt
            negative_prompt = self.get_negative_prompt(avatar_type)
            
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
            return {
                "original": user_prompt,
                "processed": f"TOK, {user_prompt}" if avatar_type == "portrait" else user_prompt,
                "negative_prompt": self.get_negative_prompt(avatar_type),
                "translation_needed": False,
                "cinematic_enhancement": False,
                "style": "fallback",
                "processing_time": time.time() - start_time
            }

    async def _translate_with_gpt(self, russian_text: str) -> str:
        """
        Переводит промпт с русского на английский через GPT API
        Сохраняет технические термины и профессиональную терминологию
        """
        if not settings.OPENAI_API_KEY:
            logger.warning("Отсутствует API ключ OpenAI, используем локальный перевод")
            return self._translate_to_english(russian_text)
        
        system_prompt = """Ты профессиональный переводчик промптов для генерации изображений.

🎯 ЗАДАЧА: Переведи русский промпт на английский для AI-генерации фотореалистичных портретов.

📋 ПРАВИЛА ПЕРЕВОДА:
1. Сохраняй все технические термины фотографии
2. Переводи названия мест точно (Бурдж Халифа → Burj Khalifa, Дубай → Dubai)
3. Сохраняй структуру и порядок слов
4. Усиливай профессиональную терминологию фотографии
5. НЕ добавляй лишних слов, только точный перевод

ПРИМЕРЫ:
• "мужчина в костюме на фоне Бурдж Халифа" → "man in suit in front of Burj Khalifa"
• "деловой портрет в офисе" → "business portrait in office"
• "в полный рост на улице" → "full body on street"

ОТВЕТ: только переведенный промпт без пояснений."""

        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = get_openai_headers(settings.OPENAI_API_KEY)
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": russian_text}
                ],
                "temperature": 0.1,  # Низкая температура для точного перевода
                "max_tokens": 200
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        translated = result["choices"][0]["message"]["content"].strip()
                        logger.info(f"[GPT Translation] Успешно: '{russian_text}' → '{translated}'")
                        return translated
                    else:
                        error_text = await response.text()
                        logger.error(f"GPT API error: {error_text}")
                        return self._translate_to_english(russian_text)
        
        except Exception as e:
            logger.error(f"Ошибка GPT перевода: {e}")
            return self._translate_to_english(russian_text)

    async def create_enhanced_detailed_prompt(self, base_prompt: str, avatar_type: str) -> str:
        """
        Создает кинематографические детальные промпты в стиле профессиональных фотографий
        Полностью переписан для максимального фотореализма и детализации
        """
        
        prompt_lower = base_prompt.lower()
        
        # 🚀 ПРОВЕРЯЕМ: Если промпт уже очень детальный - возвращаем как есть
        if len(base_prompt) > 400 and self._is_already_detailed(base_prompt):
            logger.info(f"[Detailed Mode] Промпт уже детальный ({len(base_prompt)} символов) - возвращаем как есть")
            # Добавляем только TOK если его нет
            if not base_prompt.startswith("TOK"):
                return f"TOK, {base_prompt}"
            return base_prompt
        
        # 🎯 АНАЛИЗИРУЕМ КОНТЕКСТ И СОЗДАЕМ КИНЕМАТОГРАФИЧЕСКИЙ ПРОМПТ
        
        # 1. Начинаем с TOK для портретных аватаров
        if avatar_type == "portrait":
            enhanced_parts = ["TOK"]
        else:
            enhanced_parts = []
        
        # 2. Добавляем технические характеристики фото
        tech_specs = [
            "A high-quality, cinematic, ultra-realistic",
            self._determine_shot_type(prompt_lower),
            "photograph, captured by a professional medium-format digital camera",
            "in style of super-detailed 8K resolution imagery"
        ]
        
        # 3. Определяем и добавляем описание освещения
        lighting_desc = self._analyze_and_enhance_lighting(prompt_lower)
        tech_specs.append(lighting_desc)
        
        enhanced_parts.extend(tech_specs)
        
        # 4. Добавляем композицию и центрирование
        composition = self._create_composition_description(prompt_lower)
        enhanced_parts.append(composition)
        
        # 5. Детальное описание персонажа
        character_desc = self._enhance_character_description(base_prompt, prompt_lower)
        enhanced_parts.append(character_desc)
        
        # 6. Описание позы и ракурса
        pose_desc = self._create_detailed_pose_description(prompt_lower)
        enhanced_parts.append(pose_desc)
        
        # 7. Детальное описание окружения и фона
        environment_desc = self._create_detailed_environment(prompt_lower)
        if environment_desc:
            enhanced_parts.append(environment_desc)
        
        # 8. Технические параметры камеры и фокуса
        camera_details = [
            "The depth of field is exceptional, ensuring sharp focus on the subject",
            "shot on vintage medium-format camera with 85mm lens",
            "shallow depth of field with professional bokeh",
            "high-end editorial photography style"
        ]
        enhanced_parts.extend(camera_details)
        
        # 9. Цветовая палитра и атмосфера
        color_palette = self._determine_color_palette(prompt_lower)
        enhanced_parts.append(color_palette)
        
        # 10. Финальные детали качества
        quality_details = [
            "razor-sharp focus with optimal detail retention",
            "well-defined eyes with natural catchlight",
            "realistic face with visible pores and authentic shadows",
            "natural skin texture with fine detail",
            "no facial deformation, no duplicate features"
        ]
        enhanced_parts.extend(quality_details)
        
        # 🔗 ОБЪЕДИНЯЕМ в кинематографический промпт
        enhanced_prompt = ". ".join(enhanced_parts) + "."
        
        # 🧹 ЧИСТКА И ОПТИМИЗАЦИЯ
        enhanced_prompt = self._clean_and_optimize_prompt(enhanced_prompt)
        
        logger.info(f"[Cinematic Enhancement] {len(base_prompt)} → {len(enhanced_prompt)} символов")
        logger.info(f"[Style] Кинематографический детальный промпт создан")
        
        return enhanced_prompt

    def _is_already_detailed(self, prompt: str) -> bool:
        """Проверяет, является ли промпт уже детальным"""
        detailed_indicators = [
            'cinematic', 'ultra-realistic', '8K resolution', 'professional camera',
            'golden hour', 'directional lighting', 'depth of field', 'razor-sharp focus',
            'color palette', 'editorial photography', 'medium-format', 'bokeh',
            'captured by', 'shot on', 'exceptional quality'
        ]
        return sum(1 for indicator in detailed_indicators if indicator.lower() in prompt.lower()) >= 3

    def _determine_shot_type(self, prompt_lower: str) -> str:
        """Определяет тип кадра на основе контекста"""
        if any(word in prompt_lower for word in ['full body', 'standing', 'walking', 'полный рост', 'стоя']):
            return "full-body portrait"
        elif any(word in prompt_lower for word in ['half body', 'waist up', 'по пояс', 'торс']):
            return "half-body portrait"
        elif any(word in prompt_lower for word in ['close-up', 'headshot', 'крупный план', 'голова']):
            return "close-up portrait"
        else:
            return "medium portrait"

    def _analyze_and_enhance_lighting(self, prompt_lower: str) -> str:
        """Анализирует контекст и создает описание профессионального освещения"""
        if any(word in prompt_lower for word in ['sunset', 'evening', 'закат', 'вечер']):
            return "featuring warm, directional side lighting during the golden hour"
        elif any(word in prompt_lower for word in ['studio', 'office', 'indoor', 'студия', 'офис']):
            return "featuring professional studio lighting with controlled shadows and highlights"
        elif any(word in prompt_lower for word in ['natural', 'outdoor', 'street', 'natural light', 'улица']):
            return "featuring natural diffused lighting with soft shadows"
        elif any(word in prompt_lower for word in ['dramatic', 'contrast', 'shadow', 'драматический']):
            return "featuring dramatic directional lighting with deep contrasts"
        else:
            return "featuring warm, professional lighting with optimal exposure"

    def _create_composition_description(self, prompt_lower: str) -> str:
        """Создает описание композиции"""
        base_composition = "The composition is expertly framed"
        
        if any(word in prompt_lower for word in ['center', 'middle', 'центр']):
            return f"{base_composition}, with the subject positioned centrally in the frame"
        elif any(word in prompt_lower for word in ['left', 'right', 'side', 'сбоку']):
            return f"{base_composition}, with the subject positioned slightly off-center for dynamic balance"
        else:
            return f"{base_composition}, following the rule of thirds for visual impact"

    def _enhance_character_description(self, original_prompt: str, prompt_lower: str) -> str:
        """Создает детальное описание персонажа на основе оригинального промпта"""
        # Берем базовое описание из оригинального промпта
        character_base = original_prompt.strip()
        
        # Анализируем пол для корректного описания
        gender_context = ""
        if any(word in prompt_lower for word in ['man', 'male', 'мужчина', 'парень']):
            gender_context = "featuring a confident man"
        elif any(word in prompt_lower for word in ['woman', 'female', 'женщина', 'девушка']):
            gender_context = "featuring an elegant woman"
        else:
            gender_context = "featuring a charismatic person"
        
        # Добавляем детали внешности
        details = [
            "with natural facial features and authentic expression",
            "showcasing contemporary styling with precise attention to detail"
        ]
        
        if any(word in prompt_lower for word in ['hair', 'волосы']):
            details.append("with expertly styled hair showing natural texture")
        
        if any(word in prompt_lower for word in ['suit', 'dress', 'costume', 'костюм', 'платье']):
            details.append("wearing impeccably tailored attire with refined fabric details")
        
        return f"{gender_context}, {character_base}, {', '.join(details)}"

    def _create_detailed_pose_description(self, prompt_lower: str) -> str:
        """Создает детальное описание позы и ракурса"""
        if any(word in prompt_lower for word in ['confident', 'strong', 'уверенный']):
            return "posed with confident body language and natural stance, gazing directly at the camera with engaging intensity"
        elif any(word in prompt_lower for word in ['relaxed', 'casual', 'natural', 'расслабленный']):
            return "in a relaxed, natural pose with authentic body positioning and genuine expression"
        elif any(word in prompt_lower for word in ['dramatic', 'intense', 'драматический']):
            return "striking a dramatic pose with intentional positioning and captivating presence"
        else:
            return "positioned with natural elegance and authentic body language, creating compelling visual narrative"

    def _create_detailed_environment(self, prompt_lower: str) -> str:
        """Создает детальное описание окружения и фона"""
        if any(word in prompt_lower for word in ['office', 'business', 'офис', 'деловой']):
            return ("Set in a sophisticated modern office environment, with clean architectural lines "
                   "and professional interior design elements visible in the softly blurred background, "
                   "featuring warm ambient lighting and contemporary furnishings")
        
        elif any(word in prompt_lower for word in ['studio', 'студия']):
            return ("In a professional photography studio setting with controlled environment, "
                   "featuring seamless backdrop and expertly positioned lighting equipment, "
                   "creating optimal conditions for maximum image quality")
        
        elif any(word in prompt_lower for word in ['outdoor', 'street', 'city', 'улица', 'город']):
            return ("Against an urban landscape backdrop with architectural elements softly blurred, "
                   "featuring city atmosphere with natural depth and environmental context, "
                   "showcasing the relationship between subject and metropolitan setting")
        
        elif any(word in prompt_lower for word in ['nature', 'forest', 'park', 'природа', 'лес']):
            return ("Surrounded by natural landscape with organic textures and soft environmental elements, "
                   "featuring verdant background with natural depth of field, "
                   "creating harmonious connection with the natural world")
        
        elif any(word in prompt_lower for word in ['dubai', 'burj khalifa', 'дубай']):
            return ("Set against the iconic Dubai skyline with the majestic Burj Khalifa towering in the background, "
                   "featuring the modern architectural marvel softly blurred with atmospheric perspective, "
                   "showcasing the grandeur of contemporary urban achievement")
        
        else:
            return ("Set against a carefully curated background with optimal depth of field, "
                   "featuring environmental elements that complement the subject without distraction, "
                   "creating sophisticated visual context")

    def _determine_color_palette(self, prompt_lower: str) -> str:
        """Определяет цветовую палитру на основе контекста"""
        if any(word in prompt_lower for word in ['warm', 'golden', 'sunset', 'теплый', 'золотой']):
            return ("The color palette emphasizes warm golden tones, rich ambers, and deep honey hues, "
                   "creating an inviting and luxurious atmospheric mood")
        
        elif any(word in prompt_lower for word in ['cool', 'blue', 'modern', 'холодный', 'синий']):
            return ("The color palette features sophisticated cool tones, deep blues, and crisp whites, "
                   "conveying contemporary elegance and professional refinement")
        
        elif any(word in prompt_lower for word in ['dramatic', 'contrast', 'black', 'драматический']):
            return ("The color palette utilizes dramatic contrasts between deep shadows and bright highlights, "
                   "featuring rich blacks, pristine whites, and selective color accents")
        
        elif any(word in prompt_lower for word in ['natural', 'earth', 'green', 'natural', 'природный']):
            return ("The color palette draws from natural earth tones, featuring organic greens, warm browns, "
                   "and soft beiges that create harmony with the natural environment")
        
        else:
            return ("The color palette is carefully balanced with rich, saturated colors and subtle tonal variations, "
                   "creating visual depth and emotional resonance throughout the composition")

    def _clean_and_optimize_prompt(self, prompt: str) -> str:
        """Очищает и оптимизирует финальный промпт"""
        # Удаляем дублирующиеся фразы
        sentences = prompt.split('. ')
        unique_sentences = []
        seen_keywords = set()
        
        for sentence in sentences:
            # Проверяем ключевые слова для избежания дублирования
            words = set(sentence.lower().split())
            if not any(word in seen_keywords for word in words):
                unique_sentences.append(sentence)
                seen_keywords.update(words)
        
        cleaned_prompt = '. '.join(unique_sentences)
        
        # Исправляем грамматику и пунктуацию
        cleaned_prompt = re.sub(r'\s+', ' ', cleaned_prompt)  # Убираем лишние пробелы
        cleaned_prompt = re.sub(r'\.\s*\.', '.', cleaned_prompt)  # Убираем двойные точки
        cleaned_prompt = cleaned_prompt.strip()
        
        return cleaned_prompt

    def _enhance_environmental_context(self, prompt_lower: str) -> list:
        """Анализирует локацию и добавляет environmental детали против селфи"""
        
        environmental_details = []
        
        # 🏖️ ПЛЯЖНЫЕ ЛОКАЦИИ
        if any(word in prompt_lower for word in ['beach', 'пляж', 'maldives', 'мальдивы', 'ocean', 'sea']):
            environmental_details.extend([
                "expansive beach setting with visible horizon line",
                "tropical paradise atmosphere with palm trees in background", 
                "crystal clear water and white sand texture details",
                "natural beach lighting with sun reflections on water",
                "wide coastal landscape composition"
            ])
        
        # 🏙️ ГОРОДСКИЕ ЛОКАЦИИ  
        elif any(word in prompt_lower for word in ['city', 'город', 'street', 'улица', 'urban']):
            environmental_details.extend([
                "urban landscape with architectural elements in background",
                "city street context with buildings visible",
                "metropolitan environment showing scale and depth",
                "street photography composition with environmental storytelling"
            ])
        
        # 🏢 ОФИСНЫЕ ЛОКАЦИИ
        elif any(word in prompt_lower for word in ['office', 'офис', 'business', 'деловой']):
            environmental_details.extend([
                "professional business environment with modern interior",
                "office space context with furniture and design elements visible",
                "corporate setting atmosphere with proper lighting"
            ])
        
        # 🌳 ПРИРОДНЫЕ ЛОКАЦИИ
        elif any(word in prompt_lower for word in ['park', 'парк', 'nature', 'природа', 'forest', 'лес']):
            environmental_details.extend([
                "natural outdoor setting with lush greenery in background",
                "park or garden environment with trees and landscape visible",
                "organic natural lighting and atmospheric depth"
            ])
        
        # 🌍 УНИВЕРСАЛЬНЫЕ ENVIRONMENTAL ДЕТАЛИ (для любой локации)
        if environmental_details:  # Если локация определена
            environmental_details.extend([
                "environmental storytelling through background composition",
                "contextual framing showing subject's relationship to surroundings",
                "atmospheric depth with foreground, midground, and background elements"
            ])
        
        return environmental_details

    def _needs_translation(self, text: str) -> bool:
        """Определяет нужен ли перевод текста с русского на английский"""
        # Простая проверка на наличие кириллицы
        return bool(re.search(r'[а-яё]', text.lower()))
    
    def _translate_to_english(self, text: str) -> str:
        """Переводит промпт с русского на английский с акцентом на фоны и локации"""
        
        # 🌍 РАСШИРЕННЫЙ СЛОВАРЬ ПЕРЕВОДОВ для фонов и локаций
        translations = {
            # === БАЗОВЫЕ ФРАЗЫ ===
            'мой портрет': 'my portrait',
            'портрет': 'portrait',
            'фото': 'photo',
            'изображение': 'image',
            'картинка': 'picture',
            'мужчина': 'man',
            'женщина': 'woman',
            'девушка': 'woman',
            'парень': 'man',
            
            # === ОДЕЖДА И СТИЛЬ ===
            'в костюме': 'in suit',
            'костюм': 'suit',
            'деловой костюм': 'business suit',
            'строгий костюм': 'formal suit',
            'модный костюм': 'stylish suit',
            'современная одежда': 'modern clothes',
            'стильная одежда': 'stylish clothes',
            'модная одежда': 'fashionable clothes',
            'деловая одежда': 'business attire',
            'формальная одежда': 'formal attire',
            'повседневная одежда': 'casual clothes',
            'элегантная одежда': 'elegant attire',
            
            # === ТИПЫ ФОТО ===
            'деловой портрет': 'business portrait',
            'профессиональный портрет': 'professional portrait',
            'в полный рост': 'full body',
            'полный рост': 'full body',
            'по пояс': 'half body',
            'крупный план': 'close-up',
            
            # === ФОНЫ И ЛОКАЦИИ (КАК В ПРИМЕРЕ) ===
            'на фоне': 'in front of',
            'фон': 'background',
            'задний план': 'background',
            
            # АРХИТЕКТУРА И ЗДАНИЯ
            'бурдж халифа': 'Burj Khalifa',
            'бурж халифа': 'Burj Khalifa', 
            'небоскреб': 'skyscraper',
            'высотное здание': 'high-rise building',
            'башня': 'tower',
            'здание': 'building',
            'архитектура': 'architecture',
            'современное здание': 'modern building',
            'стеклянное здание': 'glass building',
            'офисное здание': 'office building',
            'бизнес центр': 'business center',
            'торговый центр': 'shopping center',
            
            # ГОРОДА И СТРАНЫ
            'дубай': 'Dubai',
            'дубаи': 'Dubai',
            'москва': 'Moscow',
            'нью-йорк': 'New York',
            'лондон': 'London',
            'париж': 'Paris',
            'токио': 'Tokyo',
            'шанхай': 'Shanghai',
            'сингапур': 'Singapore',
            'гонконг': 'Hong Kong',
            
            # ОФИСЫ И РАБОЧИЕ МЕСТА
            'офис': 'office',
            'кабинет': 'office',
            'рабочее место': 'workplace',
            'переговорная': 'meeting room',
            'конференц-зал': 'conference room',
            'приемная': 'reception',
            'коворкинг': 'coworking space',
            'современный офис': 'modern office',
            'стеклянный офис': 'glass office',
            
            # УЛИЦЫ И ГОРОДСКАЯ СРЕДА
            'улица': 'street',
            'городская улица': 'city street',
            'центр города': 'city center',
            'деловой район': 'business district',
            'финансовый район': 'financial district',
            'площадь': 'square',
            'набережная': 'embankment',
            'парк': 'park',
            'сквер': 'square park',
            
            # ИНТЕРЬЕРЫ
            'интерьер': 'interior',
            'помещение': 'room',
            'зал': 'hall',
            'холл': 'lobby',
            'вестибюль': 'lobby',
            'лобби': 'lobby',
            'студия': 'studio',
            'лофт': 'loft',
            'современный интерьер': 'modern interior',
            'минималистичный интерьер': 'minimalist interior',
            
            # ОСВЕЩЕНИЕ И ВРЕМЯ
            'дневное время': 'daytime',
            'день': 'daytime',
            'утро': 'morning',
            'вечер': 'evening',
            'закат': 'sunset',
            'рассвет': 'sunrise',
            'золотой час': 'golden hour',
            'естественное освещение': 'natural lighting',
            'дневной свет': 'daylight',
            'солнечный свет': 'sunlight',
            'мягкий свет': 'soft lighting',
            'яркий свет': 'bright lighting',
            
            # ХАРАКТЕРИСТИКИ И КАЧЕСТВА
            'уверенный': 'confident',
            'успешный': 'successful',
            'деловой': 'business',
            'профессиональный': 'professional',
            'современный': 'modern',
            'стильный': 'stylish',
            'элегантный': 'elegant',
            'роскошный': 'luxury',
            'престижный': 'prestigious',
            'высокий класс': 'high-end',
            
            # ТЕХНИЧЕСКИЕ ТЕРМИНЫ
            'четкий фокус': 'sharp focus',
            'резкий фокус': 'sharp focus',
            'реалистичное освещение': 'realistic lighting',
            'кинематографичная глубина': 'cinematic depth of field',
            'высокая детализация': 'high detail',
            'детализация': 'detail',
            'качество': 'quality',
            'разрешение': 'resolution',
            
            # ЭСТЕТИКА И СТИЛЬ
            'городская роскошь': 'urban luxury',
            'роскошная эстетика': 'luxury aesthetic',
            'деловая эстетика': 'business aesthetic',
            'современная эстетика': 'modern aesthetic',
            'минималистичная эстетика': 'minimalist aesthetic',
            'промышленная эстетика': 'industrial aesthetic',
            
            # ПОЗЫ И ДЕЙСТВИЯ
            'стоящий': 'standing',
            'стоя': 'standing',
            'сидящий': 'sitting',
            'идущий': 'walking',
            'смотрящий': 'looking',
            'позирующий': 'posing',
            'с руками в карманах': 'with hands in pockets',
            'скрещенные руки': 'crossed arms',
            'уверенная поза': 'confident pose',
            'естественная поза': 'natural pose',
        }
        
        # 🔄 ПОШАГОВЫЙ ПЕРЕВОД с сохранением порядка слов
        result = text.lower()
        
        # Сначала переводим длинные фразы (чтобы избежать конфликтов)
        sorted_translations = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)
        
        for russian, english in sorted_translations:
            if russian in result:
                # Используем границы слов для точного перевода
                import re
                pattern = r'\b' + re.escape(russian) + r'\b'
                result = re.sub(pattern, english, result)
                logger.debug(f"[Translation] '{russian}' → '{english}'")
        
        # ✅ КАПИТАЛИЗАЦИЯ для имен собственных
        proper_nouns = ['dubai', 'burj khalifa', 'moscow', 'new york', 'london', 'paris', 'tokyo']
        for noun in proper_nouns:
            if noun in result:
                capitalized = ' '.join(word.capitalize() for word in noun.split())
                result = result.replace(noun, capitalized)
        
        # 🧹 ЧИСТКА: убираем лишние пробелы
        result = ' '.join(result.split())
        
        logger.info(f"[Translation] Переведено: '{text}' → '{result}'")
        return result

    def is_available(self) -> bool:
        """Проверяет доступность сервиса обработки промптов"""
        # Новая система всегда доступна (не зависит от OpenAI)
        return True

    def get_negative_prompt(self, avatar_type: str) -> str:
        """
        Создает оптимизированный negative prompt для улучшения качества генерации
        
        Args:
            avatar_type: Тип аватара ("portrait")
            
        Returns:
            str: Negative prompt для FLUX Pro
        """
        # Базовые негативы для борьбы с артефактами
        base_negatives = [
            "blurry",
            "low quality",
            "worst quality", 
            "bad anatomy",
            "bad hands",
            "mutated fingers",
            "extra fingers",
            "missing fingers",
            "deformed",
            "disfigured",
            "watermark",
            "signature",
            "text",
            "logo"
        ]
        
        # Специфичные негативы для портретов
        if avatar_type == "portrait":
            portrait_negatives = [
                "plastic skin",
                "waxy skin", 
                "artificial skin texture",
                "over-smoothed skin",
                "fake eyes",
                "lifeless eyes",
                "artificial lighting",
                "cartoon",
                "anime",
                "drawing",
                "painting",
                "illustration",
                "3d render",
                "cgi"
            ]
            base_negatives.extend(portrait_negatives)
        
        # Объединяем все негативы
        negative_prompt = ", ".join(base_negatives)
        
        logger.debug(f"[Negative Prompt] Создан для {avatar_type}: {len(negative_prompt)} символов")
        return negative_prompt