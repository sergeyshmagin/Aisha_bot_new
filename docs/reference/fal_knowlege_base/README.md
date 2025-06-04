# FAL AI Knowledge Base

Полная база знаний по интеграции с FAL AI для обучения и генерации аватаров в проекте Aisha Bot.

## 📚 Содержание

### 1. [Flux LoRA Portrait Trainer API](./flux-lora-portrait-trainer-api.md)
**Специализированная модель для портретов**

- 🎯 **Назначение**: Обучение LoRA моделей для генерации портретов людей
- ✨ **Особенности**: Автообрезка, создание масок, мультиразрешение
- 🚀 **Скорость**: Быстрое обучение (3-15 минут)
- 💎 **Качество**: Превосходное для портретов

**Что внутри**:
- Полное API reference
- Примеры интеграции
- Оптимальные настройки
- Класс `FALPortraitTrainer` для интеграции

### 2. [Flux Pro Trainer](./flux-pro-trainer.md)
**Универсальная модель для всех типов контента**

- 🎯 **Назначение**: Универсальное обучение (character, style, product, general)
- ✨ **Особенности**: Full + LoRA обучение, автоподписи, гибкие настройки
- 🚀 **Скорость**: Средняя (5-30 минут)
- 💎 **Качество**: Максимальное для любого контента

**Что внутри**:
- API схема и параметры
- Примеры использования
- Настройки для разных типов
- Обработка очереди и webhook

### 3. [Сравнение моделей FAL AI](./fal-ai-models-comparison.md)
**Руководство по выбору оптимальной модели**

- 📊 **Детальное сравнение** всех доступных моделей
- 🎯 **Рекомендации по выбору** для разных задач
- 🛠️ **Класс-адаптер** `FALTrainerAdapter` для автовыбора
- 📈 **Оптимизация параметров** для разных сценариев

**Что внутри**:
- Сравнительная таблица моделей
- Примеры оптимальных настроек
- Стратегии по стоимости и качеству
- Готовый код для интеграции

### 4. [Сервис генерации изображений](./generation-service-guide.md) ⭐ **НОВОЕ**
**Полное руководство по FALGenerationService**

- 🎯 **Назначение**: Единый интерфейс для генерации с LoRA и Finetune моделями
- ✨ **Особенности**: Автоматический выбор модели, пресеты качества, пакетная генерация
- 🚀 **Скорость**: Оптимизированные настройки для разных сценариев
- 💎 **Качество**: 5 пресетов от быстрой до максимального качества

**Что внутри**:
- Быстрый старт и примеры
- Конфигурация и пресеты
- Интеграция в проект
- Обработка ошибок и мониторинг

### 5. [FLUX1.1 [pro] ultra Fine-tuned API](./flux-pro-v1.1-ultra-finetuned-api.md) 🚀 **НОВЕЙШЕЕ**
**Продвинутая модель с 2K разрешением и 10x ускорением**

- 🎯 **Назначение**: Высококачественная генерация с обученными моделями
- ✨ **Особенности**: 2K разрешение, улучшенный фотореализм, finetune_strength
- 🚀 **Скорость**: 10x быстрее предыдущих версий
- 💎 **Качество**: Профессиональное качество изображений

**Что внутри**:
- Полное API reference
- Оптимизация finetune_strength
- Python интеграция
- Обработка ошибок и лимиты

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install fal-client
```

### 2. Настройка API ключа
```bash
export FAL_KEY="your_fal_api_key"
```

### 3. Выбор модели
```python
# Для портретов людей
from app.services.avatar.fal_portrait_trainer import FALPortraitTrainer

# Для стилей и объектов
from app.services.avatar.fal_trainer_adapter import FALTrainerAdapter, FALModelType
```

## 🎯 Рекомендации по использованию

### Для портретов → [Portrait Trainer](./flux-lora-portrait-trainer-api.md)
```python
trainer = FALPortraitTrainer()
result = await trainer.train_avatar(
    images_data_url="training_data.zip",
    trigger_phrase="TOK_person",
    steps=1000,
    subject_crop=True
)
```

### Для стилей → [Pro Trainer](./flux-pro-trainer.md)
```python
adapter = FALTrainerAdapter()
result = await adapter.train_avatar(
    model_type=FALModelType.STYLE,
    images_data_url="training_data.zip",
    iterations=500
)
```

### Автовыбор модели → [Models Comparison](./fal-ai-models-comparison.md)
```python
adapter = FALTrainerAdapter()

