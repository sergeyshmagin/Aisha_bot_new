# Cinematic Prompt Service - Документация

## Обзор

`CinematicPromptService` - это продвинутый сервис для создания детальных кинематографических промптов в стиле профессиональной фотографии 8K качества. Сервис генерирует промпты с максимальной детализацией сцены, позы, ракурса, освещения и технических параметров.

## Функциональность

### Основные возможности:

1. **Создание кинематографических промптов** с детальными описаниями
2. **Автоматический перевод** с русского/казахского на английский
3. **Определение типа кадра** (full-body, half-body, close-up)
4. **Описание освещения** и атмосферы
5. **Технические характеристики** камеры и съемки
6. **Цветовая палитра** и качество изображения

### Стиль создаваемых промптов:

```
TOK, A high-quality, cinematic, ultra-realistic close-up portrait photograph, 
captured by a professional medium-format digital camera, in style of super-detailed 8K resolution imagery, 
featuring warm, directional side lighting during the golden hour. 
The composition is expertly framed with the subject positioned optimally in the frame, 
featuring a confident man with contemporary styling, positioned with natural elegance and authentic body language, 
gazing directly at the camera with engaging intensity and natural charisma...
```

## Архитектура

### Основной метод:

```python
async def create_cinematic_prompt(
    user_prompt: str, 
    avatar_type: str = "portrait",
    style_preset: str = "photorealistic"
) -> Dict[str, Any]
```

### Процесс создания промпта:

1. **Проверка перевода**: Определяет нужен ли перевод с кириллицы
2. **Анализ существующего промпта**: Проверяет нужны ли улучшения
3. **Сборка по блокам**:
   - Префикс TOK для портретов
   - Технические характеристики
   - Тип кадра
   - Освещение
   - Композиция
   - Описание субъекта
   - Поза и ракурс
   - Окружение
   - Технические параметры камеры
   - Цветовая палитра
   - Спецификации качества

## Компоненты системы

### 1. Технические характеристики изображения
```python
def _build_technical_specifications(self) -> List[str]:
    return [
        "A high-quality",
        "cinematic", 
        "ultra-realistic",
        "8K resolution imagery"
    ]
```

### 2. Определение типа кадра
- **Full-body portrait** - для полного роста
- **Half-body portrait** - до пояса  
- **Close-up portrait** - крупный план
- **Medium portrait** - по умолчанию

### 3. Описание освещения
Анализирует контекст и создает соответствующее описание:
- Golden hour lighting
- Studio lighting
- Natural window light
- Outdoor lighting
- Dramatic lighting

### 4. Описание позы
Создает детальное описание языка тела в зависимости от стиля:
- Confident poses
- Relaxed poses  
- Professional poses
- Natural poses

### 5. Окружение и фон
Специальные описания для разных локаций:
- Dubai/Burj Khalifa
- Office/Business
- Studio
- Outdoor/Street
- Nature/Park
- Restaurant/Cafe

### 6. Технические параметры камеры
```python
def _create_camera_specifications(self) -> List[str]:
    return [
        "captured by a professional medium-format digital camera",
        "shot with 85mm portrait lens at f/2.8 for optimal sharpness",
        "The depth of field is exceptional, ensuring razor-sharp focus on the subject",
        "professional bokeh with smooth background transition"
    ]
```

### 7. Цветовая палитра
Адаптивные описания в зависимости от тональности:
- Warm tones (golden, amber)
- Cool tones (blue, white)
- Dramatic contrasts
- Natural earth tones

### 8. Спецификации качества
```python
def _create_quality_specifications(self) -> List[str]:
    return [
        "well-defined eyes with natural catchlight and authentic iris detail",
        "natural skin texture with fine detail and visible pores",
        "authentic facial features with realistic proportions",
        "sharp focus with optimal detail retention",
        "no facial deformation, no duplicate features",
        "high-end editorial photography style with cinematic quality"
    ]
```

## Интеграция с переводчиком

### GPT-4 перевод (приоритетный):
```python
async def _translate_with_gpt(self, russian_text: str) -> str:
    system_prompt = """Ты профессиональный переводчик промптов для AI-генерации изображений.
    
    ПРАВИЛА:
    1. Сохраняй все технические термины фотографии
    2. Переводи названия мест точно (Дубай → Dubai, Бурдж Халифа → Burj Khalifa)
    3. Сохраняй структуру и смысл
    4. НЕ добавляй лишних деталей, только точный перевод
    5. Сохраняй стиль и эмоциональность"""
```

### Fallback словарный перевод:
Базовый перевод распространенных терминов если GPT недоступен.

## Использование

### Пример использования:

```python
service = CinematicPromptService()

result = await service.create_cinematic_prompt(
    user_prompt="мужчина в костюме на фоне Бурдж Халифа",
    avatar_type="portrait",
    style_preset="photorealistic"
)

print(result["processed"])
# TOK, A high-quality, cinematic, ultra-realistic close-up portrait photograph...
```

### Результат метода:

```python
{
    "original": "мужчина в костюме на фоне Бурдж Халифа",
    "processed": "TOK, A high-quality, cinematic, ultra-realistic...",
    "enhancement_applied": True,
    "style": "cinematic_detailed",
    "word_count": 85,
    "technical_level": "professional"
}
```

## Интеграция с другими сервисами

### ImageAnalysisService
Использует `CinematicPromptService` для создания промптов на основе анализа фотографий:

```python
cinematic_result = await self.cinematic_service.create_cinematic_prompt(
    user_prompt=integrated_prompt,
    avatar_type=avatar_type,
    style_preset="photorealistic"
)
```

### PromptProcessingService  
Интегрирует кинематографический сервис в основной процесс обработки промптов:

```python
cinematic_result = await self.cinematic_service.create_cinematic_prompt(
    user_prompt=user_prompt,
    avatar_type=avatar_type,
    style_preset="photorealistic"
)
```

## Логирование

Сервис ведет детальное логирование всех этапов:

```
[Cinematic Prompt] Создание детального промпта: 'мужчина в костюме...'
[Translation] 'мужчина в костюме' → 'man in suit'
[Cinematic] Создан промпт: 847 символов
```

## Оптимизация

### Проверка на уже детальные промпты:
```python
def _is_already_cinematic(self, prompt: str) -> bool:
    # Проверяет наличие кинематографических индикаторов
    # и длину промпта > 300 символов
```

### Оптимизация финального промпта:
```python
def _optimize_prompt(self, prompt: str) -> str:
    # Удаляет дублирующиеся фразы и лишние пробелы
    # Убирает повторяющиеся элементы
```

## Преимущества

1. **Максимальная детализация** - промпты в стиле профессиональной фотографии
2. **Адаптивность** - учитывает контекст и создает подходящие описания
3. **Переводчик** - работает с русским и казахским языками
4. **Модульность** - легко интегрируется с другими сервисами
5. **Оптимизация** - избегает дублирования и ненужных деталей
6. **Fallback** - работает даже без GPT API

Этот сервис обеспечивает создание промптов максимального качества для получения кинематографических фотореалистичных изображений. 