# 🤖 Руководство по интеграции FAL AI

**Обновлено:** 15.01.2025  
**Статус:** ✅ Интеграция завершена  
**Версия:** v2.0 с поддержкой FLUX1.1 Ultra

## 📋 Обзор интеграции

FAL AI интеграция в Aisha v2 обеспечивает автоматический выбор оптимальной модели для обучения аватаров и генерации изображений. Поддерживает три основные модели с различными возможностями.

### 🎯 Поддерживаемые модели
- **FLUX LoRA Portrait Trainer** - специализация на портретах
- **FLUX Pro Trainer** - универсальное обучение
- **FLUX1.1 [pro] ultra Fine-tuned** - генерация с обученными моделями

## 🏗️ Архитектура интеграции

### Компоненты системы
```
app/services/fal/
├── fal_client.py              # Базовый клиент FAL AI
├── portrait_trainer.py        # Портретный тренер
├── pro_trainer.py            # Универсальный тренер
└── ultra_generator.py        # FLUX1.1 Ultra генератор

app/services/avatar/
└── fal_training_service.py   # Автоматический выбор модели
```

### Автоматический выбор модели
```python
class FALTrainingService:
    async def start_avatar_training(self, avatar_id, training_type, ...):
        if training_type == "portrait":
            # Специализированный портретный тренер
            return await self.portrait_trainer.train_avatar_async(...)
        else:
            # Универсальный тренер
            return await self.pro_trainer.train_avatar(...)
```

## 🎭 FLUX LoRA Portrait Trainer

### Специализация
**Оптимизирован для:** Портреты людей  
**Время обучения:** 3-15 минут  
**Endpoint:** `fal-ai/flux-lora-portrait-trainer`

### Ключевые параметры
```python
{
    "images_data_url": "https://storage.com/photos.zip",
    "trigger_phrase": "TOK_avatar123",
    "steps": 1000,                    # Шаги обучения
    "learning_rate": 0.0002,          # Скорость обучения
    "multiresolution_training": True, # Мультиразрешение
    "subject_crop": True,             # Автообрезка портретов
    "create_masks": True,             # Создание масок лица
    "webhook_url": "https://domain.com/webhook"
}
```

### Преимущества
- ⚡ **Быстрое обучение** - оптимизированный алгоритм
- 🎯 **Высокое качество** - специализация на лицах
- 🔍 **Автоматическая обработка** - обрезка и маски
- 💰 **Экономичность** - меньше вычислительных ресурсов

### Пример использования
```python
from app.services.fal.portrait_trainer import FALPortraitTrainer

trainer = FALPortraitTrainer()

result = await trainer.train_avatar_async(
    images_data_url="https://storage.com/user123_photos.zip",
    trigger_phrase="TOK_user123",
    steps=1000,
    learning_rate=0.0002,
    subject_crop=True,
    create_masks=True,
    webhook_url="https://aibots.kz/api/avatar/status_update?training_type=portrait"
)

print(f"Training started: {result}")
```

## 🎨 FLUX Pro Trainer

### Универсальность
**Оптимизирован для:** Любой контент  
**Время обучения:** 5-30 минут  
**Endpoint:** `fal-ai/flux-pro-trainer`

### Ключевые параметры
```python
{
    "images_data_url": "https://storage.com/photos.zip",
    "trigger_word": "TOK_avatar123",
    "iterations": 500,               # Итерации обучения
    "learning_rate": 1e-4,           # Скорость обучения
    "auto_captioning": True,         # Автоподписи
    "create_masks": True,            # Создание масок
    "priority": "quality",           # Приоритет: speed/quality
    "webhook_url": "https://domain.com/webhook"
}
```

### Преимущества
- 🌐 **Универсальность** - любые стили и объекты
- 🔧 **Гибкость** - множество настроек
- 📝 **Автоподписи** - автоматическое описание изображений
- 🎛️ **Контроль качества** - различные режимы

### Пример использования
```python
from app.services.fal.pro_trainer import FALProTrainer

trainer = FALProTrainer()

result = await trainer.train_avatar(
    images_data_url="https://storage.com/style_photos.zip",
    trigger_word="TOK_style123",
    iterations=500,
    learning_rate=1e-4,
    auto_captioning=True,
    priority="quality",
    webhook_url="https://aibots.kz/api/avatar/status_update?training_type=style"
)

print(f"Training started: {result['finetune_id']}")
```

## ⚡ FLUX1.1 [pro] ultra Fine-tuned

### Генерация изображений
**Оптимизирован для:** Генерация с обученными моделями  
**Разрешение:** До 2K (2048x2048)  
**Скорость:** 10x быстрее предыдущих версий  
**Endpoint:** `fal-ai/flux-pro/v1.1-ultra/finetuned`

