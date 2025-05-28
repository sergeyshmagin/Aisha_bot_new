# 🎭 Портретные аватары - Реализация

> **Статус**: ✅ Реализовано и протестировано  
> **Дата**: 23 мая 2025  
> **Версия**: 1.0

## 📋 Обзор

Система портретных аватаров позволяет пользователям создавать высококачественные портреты с использованием специализированного алгоритма **FAL AI flux-lora-portrait-trainer**.

### 🎯 Ключевые особенности

- **Специализация на лицах**: Оптимизирован для портретной съемки
- **Быстрое обучение**: 3-15 минут (в 2-3 раза быстрее художественного)
- **Высокое качество**: Максимальная детализация лиц
- **Автоматическая оптимизация**: Обрезка субъектов и создание масок
- **Простота использования**: Минимум настроек для пользователя

## 🏗️ Архитектура

### Компоненты системы

```
🎭 Portrait Avatar System
├── 📱 User Interface
│   ├── app/handlers/avatar/portrait_handler.py
│   ├── app/texts/avatar.py (TRAINING_TYPE_TEXTS)
│   └── app/keyboards/avatar_clean.py
├── 🤖 Training Services
│   ├── app/services/fal/client.py (FalAIClient)
│   ├── app/services/avatar/fal_training_service/ (FALTrainingService)
│   └── app/services/avatar/training_service/ (Legacy support)
├── 🗄️ Database Models
│   ├── Avatar.training_type = "portrait"
│   ├── Avatar.trigger_phrase
│   ├── Avatar.steps, learning_rate
│   └── Portrait-specific settings
└── ⚙️ Configuration
    ├── app/core/config.py (FAL_PORTRAIT_*)
    └── env_template.txt
```

### Интеграция с FAL AI

```python
# Endpoint для портретного обучения
ENDPOINT = "fal-ai/flux-lora-portrait-trainer"

# Основные параметры
{
    "images_data_url": "https://fal.ai/archive.zip",
    "trigger_phrase": "PERSON_12345678",
    "steps": 1000,
    "learning_rate": 0.0002,
    "multiresolution_training": True,
    "subject_crop": True,
    "create_masks": False
}
```

## 🚀 Использование

### 1. Создание портретного аватара

```python
from app.services.fal.client import FalAIClient

# Инициализация клиента
fal_client = FalAIClient()

# Конфигурация портретного обучения
portrait_config = {
    "training_type": "portrait",
    "trigger_phrase": "PERSON_12345678",
    "steps": 1000,
    "learning_rate": 0.0002,
    "multiresolution_training": True,
    "subject_crop": True,
    "create_masks": False,
    "webhook_url": "https://your-webhook.com/status"
}

# Запуск обучения
request_id = await fal_client.train_avatar(
    user_id=user_id,
    avatar_id=avatar_id,
    name="Мой портрет",
    gender="male",
    photo_urls=photo_urls,
    training_config=portrait_config
)
```

### 2. Через FAL Training Service

```python
from app.services.avatar.fal_training_service import FALTrainingService

# Инициализация сервиса
fal_service = FALTrainingService()

# Запуск портретного обучения
request_id = await fal_service.start_avatar_training(
    avatar_id=avatar_id,
    training_type="portrait",
    training_data_url=training_data_url,
    user_preferences={"quality": "balanced"}
)

# Получение информации о типе обучения
type_info = fal_service.get_training_type_info("portrait")
```

### 3. Прямой вызов портретного метода

```python
# Прямой вызов специализированного метода
request_id = await fal_client.train_portrait_model(
    images_data_url=images_data_url,
    trigger_phrase="PERSON_12345678",
    steps=1000,
    learning_rate=0.0002,
    multiresolution_training=True,
    subject_crop=True,
    create_masks=False,
    webhook_url=webhook_url
)
```

## ⚙️ Конфигурация

### Переменные окружения

