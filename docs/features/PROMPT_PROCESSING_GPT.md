# 🤖 Умная обработка промптов через GPT

## 📋 Обзор

Система автоматической обработки пользовательских промптов через OpenAI GPT-4o для создания оптимальных промптов для генерации изображений на Flux PRO Stable Diffusion с LoRA адаптерами.

## ✨ Возможности

### 🔄 Автоматический перевод
- Распознавание языка пользовательского промпта
- Автоматический перевод с русского на английский
- Сохранение художественного видения

### ⚡ Оптимизация для Flux PRO
- Добавление технических параметров качества
- Структурирование промпта для лучших результатов
- Специализированная обработка для разных типов аватаров

### 🎭 Типизированная обработка
- **Портретные аватары**: акцент на детали лица, освещение, профессиональная фотография
- **Стилевые аватары**: акцент на художественный стиль, атмосферу, технику

## 🛠️ Техническая реализация

### Архитектура
```
Пользователь → Telegram → FSM → PromptProcessingService → GPT-4o → Optimized Prompt → FAL AI
```

### Компоненты

#### 1. `PromptProcessingService`
```python
class PromptProcessingService:
    async def process_prompt(self, user_prompt: str, avatar_type: str) -> dict:
        """
        Обрабатывает пользовательский промпт
        
        Returns:
        {
            "original": str,           # Оригинальный промпт
            "processed": str,          # Обработанный GPT промпт
            "translation_needed": bool # Нужен ли был перевод
        }
        """
```

#### 2. Системные промпты
Специализированные инструкции для GPT в зависимости от типа аватара:

**Для портретов:**
```
- Акцентируй внимание на деталях лица и выражении
- Добавляй параметры освещения (studio lighting, natural light)
- Используй термины: "portrait", "detailed face", "professional photography"
- Добавляй параметры качества: "high resolution", "sharp focus", "detailed"
```

**Для стилей:**
```
- Акцентируй художественный стиль и атмосферу
- Добавляй описания техники и материалов
- Используй термины стилей: "digital art", "concept art", "illustration"
- Добавляй описания композиции и настроения
```

## 📊 Пример работы

### Вход и выход

**Пользователь вводит (на русском):**
```
деловой портрет в костюме
```

**GPT обрабатывает:**
```
professional portrait in business attire, studio lighting, sharp focus, detailed face, high resolution
```

**Финальный промпт (с триггерными словами):**
```
professional portrait of ohwx person in business attire, studio lighting, sharp focus, detailed face, high resolution
```

## 🎯 Пользовательский опыт

### До обработки
1. Пользователь вводит промпт на любом языке
2. Система показывает: "🤖 Обрабатываю ваш промпт..."

### Во время обработки
```
🤖 Обрабатываю ваш промпт...

📝 Ваш промпт: деловой портрет в костюме

⚡ Что происходит:
• Переводим на английский (если нужно)
• Оптимизируем для Flux PRO
• Добавляем технические параметры
• Подготавливаем к генерации

⏳ Это займет несколько секунд...
```

### После обработки
```
🎨 Создаю ваше изображение...

📝 Оригинальный промпт: деловой портрет в костюме
🔄 Обработанный промпт: professional portrait in business attire, studio lighting, sharp focus...
⚡ Модель: FLUX 1.1 Ultra
🖼️ Формат: Квадрат (1:1)
```

## ⚙️ Конфигурация

### Переменные окружения
```env
# OpenAI API для обработки промптов
OPENAI_API_KEY=your_openai_api_key_here
```

### Параметры GPT
```python
{
    "model": "gpt-4o",
    "temperature": 0.3,  # Низкая температура для стабильности
    "max_tokens": 300,   # Достаточно для промпта
    "top_p": 0.9
}
```

## 🔒 Fallback и обработка ошибок

### Без API ключа
- Система использует оригинальный промпт без обработки
- Пользователь не видит ошибок
- Логирование предупреждений

### При ошибке API
- Автоматический fallback на оригинальный промпт
- Логирование ошибок
- Прозрачность для пользователя

### Тестовый режим
```env
OPENAI_API_KEY="test_key"  # Обработка отключена
```

## 📈 Метрики и аналитика

### Сохранение метаданных
```python
generation.metadata = {
    'prompt_processing': {
        'original_prompt': str,      # Оригинальный промпт
        'processed_prompt': str,     # Обработанный промпт
        'translation_needed': bool,  # Нужен ли был перевод
        'processor_available': bool  # Был ли доступен GPT
    }
}
```

### Анализ использования
- Количество обработанных промптов
- Процент переводов с русского
- Доступность GPT сервиса
- Время обработки

## 🧪 Тестирование

### Unit тесты
```python
class TestPromptProcessingService:
    async def test_process_prompt_russian_to_english()
    async def test_process_prompt_already_english()
    async def test_process_prompt_without_api_key()
    def test_detect_translation_needed()
    def test_get_system_prompt_portrait()
    def test_get_system_prompt_style()
```

### Интеграционные тесты
- Полный цикл: промпт → обработка → генерация
- Различные типы аватаров
- Различные языки промптов

## 🚀 Производительность

### Время обработки
- **GPT API**: 1-3 секунды
- **Fallback**: мгновенно
- **Общий процесс**: 30-60 секунд (включая генерацию)

### Оптимизации
- Низкая температура (0.3) для стабильности
- Ограничение токенов (300) для скорости
- Асинхронная обработка
- Graceful fallback

## 📚 Примеры промптов

### Русский → Английский
```
художественный портрет в стиле ренессанс
↓
artistic portrait in renaissance style, oil painting technique, dramatic lighting, classical composition, highly detailed
```

### Английский → Оптимизированный
```
superhero photo
↓
dynamic superhero portrait, action pose, vibrant colors, comic book style, detailed costume, cinematic lighting, high resolution
```

### Смешанный язык
```
casual портрет in coffee shop
↓
casual portrait in coffee shop, warm natural lighting, cozy atmosphere, professional photography, detailed face
```

## ✅ Преимущества

1. **Удобство**: пользователи могут писать на родном языке
2. **Качество**: автоматическая оптимизация промптов
3. **Надежность**: graceful fallback при ошибках
4. **Прозрачность**: пользователь видит процесс обработки
5. **Специализация**: разные подходы для разных типов аватаров

## 🎉 Результат

Пользователи получают значительно лучшее качество генерации без необходимости изучать оптимальные английские промпты для Stable Diffusion. 