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

logger = get_logger(__name__)


class PromptProcessingService:
    """Сервис для создания детальных профессиональных промптов"""
    
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o"
    
    async def process_prompt(self, user_prompt: str, avatar_type: str) -> Dict[str, Any]:
        """
        Обрабатывает пользовательский промпт для FLUX Pro v1.1 Ultra
        Создает фотореалистичный промпт по шпаргалке и оптимизированный negative prompt
        
        Args:
            user_prompt: Промпт от пользователя
            avatar_type: Тип аватара (portrait, style, etc.)
            
        Returns:
            dict: Результат обработки с processed prompt и negative prompt
        """
        start_time = time.time()
        
        try:
            logger.info(f"[Prompt Processing] Начата обработка: '{user_prompt[:50]}...'")
            
            # 🎯 1. ПЕРЕВОДИМ ЧЕРЕЗ GPT API если нужно
            if self._needs_translation(user_prompt):
                translated_prompt = await self._translate_with_gpt(user_prompt)
                logger.info(f"[GPT Translation] '{user_prompt}' → '{translated_prompt}'")
            else:
                translated_prompt = user_prompt
            
            # 🎯 2. СОЗДАЕМ ДЕТАЛЬНЫЙ ФОТОРЕАЛИСТИЧНЫЙ ПРОМПТ 
            processed_prompt = await self.create_enhanced_detailed_prompt(translated_prompt, avatar_type)
            
            # 🎯 3. СОЗДАЕМ ОПТИМИЗИРОВАННЫЙ NEGATIVE PROMPT
            negative_prompt = self.get_negative_prompt(avatar_type)
            
            # 🎯 4. ДЛЯ FLUX PRO - ВСТРАИВАЕМ НЕГАТИВЫ В ОСНОВНОЙ ПРОМПТ
            # LEGACY: Style аватары больше не поддерживаются
            # if avatar_type == "style":
            #     # Style аватары используют FLUX Pro - встраиваем негативы
            #     key_negatives = [
            #         "plastic skin", "airbrushed", "over-processed", 
            #         "extra fingers", "deformed hands", "multiple faces",
            #         "cartoon", "cgi", "ultra-detailed", "8k"
            #     ]
            #     negative_terms = ", ".join(key_negatives)
            #     final_prompt = f"{processed_prompt}. [AVOID: {negative_terms}]"
            #     result_negative = None
            #     
            #     logger.info(f"[FLUX Pro] Добавлены негативные термины в основной промпт")
            #     
            # else:
            
            # Теперь все аватары используют LoRA (портретные) - negative prompt отдельно
            final_prompt = processed_prompt
            result_negative = negative_prompt
            
            logger.info(f"[LoRA] Negative prompt создан: {len(negative_prompt)} символов")
            
            processing_time = time.time() - start_time
            
            # ✅ РЕЗУЛЬТАТ
            result = {
                "original": user_prompt,
                "processed": final_prompt,
                "negative_prompt": result_negative,
                "translation_needed": self._needs_translation(user_prompt),
                "processing_time": processing_time
            }
            
            logger.info(f"[Prompt Processing] Завершено за {processing_time:.2f}с")
            logger.info(f"Итоговый промпт: {len(final_prompt)} символов")
            
            return result
            
        except Exception as e:
            logger.exception(f"Ошибка обработки промпта: {e}")
            # Fallback к простой обработке
            return {
                "original": user_prompt,
                "processed": user_prompt,
                "negative_prompt": self.get_negative_prompt(avatar_type),
                "translation_needed": False,
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
        УЛУЧШАЕТ существующий промпт пользователя, НЕ заменяет его!
        Добавляет технические детали к оригинальному промпту
        """
        
        prompt_lower = base_prompt.lower()
        
        # 🚀 РЕЖИМ УЛУЧШЕНИЯ: Если промпт уже детальный - НЕ ТРОГАЕМ!
        if len(base_prompt) > 200 and any(tech in prompt_lower for tech in [
            'shot on', 'canon', 'nikon', 'sony', 'lighting', 'professional', 
            'portrait photo', 'sharp focus', 'realistic'
        ]):
            logger.info(f"[Smart Mode] Промпт уже детальный ({len(base_prompt)} символов) - возвращаем как есть")
            return base_prompt
        
        # 🎯 АНАЛИЗИРУЕМ что УЖЕ ЕСТЬ в промпте
        has_shot_type = any(word in prompt_lower for word in ['full-body', 'half-body', 'portrait photo', 'portrait of'])
        has_technical = any(word in prompt_lower for word in ['shot on', 'canon', 'nikon', 'sony', 'lens', 'mm'])
        has_lighting = any(word in prompt_lower for word in ['lighting', 'golden hour', 'studio', 'natural light'])
        has_quality = any(word in prompt_lower for word in ['sharp focus', 'high detail', 'realistic', 'professional'])
        
        # 🔧 НАЧИНАЕМ С ОРИГИНАЛЬНОГО ПРОМПТА
        enhanced_parts = [base_prompt]
        
        # ✅ ДОБАВЛЯЕМ ТОЛЬКО ТО, ЧЕГО НЕТ
        
        # 1. Добавляем тип кадра только если его нет
        if not has_shot_type:
            if any(word in prompt_lower for word in ['standing', 'full body']):
                enhanced_parts.append("full-body portrait photo style")
            elif any(word in prompt_lower for word in ['portrait', 'headshot']):
                enhanced_parts.append("portrait photo style")
            else:
                enhanced_parts.append("professional portrait style")
        
        # 2. Добавляем технические детали кожи только если их нет
        if not any(word in prompt_lower for word in ['skin texture', 'natural', 'realistic']):
            enhanced_parts.append("natural skin texture with authentic detail")
        
        # 3. Добавляем глаза только если их нет
        if not any(word in prompt_lower for word in ['eyes', 'eye', 'gaze']):
            enhanced_parts.append("well-defined eyes with natural catchlight")
        
        # 4. Добавляем освещение только если его нет
        if not has_lighting:
            lighting_options = [
                "professional lighting",
                "natural lighting", 
                "studio lighting",
                "soft lighting"
            ]
            enhanced_parts.append(random.choice(lighting_options))
        
        # 5. Добавляем камеру только если её нет
        if not has_technical:
            camera_options = [
                "shot on professional camera",
                "photographed with portrait lens",
                "captured with high-end camera"
            ]
            enhanced_parts.append(random.choice(camera_options))
        
        # 6. Добавляем качество только если его нет
        if not has_quality:
            enhanced_parts.append("sharp focus, high detail")
        
        # 🎯 СПЕЦИАЛЬНАЯ ОБРАБОТКА ЛИЦА для full-body (НОВОЕ!)
        if "face" not in prompt_lower and "portrait" not in prompt_lower:
            enhanced_parts.append("extremely sharp and realistic face, defined eyebrows, high-fidelity facial features")
        
        # 🎯 ДОПОЛНИТЕЛЬНАЯ ДЕТАЛИЗАЦИЯ ЛИЦА И ГЛАЗ для LoRA
        if "eyes" not in prompt_lower or "face" not in prompt_lower:
            enhanced_parts.append("realistic face with visible pores, authentic shadows, well-defined eyes with natural catchlight")
        
        # 🎯 LORA-СПЕЦИФИЧНАЯ ПОДДЕРЖКА для portrait аватаров
        if avatar_type == "portrait":
            enhanced_parts.append("LoRA trained full-body structure, no facial deformation, no duplicate features")
        
        # 🎯 УСИЛЕННЫЕ FULL-BODY ИНСТРУКЦИИ (НОВОЕ!)
        # Добавляем только если явно запрашивается full-body или если тип кадра не определен
        is_explicit_fullbody = any(word in prompt_lower for word in ['full body', 'standing', 'полный рост', 'full-body'])
        is_explicit_portrait = any(word in prompt_lower for word in ['portrait', 'headshot', 'портрет', 'крупный план'])
        
        if is_explicit_fullbody or (not has_shot_type and not is_explicit_portrait):
            # Добавляем мощные full-body инструкции только когда нужно
            enhanced_parts.append("show entire body from head to feet")
            enhanced_parts.append("complete figure visible in frame") 
            enhanced_parts.append("full body composition with proper proportions")
            enhanced_parts.append("wide shot to capture full silhouette")
            
            # 🌍 НОВЫЕ ENVIRONMENTAL И COMPOSITION ДЕТАЛИ (против селфи!)
            enhanced_parts.append("environmental perspective showing subject in context")
            enhanced_parts.append("step back camera angle for full scene composition")
            enhanced_parts.append("medium distance shot with background details visible")
            enhanced_parts.append("establish relationship between subject and environment")
            
            # 🏖️ СПЕЦИФИЧНЫЕ ENVIRONMENTAL ДЕТАЛИ по локации
            environmental_details = self._enhance_environmental_context(prompt_lower)
            if environmental_details:
                # Добавляем 2-3 самых релевантных environmental детали
                enhanced_parts.extend(environmental_details[:3])
        
        # 🔗 ОБЪЕДИНЯЕМ через запятые
        enhanced_prompt = ", ".join(enhanced_parts)
        
        # 🧹 ЧИСТКА
        enhanced_prompt = enhanced_prompt.replace(", ,", ",").replace("  ", " ").strip()
        
        logger.info(f"[Smart Enhancement] Оригинал: {len(base_prompt)} символов → Улучшенный: {len(enhanced_prompt)} символов")
        logger.info(f"[Smart Enhancement] Добавлено деталей: {len(enhanced_parts)-1}")
        
        return enhanced_prompt

    # def _analyze_clothing(self, prompt_lower: str) -> str:
    #     """LEGACY: Анализирует и детализирует одежду - НЕИСПОЛЬЗУЕТСЯ"""
    #     if any(word in prompt_lower for word in ['suit', 'business', 'formal']):
    #         return "wearing a tailored modern business suit with crisp details"
    #     elif any(word in prompt_lower for word in ['casual', 'relaxed']):
    #         return "wearing stylish casual attire with contemporary design"
    #     elif any(word in prompt_lower for word in ['elegant', 'luxury']):
    #         return "wearing elegant luxury clothing with sophisticated styling"
    #     else:
    #         return "wearing modern stylish clothes with clean lines"

    # def _analyze_location(self, prompt_lower: str) -> str:
    #     """LEGACY: Анализирует и детализирует локацию - НЕИСПОЛЬЗУЕТСЯ"""
    #     if "burj khalifa" in prompt_lower:
    #         return "standing confidently in front of the iconic Burj Khalifa in Dubai"
    #     elif "dubai" in prompt_lower:
    #         return "positioned against Dubai's modern skyline backdrop"
    #     elif any(word in prompt_lower for word in ['office', 'business']):
    #         return "in a contemporary office environment with professional atmosphere"
    #     elif any(word in prompt_lower for word in ['city', 'urban', 'street']):
    #         return "against an urban cityscape with architectural elements"
    #     elif any(word in prompt_lower for word in ['studio', 'indoor']):
    #         return "in a professional studio setting with controlled environment"
    #     else:
    #         return ""

    # def _get_pose_details(self, shot_type: str, prompt_lower: str) -> str:
    #     """LEGACY: Получает детали позы в зависимости от типа кадра - НЕИСПОЛЬЗУЕТСЯ"""
    #     if "full-body" in shot_type:
    #         poses = [
    #             "standing naturally with weight on one leg, both hands relaxed",
    #             "hands in pockets, slight tilt of head, natural smile",
    #             "relaxed standing pose with arms by sides and slight hip shift",
    #             "professional standing pose with one hand casually positioned",
    #             "natural full-body posture with authentic confidence",
    #             "dynamic standing position with engaging body language"
    #         ]
    #     elif "half-body" in shot_type:
    #         poses = [
    #             "confident upper body positioning with relaxed shoulders",
    #             "professional torso pose with natural arm placement",
    #             "engaging half-body stance with authentic presence"
    #         ]
    #     else:  # portrait
    #         poses = [
    #             "direct confident gaze with natural facial expression",
    #             "authentic head positioning with engaging eye contact",
    #             "professional portrait pose with genuine emotion"
    #         ]
    #     
    #     return random.choice(poses)

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

    # async def _translate_prompt(self, prompt: str) -> str:
    #     """LEGACY: Переводит промпт с русского на английский (заглушка) - НЕИСПОЛЬЗУЕТСЯ"""
    #     # TODO: Реализовать перевод через API или библиотеку
    #     return prompt
    
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

    def get_negative_prompt(self, avatar_type: str) -> str:
        """
        Создает революционный negative prompt для FLUX Pro v1.1 Ultra
        СПЕЦИАЛЬНО для борьбы с мыльностью и неестественными глазами
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
        # LEGACY: Style аватары больше не поддерживаются
        # if avatar_type == "style":
        #     # Для стилевых - борьба с артефактами композиции
        #     specific_negatives = [
        #         "inconsistent lighting", "mixed styles", "poor composition",
        #         "floating elements", "unrealistic proportions", "style mixing"
        #     ]
        # else:
        
        if avatar_type == "portrait":
            # Для портретов - максимальный фокус на естественности лица
            specific_negatives = [
                "unnatural facial features", "distorted face", "fake expression",
                "artificial smile", "forced expression", "mask-like face",
                "symmetrical face", "perfect symmetry", "uncanny valley"
            ]
        else:
            # Универсальные для всех типов
            specific_negatives = [
                "unnatural appearance", "artificial look", "fake rendering",
                "poor anatomy", "unrealistic features"
            ]
        
        # 🎯 НОВЫЕ НЕГАТИВЫ ПРОТИВ НЕЖЕЛАТЕЛЬНОЙ РАСТИТЕЛЬНОСТИ
        facial_hair_negatives = [
            # Против бороды и щетины
            "stubble", "beard", "mustache", "facial hair", "five o'clock shadow",
            "unshaven", "scruff", "whiskers", "goatee", "sideburns",
            "patchy beard", "scruffy", "unkempt facial hair", "rough stubble",
            
            # Против клочковатой растительности
            "patchy hair", "uneven hair growth", "sparse facial hair",
            "random hair patches", "irregular stubble", "messy facial hair"
        ]
        
        # 🎯 НОВЫЕ НЕГАТИВЫ ДЛЯ ЛИЦА И КОМПОЗИЦИИ (НОВОЕ!)
        face_composition_negatives = [
            # Против деформаций лица
            "symmetrical eyes", "flat face", "melted face", "textureless face", 
            "generic male face", "3d anime style eyes", "perfect symmetrical face",
            "artificial facial structure", "clone face", "mannequin face",
            
            # Против композиционных проблем
            "floating head", "disconnected body parts", "incorrect proportions",
            "oversized head", "tiny head", "body-head mismatch", "anatomical errors"
        ]
        
        # 🎯 ОБЪЕДИНЯЕМ ВСЕ НЕГАТИВЫ
        all_negatives = (clarity_negatives + eye_negatives + processing_negatives + 
                        technical_negatives + style_negatives + specific_negatives +
                        facial_hair_negatives + face_composition_negatives)
        
        # Создаем строку негативов
        negative_prompt = ", ".join(all_negatives)
        
        # ✅ ЛОГИРОВАНИЕ
        logger.info(f"[ENHANCED Negative] Революционный negative prompt: {len(all_negatives)} терминов против мыльности и неестественных глаз")
        logger.debug(f"[ENHANCED Negative] Ключевые негативы: мыльность={len(clarity_negatives)}, глаза={len(eye_negatives)}")
        
        return negative_prompt

    def is_available(self) -> bool:
        """Проверяет доступность сервиса обработки промптов"""
        # Новая система всегда доступна (не зависит от OpenAI)
        return True
    
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

    # def _enhance_simple_prompt(self, english_prompt: str, avatar_type: str) -> str:
    #     """
    #     LEGACY: Умное улучшение простых промптов согласно примеру пользователя
    #     НЕИСПОЛЬЗУЕТСЯ - имеет ошибки (неопределенная переменная enhanced_parts)
    #     Заменено на create_enhanced_detailed_prompt
    #     """
    #     
    #     # 📋 АНАЛИЗ ПРОМПТА (учитываем оригинальные русские слова)
    #     prompt_lower = english_prompt.lower()
    #     
    #     # 🎯 ОПРЕДЕЛЯЕМ ТИП КАДРА из переведенного промпта
    #     if any(word in prompt_lower for word in ['full body', 'standing', 'полный рост', 'full-body']):
    #         shot_type = "full-body portrait photo"
    #         # 🚨 УСИЛЕННЫЕ ИНСТРУКЦИИ для FULL BODY (НОВОЕ!)
    #         enhanced_parts.append("show entire body from head to feet")
    #         enhanced_parts.append("complete figure visible in frame")
    #         enhanced_parts.append("full body composition with proper proportions")
    #     elif any(word in prompt_lower for word in ['half body', 'по пояс', 'half-body']):
    #         shot_type = "half-body portrait photo" 
    #     elif any(word in prompt_lower for word in ['portrait', 'портрет', 'headshot', 'business portrait']):
    #         shot_type = "portrait photo"
    #     else:
    #         # По умолчанию full body как в примере
    #         shot_type = "full-body portrait photo"
    #         # 🚨 ДОБАВЛЯЕМ FULL BODY по умолчанию
    #         enhanced_parts.append("show entire body from head to feet")
    #         enhanced_parts.append("full body composition")
    #     
    #     # ... остальной код был с ошибками
    #     logger.info(f"[Enhanced] '{english_prompt}' → 'LEGACY FUNCTION'")
    #     return english_prompt  # Fallback 