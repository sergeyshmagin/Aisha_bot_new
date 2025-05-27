# Руководство по сервису генерации изображений FAL AI

## 🎯 Обзор

`FALGenerationService` - это новый сервис для генерации изображений с обученными аватарами в проекте Aisha Bot. Он поддерживает все типы обученных моделей:

- **Портретные аватары** → LoRA файлы (`fal-ai/flux-lora`)
- **Стилевые аватары** → Finetune ID (`fal-ai/flux-pro`)
- **Ultra качество** → Finetune ID (`fal-ai/flux-pro/v1.1-ultra-finetuned`) 🚀 **НОВОЕ**

## 🚀 Быстрый старт

### 1. Импорт и инициализация

```python
from app.services.fal.generation_service import FALGenerationService

# Создаем экземпляр сервиса
generation_service = FALGenerationService()
```

### 2. Базовая генерация

```python
# Получаем аватар из БД
avatar = await avatar_service.get_avatar(avatar_id)

# Генерируем изображение
image_url = await generation_service.generate_avatar_image(
    avatar=avatar,
    prompt="beautiful portrait, professional lighting, 4k"
)

print(f"Сгенерированное изображение: {image_url}")
```

## 🎭 Типы аватаров

### Портретные аватары (LoRA)

**Используют**: `flux-lora-portrait-trainer` → `fal-ai/flux-lora`

```python
# Портретный аватар автоматически использует LoRA файл
if avatar.training_type == AvatarTrainingType.PORTRAIT:
    # Сервис автоматически:
    # 1. Проверяет наличие diffusers_lora_file_url
    # 2. Добавляет trigger_phrase к промпту
    # 3. Использует fal-ai/flux-lora для генерации
    
    image_url = await generation_service.generate_avatar_image(
        avatar=avatar,
        prompt="smiling portrait in a park"
    )
```

**Что происходит внутри**:
1. Проверка `avatar.diffusers_lora_file_url`
2. Добавление `avatar.trigger_phrase` к промпту
3. Вызов `fal-ai/flux-lora` с LoRA файлом

### Стилевые аватары (Finetune)

**Используют**: `flux-pro-trainer` → `fal-ai/flux-pro`

```python
# Стилевой аватар автоматически использует finetune_id
if avatar.training_type == AvatarTrainingType.STYLE:
    # Сервис автоматически:
    # 1. Проверяет наличие finetune_id
    # 2. Добавляет trigger_word к промпту
    # 3. Использует fal-ai/flux-pro для генерации
    
    image_url = await generation_service.generate_avatar_image(
        avatar=avatar,
        prompt="cyberpunk style artwork"
    )
```

**Что происходит внутри**:
1. Проверка `avatar.finetune_id`
2. Добавление `avatar.trigger_word` к промпту
3. Вызов `fal-ai/flux-pro` или `fal-ai/flux-pro/v1.1-ultra-finetuned` с обученной моделью

### Ultra качество (FLUX1.1) 🚀 **НОВОЕ**

**Используют**: `flux-pro-trainer` → `fal-ai/flux-pro/v1.1-ultra-finetuned`

```python
# Ultra качество автоматически использует новейшую модель
if quality_preset == "ultra":
    # Сервис автоматически:
    # 1. Проверяет наличие finetune_id
    # 2. Добавляет trigger_word к промпту
    # 3. Использует fal-ai/flux-pro/v1.1-ultra-finetuned
    # 4. Настраивает finetune_strength для оптимального качества
    
    image_url = await generation_service.generate_avatar_image(
        avatar=avatar,
        prompt="ultra high quality portrait",
        generation_config=presets["ultra"]
    )
```

**Преимущества Ultra модели**:
- 🚀 **10x быстрее** предыдущих версий
- 📐 **2K разрешение** (до 2048x2048)
- 🎨 **Улучшенный фотореализм**
- ⚙️ **Настраиваемая finetune_strength**

## ⚙️ Конфигурация генерации

### Пресеты качества

```python
# Получаем доступные пресеты
presets = generation_service.get_generation_config_presets()

# Быстрая генерация
fast_config = presets["fast"]
image_url = await generation_service.generate_avatar_image(
    avatar=avatar,
    prompt="quick test image",
    generation_config=fast_config
)

# Высокое качество
quality_config = presets["quality"]
image_url = await generation_service.generate_avatar_image(
    avatar=avatar,
    prompt="high quality masterpiece",
    generation_config=quality_config
)
```

### Доступные пресеты