### Ключевые параметры
```python
{
    "prompt": "TOK_avatar123 in business suit",
    "finetune_id": "lora:abc123def456",      # ID обученной модели
    "finetune_strength": 1.1,                # Сила влияния (0.0-2.0)
    "aspect_ratio": "1:1",                   # Соотношение сторон
    "num_images": 1,                         # Количество изображений
    "output_format": "jpeg",                 # Формат вывода
    "enable_safety_checker": True            # Проверка безопасности
}
```

### Рекомендуемые значения finetune_strength
- **Портреты:** 0.8-1.2
- **Стили:** 1.0-1.5
- **Объекты:** 0.6-1.0
- **Концепты:** 1.2-2.0

### Пример использования
```python
from app.services.fal.ultra_generator import FALUltraGenerator

generator = FALUltraGenerator()

result = await generator.generate_image(
    prompt="TOK_avatar123 professional headshot, business attire",
    finetune_id="lora:abc123def456",
    finetune_strength=1.1,
    aspect_ratio="1:1",
    num_images=1,
    output_format="jpeg"
)

print(f"Generated image: {result['images'][0]['url']}")
```

## 🔄 Сравнение моделей

### Таблица сравнения

| Критерий | Portrait Trainer | Pro Trainer | Ultra Generator |
|----------|------------------|-------------|-----------------|
| **Назначение** | Портреты людей | Универсальное | Генерация |
| **Время** | 3-15 мин | 5-30 мин | 10-30 сек |
| **Качество портретов** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Универсальность** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Скорость обучения** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | N/A |
| **Скорость генерации** | N/A | N/A | ⭐⭐⭐⭐⭐ |
| **Стоимость** | $ | $$ | $ |

### Рекомендации по выбору

**Используйте Portrait Trainer если:**
- У вас фотографии людей
- Нужно высокое качество лиц
- Важна скорость обучения
- Ограниченный бюджет

**Используйте Pro Trainer если:**
- Нужны стили или объекты
- Требуется максимальная гибкость
- Работаете с нестандартным контентом
- Качество важнее скорости

**Используйте Ultra Generator если:**
- Модель уже обучена
- Нужна быстрая генерация
- Требуется высокое разрешение
- Важно качество финального изображения

## ⚙️ Конфигурация

### Переменные окружения
```env
# FAL AI API
FAL_API_KEY=your_fal_api_key_here

# Webhook endpoints
FAL_WEBHOOK_URL=https://aibots.kz/api/avatar/status_update
FAL_WEBHOOK_PORTRAIT_URL=https://aibots.kz/api/avatar/status_update?training_type=portrait
FAL_WEBHOOK_STYLE_URL=https://aibots.kz/api/avatar/status_update?training_type=style

# Тестовый режим
FAL_TRAINING_TEST_MODE=true
FAL_ENABLE_WEBHOOK_SIMULATION=true
FAL_MOCK_TRAINING_DURATION=30

# Пресеты качества
FAL_PRESET_FAST={"portrait": {"steps": 500}, "general": {"iterations": 200}}
FAL_PRESET_BALANCED={"portrait": {"steps": 1000}, "general": {"iterations": 500}}
FAL_PRESET_QUALITY={"portrait": {"steps": 2500}, "general": {"iterations": 1000}}
```

### Настройки по умолчанию
```python
# Portrait Trainer
DEFAULT_PORTRAIT_SETTINGS = {
    "steps": 1000,
    "learning_rate": 0.0002,
    "multiresolution_training": True,
    "subject_crop": True,
    "create_masks": True
}

# Pro Trainer
DEFAULT_PRO_SETTINGS = {
    "iterations": 500,
    "learning_rate": 1e-4,
    "auto_captioning": True,
    "create_masks": True,
    "priority": "quality"
}

# Ultra Generator
DEFAULT_ULTRA_SETTINGS = {
    "finetune_strength": 1.1,
    "aspect_ratio": "1:1",
    "num_images": 1,
    "output_format": "jpeg",
    "enable_safety_checker": True
}
```

## 📡 Webhook система

### Единый endpoint
```
POST /api/avatar/status_update?training_type={portrait|style|ultra}
```

### Обработка разных типов
```python
@router.post("/avatar/status_update")
async def fal_webhook(request: Request):
    data = await request.json()
    training_type = request.query_params.get("training_type", "portrait")
    
    if training_type == "portrait":
        # Обработка Portrait Trainer
        model_url = data.get("result", {}).get("diffusers_lora_file", {}).get("url")
    elif training_type == "style":
        # Обработка Pro Trainer
        model_url = data.get("result", {}).get("finetune_id")
    elif training_type == "ultra":
        # Обработка Ultra Generator
        image_url = data.get("result", {}).get("images", [{}])[0].get("url")
    
    # Обновление статуса в БД
    await update_avatar_status(data.get("avatar_id"), data.get("status"), model_url)
```