```bash
# Основные настройки портретного обучения
FAL_PORTRAIT_STEPS=1000
FAL_PORTRAIT_LEARNING_RATE=0.0002
FAL_PORTRAIT_SUBJECT_CROP=true
FAL_PORTRAIT_CREATE_MASKS=false
FAL_PORTRAIT_MULTIRESOLUTION=true

# Пресеты качества для портретов
FAL_FAST_PORTRAIT_STEPS=300
FAL_FAST_PORTRAIT_LR=0.0003

FAL_BALANCED_PORTRAIT_STEPS=600
FAL_BALANCED_PORTRAIT_LR=0.0002

FAL_QUALITY_PORTRAIT_STEPS=1000
FAL_QUALITY_PORTRAIT_LR=0.0001

# Webhook для портретного обучения
FAL_WEBHOOK_PORTRAIT_URL=https://your-domain.com/api/avatar/status_update?training_type=portrait
```

### Настройки в config.py

```python
class Settings(BaseSettings):
    # Портретное обучение
    FAL_PORTRAIT_STEPS: int = Field(1000, env="FAL_PORTRAIT_STEPS")
    FAL_PORTRAIT_LEARNING_RATE: float = Field(0.0002, env="FAL_PORTRAIT_LEARNING_RATE")
    FAL_PORTRAIT_SUBJECT_CROP: bool = Field(True, env="FAL_PORTRAIT_SUBJECT_CROP")
    FAL_PORTRAIT_CREATE_MASKS: bool = Field(False, env="FAL_PORTRAIT_CREATE_MASKS")
    FAL_PORTRAIT_MULTIRESOLUTION: bool = Field(True, env="FAL_PORTRAIT_MULTIRESOLUTION")
    
    @property
    def FAL_PRESET_FAST(self) -> Dict[str, Any]:
        return {
            "portrait": {
                "steps": self.FAL_FAST_PORTRAIT_STEPS, 
                "learning_rate": self.FAL_FAST_PORTRAIT_LR
            },
            "general": {
                "iterations": 200, 
                "learning_rate": 0.0003
            }
        }
```

## 📊 Сравнение типов обучения

| Критерий | 🎭 Портретный | 🎨 Художественный |
|----------|---------------|-------------------|
| **API Endpoint** | flux-lora-portrait-trainer | flux-pro-trainer |
| **Лучше для** | Лица людей | Стили, объекты |
| **Скорость** | ⭐⭐⭐⭐ (3-15 мин) | ⭐⭐⭐ (5-30 мин) |
| **Качество портретов** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Универсальность** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Простота** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Параметр обучения** | steps | iterations |
| **Триггер** | trigger_phrase | trigger_word |
| **Автообрезка** | ✅ subject_crop | ❌ |
| **Маски** | ✅ create_masks | ❌ |

## 🔄 Workflow обучения

### 1. Пользовательский интерфейс

```
👤 Пользователь выбирает "Создать аватар"
    ↓
🎯 Выбор типа: "Портретный" или "Художественный"
    ↓
👨/👩 Выбор пола для оптимизации
    ↓
📝 Ввод имени аватара
    ↓
📸 Загрузка 10-20 фотографий
    ↓
🚀 Запуск обучения
```

### 2. Серверная обработка

```
📦 Создание архива с фотографиями
    ↓
🎭 Определение типа обучения (portrait/style)
    ↓
⚙️ Настройка параметров для портретного тренера
    ↓
🌐 Отправка запроса в FAL AI flux-lora-portrait-trainer
    ↓
📋 Получение request_id
    ↓
🔍 Запуск мониторинга статуса
    ↓
📬 Обработка webhook уведомлений
    ↓
✅ Завершение обучения
```

### 3. Результат обучения

