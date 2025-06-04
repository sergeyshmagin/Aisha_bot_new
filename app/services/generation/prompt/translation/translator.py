"""
Модуль перевода промптов через GPT API
"""
import re
import aiohttp
from typing import Optional

from app.core.config import settings
from app.core.logger import get_logger
from app.shared.utils.openai import get_openai_headers

logger = get_logger(__name__)


class PromptTranslator:
    """Переводчик промптов для генерации изображений"""
    
    def __init__(self):
        self.model = "gpt-4o"
    
    async def translate_with_gpt(self, russian_text: str) -> str:
        """
        Переводит промпт с русского на английский через GPT API
        Сохраняет технические термины и профессиональную терминологию
        """
        if not settings.OPENAI_API_KEY:
            logger.warning("Отсутствует API ключ OpenAI, используем локальный перевод")
            return self.translate_to_english(russian_text)
        
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
                        return self.translate_to_english(russian_text)
        
        except Exception as e:
            logger.error(f"Ошибка GPT перевода: {e}")
            return self.translate_to_english(russian_text)
    
    def needs_translation(self, text: str) -> bool:
        """Определяет нужен ли перевод текста"""
        cyrillic_pattern = re.compile(r'[а-яё]', re.IGNORECASE)
        return bool(cyrillic_pattern.search(text))
    
    def translate_to_english(self, text: str) -> str:
        """
        Простой локальный перевод основных терминов
        Используется как fallback когда GPT недоступен
        """
        # Базовый словарь для перевода
        translation_dict = {
            # Основные термины
            "мужчина": "man",
            "женщина": "woman", 
            "девушка": "girl",
            "парень": "guy",
            "человек": "person",
            
            # Одежда
            "костюм": "suit",
            "платье": "dress",
            "рубашка": "shirt",
            "футболка": "t-shirt",
            "джинсы": "jeans",
            
            # Места
            "офис": "office",
            "улица": "street",
            "дом": "house", 
            "комната": "room",
            "парк": "park",
            "кафе": "cafe",
            
            # Эмоции и позы
            "улыбается": "smiling",
            "серьезный": "serious",
            "стоит": "standing",
            "сидит": "sitting",
            
            # Технические термины
            "портрет": "portrait",
            "полный рост": "full body",
            "крупный план": "close-up",
            "профиль": "profile",
            
            # Освещение
            "естественный свет": "natural light",
            "студийный свет": "studio light",
            "мягкий свет": "soft light",
            
            # Цвета
            "черный": "black",
            "белый": "white",
            "красный": "red",
            "синий": "blue",
            "зеленый": "green",
            "желтый": "yellow",
            
            # Времена года и погода
            "зима": "winter",
            "лето": "summer",
            "весна": "spring",
            "осень": "autumn",
            "солнечно": "sunny",
            "дождь": "rain"
        }
        
        # Переводим по словам
        words = text.split()
        translated_words = []
        
        for word in words:
            # Убираем знаки препинания для поиска
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in translation_dict:
                # Переводим и сохраняем оригинальную пунктуацию
                translated = translation_dict[clean_word]
                if word != word.lower():  # Если было с заглавной буквы
                    translated = translated.capitalize()
                # Восстанавливаем знаки препинания
                for char in word:
                    if not char.isalnum():
                        translated += char
                translated_words.append(translated)
            else:
                translated_words.append(word)
        
        result = " ".join(translated_words)
        logger.info(f"[Local Translation] '{text}' → '{result}'")
        return result 