### Формат webhook данных

#### Portrait Trainer
```json
{
    "request_id": "req_portrait_123",
    "status": "completed",
    "result": {
        "diffusers_lora_file": {
            "url": "https://fal.ai/files/portrait_model.safetensors",
            "file_name": "portrait_model.safetensors"
        }
    }
}
```

#### Pro Trainer
```json
{
    "request_id": "req_pro_456",
    "status": "completed",
    "result": {
        "finetune_id": "lora:abc123def456",
        "config_file": {
            "url": "https://fal.ai/files/config.json"
        }
    }
}
```

#### Ultra Generator
```json
{
    "request_id": "req_ultra_789",
    "status": "completed",
    "result": {
        "images": [
            {
                "url": "https://fal.ai/files/generated_image.jpeg",
                "width": 1024,
                "height": 1024
            }
        ]
    }
}
```

## 🧪 Тестовый режим

### Настройка тестирования
```python
class FALTrainingService:
    def __init__(self):
        self.test_mode = settings.FAL_TRAINING_TEST_MODE
        
    async def start_avatar_training(self, ...):
        if self.test_mode:
            return await self._simulate_training(avatar_id, training_type)
        
        # Реальное обучение
        if training_type == "portrait":
            return await self.portrait_trainer.train_avatar_async(...)
        else:
            return await self.pro_trainer.train_avatar(...)
```

### Симуляция webhook
```python
async def _simulate_webhook_callback(self, request_id, avatar_id, training_type):
    await asyncio.sleep(30)  # Имитация времени обучения
    
    webhook_data = {
        "request_id": request_id,
        "avatar_id": str(avatar_id),
        "training_type": training_type,
        "status": "completed",
        "result": {
            "test_mode": True,
            "mock_model_url": f"https://test.example.com/models/{request_id}.safetensors"
        }
    }
    
    # Отправка тестового webhook
    async with aiohttp.ClientSession() as session:
        await session.post(webhook_url, json=webhook_data)
```

## 🚨 Обработка ошибок

### Типичные ошибки и решения

#### Ошибки аутентификации
```python
try:
    result = await fal_client.submit(endpoint, arguments)
except AuthenticationError:
    logger.error("Неверный FAL_API_KEY")
    raise FALAuthenticationError("Проверьте FAL_API_KEY в настройках")
```

#### Ошибки лимитов
```python
try:
    result = await fal_client.submit(endpoint, arguments)
except RateLimitError:
    logger.warning("Превышен лимит запросов FAL AI")
    await asyncio.sleep(60)  # Ожидание 1 минуту
    return await self.retry_request(endpoint, arguments)
```

#### Ошибки обучения
```python
try:
    result = await fal_client.result(endpoint, request_id)
    if result.get("status") == "failed":
        error_msg = result.get("error", "Неизвестная ошибка")
        raise FALTrainingError(f"Обучение провалилось: {error_msg}")
except Exception as e:
    logger.exception(f"Ошибка получения результата: {e}")
    raise
```

## 📊 Мониторинг и метрики

### Логирование операций
```python
logger.info(f"[FAL] Запуск обучения {training_type} для аватара {avatar_id}")
logger.info(f"[FAL] Получен request_id: {request_id}")
logger.info(f"[FAL] Webhook получен: {status}, прогресс: {progress}%")
logger.info(f"[FAL] Обучение завершено: {model_url}")
```

### Метрики для отслеживания
- Время обучения по типам моделей
- Успешность обучений (%)
- Использование API квот
- Качество генерируемых изображений
- Стоимость операций

### Health check
```python
async def check_fal_api_health():
    try:
        # Простой запрос для проверки доступности
        result = await fal_client.submit("fal-ai/fast-sdxl", {"prompt": "test"})
        return {"status": "healthy", "api_available": True}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## 🔧 Лучшие практики

### Оптимизация производительности
1. **Кэширование результатов** - сохранение обученных моделей
2. **Пулинг соединений** - переиспользование HTTP соединений
3. **Асинхронная обработка** - неблокирующие операции
4. **Batch обработка** - групповые запросы где возможно

### Управление ресурсами
1. **Мониторинг квот** - отслеживание лимитов API
2. **Graceful degradation** - fallback при недоступности
3. **Retry логика** - повторные попытки с экспоненциальной задержкой
4. **Circuit breaker** - защита от каскадных сбоев

### Безопасность
1. **Валидация входных данных** - проверка параметров
2. **Санитизация промптов** - очистка пользовательского ввода
3. **Rate limiting** - ограничение частоты запросов
4. **Аудит операций** - логирование всех действий

---

**🚀 FAL AI интеграция готова для продакшн использования!** 