# Imagen 4 API Documentation

## Обзор

Google Imagen 4 - это модель для генерации высококачественных изображений с улучшенной детализацией, богатым освещением и минимальными артефактами.

### Возможности модели:
- Захват мелких деталей и текстур
- Рендеринг различных художественных стилей от фотореализма до анимации
- Понимание естественного языка в промптах
- Поддержание высокого визуального качества и композиции

## 1. API Эндпоинт

**URL:** `fal-ai/imagen4/preview`

## 2. Установка клиента

```bash
pip install fal-client
```

## 3. Настройка API ключа

```bash
export FAL_KEY="YOUR_API_KEY"
```

## 4. Примеры использования

### Простой асинхронный запрос

```python
import asyncio
import fal_client

async def generate_image():
    handler = await fal_client.submit_async(
        "fal-ai/imagen4/preview",
        arguments={
            "prompt": "Beautiful sunset over mountains, photorealistic",
            "aspect_ratio": "16:9",
            "num_images": 1
        },
    )
    
    result = await handler.get()
    return result
```

### Запрос с вебхуком

```python
async def submit_with_webhook():
    handler = await fal_client.submit_async(
        "fal-ai/imagen4/preview",
        arguments={
            "prompt": "Beautiful sunset over mountains, photorealistic"
        },
        webhook_url="https://your-webhook.url/results",
    )
    
    request_id = handler.request_id
    return request_id
```

### Проверка статуса

```python
status = await fal_client.status_async("fal-ai/imagen4/preview", request_id, with_logs=True)
```

### Получение результата

```python
result = await fal_client.result_async("fal-ai/imagen4/preview", request_id)
```

## 5. Схема входных данных

### Параметры запроса

| Параметр | Тип | Описание | По умолчанию |
|----------|-----|----------|--------------|
| `prompt` | string | Текстовое описание желаемого изображения | **обязательный** |
| `negative_prompt` | string | Описание того, что не должно быть на изображении | `""` |
| `aspect_ratio` | enum | Соотношение сторон изображения | `"1:1"` |
| `num_images` | integer | Количество изображений для генерации (1-4) | `1` |
| `seed` | integer | Зерно для воспроизводимой генерации | случайное |

### Возможные соотношения сторон
- `1:1` - квадратное
- `16:9` - широкое (горизонтальное)
- `9:16` - портретное (вертикальное)
- `3:4` - портретное
- `4:3` - альбомное

## 6. Схема выходных данных

### Структура ответа

```json
{
  "images": [
    {
      "url": "https://v3.fal.media/files/rabbit/rmgBxhwGYb2d3pl3x9sKf_output.png",
      "content_type": "image/png",
      "file_name": "generated_image.png",
      "file_size": 1024000
    }
  ],
  "seed": 42
}
```

### Поля результата

| Поле | Тип | Описание |
|------|-----|----------|
| `images` | array | Массив сгенерированных изображений |
| `seed` | integer | Использованное зерно для генерации |

### Структура объекта File

| Поле | Тип | Описание |
|------|-----|----------|
| `url` | string | URL для скачивания файла |
| `content_type` | string | MIME-тип файла |
| `file_name` | string | Имя файла |
| `file_size` | integer | Размер файла в байтах |
| `file_data` | string | Данные файла (опционально) |

## 7. Особенности интеграции

### Обработка файлов
- API принимает файлы в виде URL или Base64 data URI
- Можно загружать файлы через `fal_client.upload_file_async()`
- Поддерживаются публично доступные URL

### Производительность
- Для длительных запросов рекомендуется использовать вебхуки
- Можно проверять статус запроса через API
- Поддерживается асинхронная обработка

## 8. Ограничения и рекомендации

- Максимум 4 изображения за один запрос
- Рекомендуется использовать вебхуки для длительных операций
- API ключ не должен быть доступен на клиентской стороне
- Для продакшена используйте серверную прокси-интеграцию

## 9. Примеры промптов

### Фотореалистичные изображения
```
"Professional portrait of a business woman in modern office, natural lighting, high detail"
```

### Художественные стили
```
"Watercolor painting of a peaceful lake with mountains in background, soft pastel colors"
```

### Детализированные сцены
```
"Cozy coffee shop interior with vintage furniture, warm lighting, books on shelves, steaming coffee cups"
```

## 10. Интеграция в проект

### Необходимые зависимости
- `fal-client` для работы с API
- Асинхронная обработка запросов
- MinIO для хранения сгенерированных изображений
- PostgreSQL для метаданных
- Redis для кеширования статусов

### Рекомендуемая архитектура
1. Оптимизация промпта через существующий prompt optimizer
2. Отправка запроса в Imagen 4 API
3. Сохранение результата в MinIO
4. Обновление галереи пользователя
5. Уведомление пользователя о готовности 