# Автоматически выберет оптимальную модель и настройки
if avatar_type == "character":
    model_type = FALModelType.PORTRAIT
else:
    model_type = FALModelType.STYLE

result = await adapter.train_avatar(model_type, data_url)
```

## 📊 Сравнение моделей

| Критерий | Portrait Trainer | Pro Trainer |
|----------|------------------|-------------|
| **Лучше для** | Портреты людей | Стили, объекты |
| **Скорость** | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Качество портретов** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Универсальность** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Простота** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 🛠️ Интеграция в проект

### Структура файлов
```
app/services/avatar/
├── fal_portrait_trainer.py    # Класс для Portrait Trainer
├── fal_trainer_adapter.py     # Адаптер для выбора модели
└── training_service.py        # Основной сервис обучения
```

### Основные классы

1. **`FALPortraitTrainer`** - Специализация на портретах
2. **`FALTrainerAdapter`** - Автовыбор оптимальной модели
3. **`AvatarTrainingService`** - Интеграция в систему аватаров

## 📈 Оптимизация производительности

### Быстрое обучение (прототипы)
- Portrait: `steps=500`, `learning_rate=0.0003`
- General: `iterations=200`, `priority="speed"`

### Продакшн качество
- Portrait: `steps=1500`, `create_masks=True`
- General: `iterations=600`, `lora_rank=32`

### Максимальное качество
- Portrait: `steps=2500`, `multiresolution_training=True`
- General: `iterations=1000`, `priority="quality"`

## 🚨 Частые ошибки и решения

### "Token is invalid"
```python
import os
os.environ['FAL_KEY'] = 'your_valid_api_key'
```

### "Insufficient data"
- Минимум 10 изображений для обучения
- Проверьте ZIP архив

### "Rate limit exceeded"
- Используйте асинхронные методы
- Добавьте задержки между запросами

### "Invalid format"
- Используйте ZIP архивы
- Проверьте форматы изображений (JPG, PNG, WEBP)

## 📝 Примеры кода

### Базовое обучение портрета
```python
from app.services.avatar.fal_portrait_trainer import FALPortraitTrainer

trainer = FALPortraitTrainer()
result = await trainer.train_avatar(
    images_data_url=training_url,
    trigger_phrase=f"TOK_{user_id}",
    steps=1000
)
finetune_id = result["diffusers_lora_file"]["url"]
```

### Мониторинг прогресса
```python
# Асинхронный запуск
request_id = await trainer.train_avatar_async(training_url)

# Проверка статуса
while True:
    status = await trainer.check_training_status(request_id)
    if status["status"] == "completed":
        result = await trainer.get_training_result(request_id)
        break
    await asyncio.sleep(30)
```

### Обработка ошибок
```python
try:
    result = await trainer.train_avatar(...)
except ValueError as e:
    logger.error(f"Ошибка валидации: {e}")
except Exception as e:
    logger.error(f"Ошибка обучения: {e}")
```

## 🔗 Полезные ссылки

- [FAL AI Official](https://fal.ai/)
- [Python Client GitHub](https://github.com/fal-ai/fal)
- [Community Discord](https://discord.gg/fal-ai)
- [Pricing](https://fal.ai/pricing)
- [Status Page](https://status.fal.ai/)

## 📅 Последние обновления

- **2025-05-23**: Добавлена документация по Portrait Trainer
- **2025-05-23**: Создан адаптер для автовыбора моделей
- **2025-05-23**: Добавлены примеры интеграции в проект

## 🤝 Поддержка

При возникновении вопросов:

1. Проверьте [FAQ](https://fal.ai/docs/faq)
2. Посмотрите примеры в этой knowledge base
3. Обратитесь в [Discord сообщество](https://discord.gg/fal-ai)
4. Создайте issue в [GitHub репозитории](https://github.com/fal-ai/fal) 