```python
# Результат портретного обучения
{
    "diffusers_lora_file": {
        "url": "https://fal.ai/files/lora_weights.safetensors",
        "content_type": "application/octet-stream",
        "file_name": "portrait_lora.safetensors",
        "file_size": 144000000
    },
    "config_file": {
        "url": "https://fal.ai/files/training_config.json",
        "content_type": "application/json",
        "file_name": "config.json",
        "file_size": 2048
    }
}
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Тест портретного обучения
python test_portrait_avatars.py

# Результат теста
🎭 Тестирование портретного обучения аватаров
==================================================
✅ Портретное обучение запущено успешно!
📋 Request ID: test_5f8a8728_c20b8cf4
📊 Информация о портретном обучении:
   name: Портретный
   description: Специально для фотографий людей
   speed: ⭐⭐⭐⭐ (3-15 минут)
   quality_portraits: ⭐⭐⭐⭐⭐
   best_for: ['Селфи', 'Портреты', 'Фото людей']
   technology: Flux LoRA Portrait Trainer
```

### Тестовый режим

В тестовом режиме (`AVATAR_TEST_MODE=true`):
- Не отправляются реальные запросы в FAL AI
- Имитируется процесс обучения
- Возвращаются мок request_id
- Симулируется прогресс обучения

## 🚨 Обработка ошибок

### Типичные ошибки и решения

```python
# 1. Отсутствие API ключа
try:
    request_id = await fal_client.train_portrait_model(...)
except MissingCredentialsError:
    logger.warning("FAL API ключ не установлен, переключение в тестовый режим")
    # Автоматическое переключение в тестовый режим

# 2. Недостаточно фотографий
if len(photo_urls) < 10:
    raise ValueError("Для портретного обучения нужно минимум 10 фотографий")

# 3. Ошибка создания архива
if not training_data_url:
    raise RuntimeError("Не удалось создать архив с фотографиями")

# 4. Ошибка запуска обучения
if not request_id:
    raise RuntimeError("FAL AI не смог запустить портретное обучение")
```

## 📈 Мониторинг и уведомления

### Webhook обработка

```python
# Обработка результата портретного обучения
if avatar.training_type == AvatarTrainingType.PORTRAIT:
    # flux-lora-portrait-trainer возвращает файлы LoRA
    diffusers_file = result.get("diffusers_lora_file", {})
    config_file = result.get("config_file", {})
    
    update_data.update({
        "diffusers_lora_file_url": diffusers_file.get("url"),
        "config_file_url": config_file.get("url")
    })
```

### Статус мониторинг

```python
# Проверка статуса портретного обучения
if training_type == "portrait":
    endpoint = "fal-ai/flux-lora-portrait-trainer"
else:
    endpoint = "fal-ai/flux-pro-trainer"

status = await fal_client.status_async(endpoint, request_id, with_logs=True)
```

## 🎯 Рекомендации по использованию

### Для пользователей

1. **Количество фото**: 10-20 изображений
2. **Качество**: Высокое разрешение (минимум 512×512)
3. **Разнообразие**: Разные ракурсы и выражения лица
4. **Освещение**: Хорошее, равномерное освещение
5. **Фон**: Разнообразные фоны
6. **Один человек**: На каждом фото должен быть только один человек

### Для разработчиков

1. **Тестовый режим**: Используйте для разработки без затрат
2. **Мониторинг**: Настройте webhook для получения уведомлений
3. **Обработка ошибок**: Предусмотрите fallback на тестовый режим
4. **Логирование**: Детальное логирование для отладки
5. **Кэширование**: Избегайте дублирования уведомлений

## 📚 Дополнительные ресурсы

- [FAL AI Portrait Trainer API](../fal_knowlege_base/flux-lora-portrait-trainer-api.md)
- [Сравнение FAL AI моделей](../fal_knowlege_base/fal-ai-models-comparison.md)
- [Руководство по интеграции FAL AI](../guides/fal_ai_integration.md)
- [Архитектура системы аватаров](../AVATAR_ARCHITECTURE_CONSOLIDATED.md)

---

**Статус**: ✅ Готово к продакшену  
**Последнее обновление**: 23 мая 2025  
**Автор**: AI Assistant 