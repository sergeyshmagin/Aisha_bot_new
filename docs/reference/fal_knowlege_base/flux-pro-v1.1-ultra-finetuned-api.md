# FLUX1.1 [pro] ultra Fine-tuned API

## 🎯 Обзор

**FLUX1.1 [pro] ultra Fine-tuned** - это новейшая версия FLUX1.1 [pro] с fine-tuned LoRA, которая поддерживает профессиональное качество изображений с разрешением до 2K и улучшенным фотореализмом.

**Модель**: `fal-ai/flux-pro/v1.1-ultra-finetuned`

## ⚡ Ключевые особенности

- **Высокое разрешение**: До 2K (2048x2048)
- **Улучшенный фотореализм**: Более реалистичные изображения
- **10x ускорение**: По сравнению с предыдущими версиями
- **Fine-tuned LoRA**: Поддержка обученных моделей
- **Коммерческое использование**: Разрешено

## 🚀 Быстрый старт

### Установка клиента

```bash
npm install --save @fal-ai/client
```

### Базовая генерация

```javascript
import { fal } from "@fal-ai/client";

const result = await fal.subscribe("fal-ai/flux-pro/v1.1-ultra-finetuned", {
  input: {
    prompt: "beautiful portrait, professional lighting, 4k",
    finetune_id: "your_finetune_id",
    finetune_strength: 1.0
  },
  logs: true,
  onQueueUpdate: (update) => {
    if (update.status === "IN_PROGRESS") {
      update.logs.map((log) => log.message).forEach(console.log);
    }
  },
});

console.log(result.data.images[0].url);
```

## 📋 Параметры API

### Обязательные параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `prompt` | `string` | Промпт для генерации изображения |
| `finetune_id` | `string` | ID вашей обученной модели |
| `finetune_strength` | `float` | Сила влияния finetune (0.0-2.0) |

### Дополнительные параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `seed` | `integer` | `null` | Сид для воспроизводимости |
| `num_images` | `integer` | `1` | Количество изображений |
| `aspect_ratio` | `string` | `"16:9"` | Соотношение сторон |
| `output_format` | `string` | `"jpeg"` | Формат вывода (jpeg/png) |
| `enable_safety_checker` | `boolean` | `true` | Проверка безопасности |
| `safety_tolerance` | `integer` | `2` | Уровень толерантности (1-6) |
| `sync_mode` | `boolean` | `false` | Синхронный режим |
| `raw` | `boolean` | `false` | Менее обработанные изображения |

### Доступные соотношения сторон

- `21:9` - Ультраширокий
- `16:9` - Широкий (по умолчанию)
- `4:3` - Стандартный
- `3:2` - Фото
- `1:1` - Квадрат
- `2:3` - Портрет
- `3:4` - Портрет стандартный
- `9:16` - Вертикальный
- `9:21` - Ультравертикальный

## 🎨 Оптимизация finetune_strength

### Рекомендуемые значения

| Тип контента | finetune_strength | Описание |
|--------------|-------------------|----------|
| **Портреты** | `0.8 - 1.2` | Сбалансированное влияние |
| **Стили** | `1.0 - 1.5` | Сильное стилевое влияние |
| **Объекты** | `0.6 - 1.0` | Умеренное влияние |
| **Концепты** | `1.2 - 2.0` | Максимальное влияние |

### Примеры настройки

```javascript
// Слабое влияние - больше креативности
{
  finetune_strength: 0.6,
  prompt: "creative interpretation of TOK_person in fantasy style"
}

// Сильное влияние - точное соответствие
{
  finetune_strength: 1.5,
  prompt: "exact TOK_person portrait, professional headshot"
}
```

## 🔄 Асинхронная генерация

### Отправка запроса

```javascript
const { request_id } = await fal.queue.submit("fal-ai/flux-pro/v1.1-ultra-finetuned", {
  input: {
    prompt: "professional portrait of TOK_person",
    finetune_id: "your_finetune_id",
    finetune_strength: 1.0
  },
  webhookUrl: "https://your-webhook.url/results",
});
```

### Проверка статуса

```javascript
const status = await fal.queue.status("fal-ai/flux-pro/v1.1-ultra-finetuned", {
  requestId: request_id,
  logs: true,
});
```

### Получение результата

```javascript
const result = await fal.queue.result("fal-ai/flux-pro/v1.1-ultra-finetuned", {
  requestId: request_id
});

console.log(result.data.images[0].url);
```

## 📊 Структура ответа