| Пресет | Шаги | Guidance | Размер | LoRA Scale | Finetune Strength | Назначение |
|--------|------|----------|--------|------------|-------------------|------------|
| `fast` | 20 | 3.0 | square | 0.8 | 0.8 | Быстрая генерация |
| `balanced` | 28 | 3.5 | square_hd | 1.0 | 1.0 | Баланс скорости/качества |
| `quality` | 50 | 4.0 | square_hd | 1.2 | 1.2 | Максимальное качество |
| `ultra` | 35 | 3.5 | square_hd | 1.1 | 1.1 | FLUX1.1 Ultra (2K) 🚀 |
| `portrait` | 35 | 3.5 | portrait_4_3 | 1.1 | 1.0 | Портретная ориентация |
| `landscape` | 30 | 3.5 | landscape_4_3 | 1.0 | 1.0 | Альбомная ориентация |

### Кастомная конфигурация

```python
custom_config = {
    "num_inference_steps": 40,
    "guidance_scale": 4.0,
    "image_size": "square_hd",
    "lora_scale": 1.1,  # Только для LoRA
    "num_images": 1,
    "enable_safety_checker": True
}

image_url = await generation_service.generate_avatar_image(
    avatar=avatar,
    prompt="custom generation settings",
    generation_config=custom_config
)
```

## 🔄 Пакетная генерация

### Несколько промптов для одного аватара

```python
prompts = [
    "professional headshot, business attire",
    "casual portrait, outdoor setting",
    "artistic portrait, dramatic lighting",
    "smiling portrait, natural light"
]

# Генерируем все изображения
image_urls = await generation_service.generate_multiple_images(
    avatar=avatar,
    prompts=prompts,
    generation_config=presets["balanced"]
)

# Обрабатываем результаты
for i, url in enumerate(image_urls):
    if url:
        print(f"Изображение {i+1}: {url}")
    else:
        print(f"Ошибка генерации {i+1}")
```

## 🧪 Тестовый режим

### Автоматическое переключение

```python
# Сервис автоматически определяет режим из настроек
if settings.AVATAR_TEST_MODE:
    # Возвращает тестовые URL без реальных запросов к FAL AI
    test_url = await generation_service.generate_avatar_image(
        avatar=avatar,
        prompt="test generation"
    )
    # test_url = "https://picsum.photos/1024/1024?random=..."
```

### Проверка режима

```python
# Проверяем доступность сервиса
if generation_service.is_available():
    print("Сервис генерации доступен")
    
# Получаем сводку конфигурации
config = generation_service.get_config_summary()
print(f"Тестовый режим: {config['test_mode']}")
print(f"API ключ установлен: {config['api_key_set']}")
print(f"Поддерживаемые типы: {config['supported_types']}")
```

## 🔧 Интеграция в проект

### В сервисе аватаров

```python
# app/services/avatar/avatar_service.py

from ..fal.generation_service import FALGenerationService

class AvatarService:
    def __init__(self):
        self.generation_service = FALGenerationService()
    
    async def generate_avatar_image(
        self, 
        avatar_id: UUID, 
        prompt: str,
        quality: str = "balanced"
    ) -> Optional[str]:
        """Генерирует изображение для аватара"""
        
        # Получаем аватар
        avatar = await self.get_avatar(avatar_id)
        
        if not avatar:
            raise ValueError(f"Аватар {avatar_id} не найден")
        
        # Проверяем что аватар обучен
        if avatar.status != AvatarStatus.COMPLETED:
            raise ValueError(f"Аватар {avatar_id} не обучен")
        
        # Выбираем пресет качества
        presets = self.generation_service.get_generation_config_presets()
        config = presets.get(quality, presets["balanced"])
        
        # Генерируем изображение
        return await self.generation_service.generate_avatar_image(
            avatar=avatar,
            prompt=prompt,
            generation_config=config
        )
```

### В Telegram хендлерах

```python
# app/handlers/avatar/generation.py

from app.services.fal.generation_service import FALGenerationService

async def handle_generate_image(message, avatar_id: str, prompt: str):
    """Обработчик генерации изображения"""
    
    try:
        # Получаем аватар
        avatar = await avatar_service.get_avatar(UUID(avatar_id))
        
        # Создаем сервис генерации
        generation_service = FALGenerationService()
        
        # Отправляем уведомление о начале генерации
        await message.reply("🎨 Генерирую изображение...")
        
        # Генерируем изображение
        image_url = await generation_service.generate_avatar_image(
            avatar=avatar,
            prompt=prompt,
            generation_config={"quality": "balanced"}
        )
        
        if image_url:
            # Отправляем результат
            await message.reply_photo(
                photo=image_url,
                caption=f"✨ Готово! Промпт: {prompt}"
            )
        else:
            await message.reply("❌ Не удалось сгенерировать изображение")
            
    except Exception as e:
        logger.exception(f"Ошибка генерации: {e}")
        await message.reply("❌ Произошла ошибка при генерации")
```

