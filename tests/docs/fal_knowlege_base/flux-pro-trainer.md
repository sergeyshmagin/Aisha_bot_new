# fal-ai/flux-pro-trainer API

## 1. Аутентификация

Для работы с API требуется API-ключ. Рекомендуется установить переменную окружения:

```bash
export FAL_KEY="YOUR_API_KEY"
```

## 2. Отправка запроса

Асинхронный пример на Python:

```python
import asyncio
import fal_client

async def subscribe():
    handler = await fal_client.submit_async(
        "fal-ai/flux-pro-trainer",
        arguments={
            "data_url": "",
            "finetune_comment": "test-1"
        },
    )

    async for event in handler.iter_events(with_logs=True):
        print(event)

    result = await handler.get()
    print(result)

if __name__ == "__main__":
    asyncio.run(subscribe())
```

## 3. Очередь и Webhook

Для долгих задач рекомендуется использовать webhook для получения результата:

```python
import asyncio
import fal_client

async def submit():
    handler = await fal_client.submit_async(
        "fal-ai/flux-pro-trainer",
        arguments={
            "data_url": "",
            "finetune_comment": "test-1"
        },
        webhook_url="https://optional.webhook.url/for/results",
    )
    request_id = handler.request_id
    print(request_id)

if __name__ == "__main__":
    asyncio.run(submit())
```

## 4. Проверка статуса и получение результата

```python
status = await fal_client.status_async("fal-ai/flux-pro-trainer", request_id, with_logs=True)
result = await fal_client.result_async("fal-ai/flux-pro-trainer", request_id)
```

## 5. Работа с файлами

- Можно передавать ссылки на публичные файлы (data_url)
- Можно использовать base64 data URI
- Можно загружать файлы через fal_client:

```python
url = fal_client.upload_file_async("path/to/file")
```

## 6. Схема запроса

### Входные параметры

| Параметр           | Тип      | Описание                                                                 | Значение по умолчанию / Enum |
|--------------------|----------|--------------------------------------------------------------------------|-----------------------------|
| data_url           | string   | URL к данным для обучения                                                |                             |
| mode               | enum     | Режим дообучения: character, product, style, general                     | character                   |
| finetune_comment   | string   | Описание/комментарий к задаче                                            |                             |
| iterations         | integer  | Количество итераций обучения                                             | 300                         |
| learning_rate      | float    | Learning rate для обучения                                               | 1e-5 (full), 1e-4 (LoRA)    |
| priority           | enum     | Приоритет: speed, quality, high_res_only                                 | quality                     |
| captioning         | boolean  | Включить/выключить автогенерацию подписей                                | true                        |
| trigger_word       | string   | Уникальное слово/фраза для генерации                                     | TOK                         |
| lora_rank          | integer  | 32 или 16. 16 — быстрее, 32 — качественнее                               | 32                          |
| finetune_type      | enum     | full (полное дообучение) или lora (LoRA)                                 | full                        |

Пример:

```json
{
  "data_url": "",
  "mode": "character",
  "finetune_comment": "test-1",
  "iterations": 300,
  "priority": "quality",
  "captioning": true,
  "trigger_word": "TOK",
  "lora_rank": 32,
  "finetune_type": "full"
}
```

### Выходные параметры

| Параметр      | Тип     | Описание                        |
|--------------|---------|----------------------------------|
| finetune_id  | string  | Идентификатор вашей модели       |

```json
{
  "finetune_id": ""
}
```

## 7. Примечания
- Не публикуйте свой FAL_KEY в клиентском коде.
- Для больших файлов используйте upload_file_async.
- Для долгих задач используйте webhook. 