```json
{
  "images": [
    {
      "url": "https://fal.media/files/generated_image.jpg",
      "content_type": "image/jpeg",
      "width": 1024,
      "height": 1024
    }
  ],
  "timings": {
    "inference": 2.5
  },
  "seed": 12345,
  "has_nsfw_concepts": [false],
  "prompt": "beautiful portrait of TOK_person"
}
```

## 🐍 Python интеграция

### Установка

```bash
pip install fal-client
```

### Пример использования

```python
import fal_client

# Настройка API ключа
fal_client.api_key = "your_fal_api_key"

# Генерация изображения
result = fal_client.subscribe(
    "fal-ai/flux-pro/v1.1-ultra-finetuned",
    arguments={
        "prompt": "professional portrait of TOK_person",
        "finetune_id": "your_finetune_id",
        "finetune_strength": 1.0,
        "aspect_ratio": "1:1",
        "num_images": 1
    }
)

image_url = result["images"][0]["url"]
print(f"Generated image: {image_url}")
```

## 🔧 Интеграция в Aisha Bot

### Обновление FALGenerationService

```python
async def _generate_with_finetune_ultra(
    self,
    avatar: Avatar,
    prompt: str,
    config: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Генерация с FLUX1.1 [pro] ultra Fine-tuned
    """
    if not avatar.finetune_id:
        raise ValueError(f"Finetune ID не найден для аватара {avatar.id}")
    
    # Формируем промпт с триггерным словом
    full_prompt = self._build_prompt_with_trigger(prompt, avatar.trigger_word)
    
    # Настройки для ultra модели
    generation_args = {
        "prompt": full_prompt,
        "finetune_id": avatar.finetune_id,
        "finetune_strength": config.get("finetune_strength", 1.0) if config else 1.0,
        "aspect_ratio": config.get("aspect_ratio", "1:1") if config else "1:1",
        "num_images": config.get("num_images", 1) if config else 1,
        "output_format": config.get("output_format", "jpeg") if config else "jpeg",
        "enable_safety_checker": config.get("enable_safety_checker", True) if config else True,
        "raw": config.get("raw", False) if config else False,
    }
    
    logger.info(f"[FAL AI] Ultra генерация для аватара {avatar.id}: {generation_args}")
    
    # Запускаем генерацию
    result = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: fal_client.subscribe(
            "fal-ai/flux-pro/v1.1-ultra-finetuned",
            arguments=generation_args
        )
    )
    
    # Извлекаем URL изображения
    images = result.get("images", [])
    if images and len(images) > 0:
        image_url = images[0].get("url")
        logger.info(f"[FAL AI] Ultra генерация завершена: {image_url}")
        return image_url
    
    return None
```

## 💰 Стоимость и лимиты

### Ценообразование
- **Базовая генерация**: ~$0.05 за изображение
- **Высокое разрешение**: +50% к базовой стоимости
- **Пакетная генерация**: Скидки при больших объемах

### Лимиты
- **Максимальное разрешение**: 2048x2048
- **Максимум изображений за запрос**: 4
- **Максимальная длина промпта**: 1000 символов
- **Rate limit**: 100 запросов в минуту

## 🚨 Обработка ошибок

### Типичные ошибки

```python
try:
    result = await generate_ultra_image(avatar, prompt)
except Exception as e:
    if "invalid finetune_id" in str(e):
        logger.error("Неверный finetune_id")
    elif "rate limit" in str(e):
        logger.error("Превышен лимит запросов")
    elif "nsfw content" in str(e):
        logger.error("Контент заблокирован фильтром")
    else:
        logger.error(f"Неизвестная ошибка: {e}")
```

## 🎯 Рекомендации

### Для лучшего качества
1. **Используйте описательные промпты**: "professional portrait, studio lighting, 4k"
2. **Настраивайте finetune_strength**: Начните с 1.0, корректируйте по результату
3. **Выбирайте правильное соотношение**: 1:1 для портретов, 16:9 для сцен
4. **Используйте raw=false**: Для более обработанных изображений

### Для оптимизации производительности
1. **Асинхронные запросы**: Для множественной генерации
2. **Кеширование**: Сохраняйте популярные результаты
3. **Пакетная обработка**: Группируйте запросы
4. **Мониторинг**: Отслеживайте время генерации

## 🔗 Связанные документы

- [Generation Service Guide](./generation-service-guide.md)
- [Flux Pro Trainer](./flux-pro-trainer.md)
- [Models Comparison](./fal-ai-models-comparison.md)

## 📅 Обновления

- **2025-05-23**: Добавлена поддержка FLUX1.1 [pro] ultra Fine-tuned
- **2025-05-23**: Обновлены параметры API и примеры интеграции 