## 🚨 Обработка ошибок

### Типичные ошибки

```python
try:
    image_url = await generation_service.generate_avatar_image(
        avatar=avatar,
        prompt=prompt
    )
    
except ValueError as e:
    # Аватар не обучен или отсутствуют данные модели
    if "не обучен" in str(e):
        print("Аватар еще не завершил обучение")
    elif "LoRA файл не найден" in str(e):
        print("Отсутствует LoRA файл для портретного аватара")
    elif "Finetune ID не найден" in str(e):
        print("Отсутствует Finetune ID для стилевого аватара")
    
except RuntimeError as e:
    # Ошибки FAL AI API
    print(f"Ошибка генерации: {e}")
    
except Exception as e:
    # Неожиданные ошибки
    print(f"Неизвестная ошибка: {e}")
```

### Безопасная генерация

```python
async def safe_generate_image(avatar_id: UUID, prompt: str) -> Optional[str]:
    """Безопасная генерация с обработкой всех ошибок"""
    
    try:
        generation_service = FALGenerationService()
        
        # Проверяем доступность сервиса
        if not generation_service.is_available():
            logger.warning("Сервис генерации недоступен")
            return None
        
        # Получаем аватар
        avatar = await avatar_service.get_avatar(avatar_id)
        if not avatar:
            logger.error(f"Аватар {avatar_id} не найден")
            return None
        
        # Генерируем изображение
        return await generation_service.generate_avatar_image(
            avatar=avatar,
            prompt=prompt
        )
        
    except Exception as e:
        logger.exception(f"Ошибка безопасной генерации: {e}")
        return None
```

## 📊 Мониторинг и метрики

### Логирование

```python
# Сервис автоматически логирует:
# [FAL AI] Генерация с LoRA для аватара {id}: {args}
# [FAL AI] LoRA генерация завершена: {url}
# [FAL AI] Генерация с finetune для аватара {id}: {args}
# [FAL AI] Finetune генерация завершена: {url}

# В тестовом режиме:
# 🧪 [FAL TEST MODE] Симуляция генерации завершена: {url}
```

### Сбор статистики

```python
async def generate_with_metrics(avatar_id: UUID, prompt: str):
    """Генерация с метриками"""
    
    start_time = time.time()
    
    try:
        image_url = await generation_service.generate_avatar_image(
            avatar=avatar,
            prompt=prompt
        )
        
        # Успешная генерация
        duration = time.time() - start_time
        logger.info(f"Генерация завершена за {duration:.2f}с")
        
        return image_url
        
    except Exception as e:
        # Ошибка генерации
        duration = time.time() - start_time
        logger.error(f"Ошибка генерации за {duration:.2f}с: {e}")
        raise
```

## 🔗 Связанные документы

- [Flux LoRA Portrait Trainer API](./flux-lora-portrait-trainer-api.md)
- [Flux Pro Trainer](./flux-pro-trainer.md)
- [Сравнение моделей FAL AI](./fal-ai-models-comparison.md)
- [Архитектура аватаров](../AVATAR_ARCHITECTURE_CONSOLIDATED.md)

## 🎯 Рекомендации

### Для продакшена

1. **Используйте пресеты** - они оптимизированы для разных сценариев
2. **Обрабатывайте ошибки** - FAL AI может быть недоступен
3. **Логируйте метрики** - отслеживайте время генерации и успешность
4. **Кешируйте результаты** - сохраняйте сгенерированные изображения

### Для разработки

1. **Тестовый режим** - используйте `AVATAR_TEST_MODE=true`
2. **Проверяйте доступность** - `generation_service.is_available()`
3. **Начинайте с balanced** - оптимальный баланс скорости/качества
4. **Тестируйте оба типа** - портретные и стилевые аватары

## ✅ Заключение

`FALGenerationService` предоставляет единый интерфейс для генерации изображений с любыми типами обученных аватаров. Сервис автоматически:

- ✅ Определяет тип аватара (портретный/стилевой)
- ✅ Выбирает правильную модель FAL AI
- ✅ Добавляет триггерные фразы/слова
- ✅ Обрабатывает ошибки и логирует процесс
- ✅ Поддерживает тестовый режим

**Используйте этот сервис для всех задач генерации изображений в проекте!** 