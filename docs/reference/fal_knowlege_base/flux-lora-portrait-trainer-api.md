# FAL AI Flux LoRA Portrait Trainer API

> **Источник**: https://fal.ai/models/fal-ai/flux-lora-portrait-trainer/api?platform=python

## 📋 Обзор

**Модель**: `fal-ai/flux-lora-portrait-trainer`

FLUX LoRA training оптимизированная для генерации портретов с яркими бликами, отличным следованием промптам и высокодетализированными результатами.

**Особенности**:
- ✅ Training (обучение моделей)
- ✅ Commercial use (коммерческое использование)
- 🎯 Специализация на портретах
- 🚀 Высокое качество результатов

## 🚀 Быстрый старт

### 1. Установка клиента

```bash
pip install fal-client
```

### 2. Настройка API ключа

```bash
export FAL_KEY="YOUR_API_KEY"
```

### 3. Базовый пример использования

```python
import fal_client

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])

result = fal_client.subscribe(
    "fal-ai/flux-lora-portrait-trainer",
    arguments={
        "images_data_url": "https://example.com/training_data.zip"
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
print(result)
```

## 🔐 Аутентификация

### API Key

API использует API ключ для аутентификации. Рекомендуется установить переменную окружения `FAL_KEY`.

```python
import os
os.environ['FAL_KEY'] = 'your_api_key_here'
```

> ⚠️ **Безопасность**: При работе на клиентской стороне (браузер, мобильное приложение) НЕ раскрывайте ваш `FAL_KEY`. Используйте серверный прокси для запросов к API.

## 📨 Очередь запросов

### Отправка запроса

Для долгосрочных запросов (например, обучение моделей) рекомендуется использовать проверку статуса очереди и webhooks вместо блокирующего ожидания.

```python
import fal_client

# Отправка запроса
handler = fal_client.submit(
    "fal-ai/flux-lora-portrait-trainer",
    arguments={
        "images_data_url": "https://example.com/training_data.zip"
    },
    webhook_url="https://optional.webhook.url/for/results",
)

request_id = handler.request_id
print(f"Запрос отправлен: {request_id}")
```

### Проверка статуса

```python
# Проверка статуса запроса
status = fal_client.status(
    "fal-ai/flux-lora-portrait-trainer", 
    request_id, 
    with_logs=True
)
print(f"Статус: {status}")
```

### Получение результата

```python
# Получение результата после завершения
result = fal_client.result(
    "fal-ai/flux-lora-portrait-trainer", 
    request_id
)
print(f"Результат: {result}")
```

## 📁 Работа с файлами

### Data URI (base64)

Можно передавать Base64 data URI как вход для файлов:

```python
# Пример с base64
data_uri = "data:application/zip;base64,UEsDBBQAAgAIA..."
```

### Hosted files (URL)

Можно использовать публично доступные URL:

```python
images_url = "https://your-domain.com/training_data.zip"
```

### Загрузка файлов

FAL предоставляет удобное файловое хранилище:

```python
# Загрузка файла
url = fal_client.upload_file("path/to/training_data.zip")
print(f"Файл загружен: {url}")

# Использование загруженного файла
result = fal_client.subscribe(
    "fal-ai/flux-lora-portrait-trainer",
    arguments={
        "images_data_url": url
    }
)
```

## 📋 Схема API

### Input параметры

#### `images_data_url` *(required)*
- **Тип**: `string`
- **Описание**: URL к zip архиву с изображениями последовательного стиля
- **Рекомендации**: Используйте минимум 10 изображений, больше - лучше

**Структура архива**:
```
training_data.zip
├── image1.jpg
├── image1.txt          # Опциональные подписи
├── image2.jpg
├── image2.txt
└── ...
```

**Подписи (captions)**:
- Каждый текстовый файл должен иметь то же имя, что и соответствующее изображение
- Могут содержать специальную строку `[trigger]`
- Если указан `trigger_phrase`, он заменит `[trigger]` в подписях

#### `trigger_phrase` *(optional)*
- **Тип**: `string`
- **Описание**: Триггерная фраза для использования в подписях
- **Поведение**: Если не указан, триггерное слово не используется

#### `learning_rate` *(optional)*
- **Тип**: `float`
- **По умолчанию**: `0.00009`
- **Описание**: Скорость обучения

#### `steps` *(optional)*
- **Тип**: `integer`
- **По умолчанию**: `2500`
- **Описание**: Количество шагов обучения LoRA

#### `multiresolution_training` *(optional)*
- **Тип**: `boolean`
- **По умолчанию**: `true`
- **Описание**: Включает мультиразрешающее обучение

#### `subject_crop` *(optional)*
- **Тип**: `boolean`
- **По умолчанию**: `true`
- **Описание**: Автоматическая обрезка объекта в изображении

#### `data_archive_format` *(optional)*
- **Тип**: `string`
- **Описание**: Формат архива (автоопределение если не указан)

#### `resume_from_checkpoint` *(optional)*
- **Тип**: `string`
- **По умолчанию**: `""`
- **Описание**: URL чекпоинта для продолжения обучения

#### `create_masks` *(optional)*
- **Тип**: `boolean`
- **Описание**: Создание масок для объекта

### Пример входных данных

```json
{
  "images_data_url": "https://example.com/training_data.zip",
  "learning_rate": 0.0002,
  "steps": 1000,
  "multiresolution_training": true,
  "subject_crop": true,
  "create_masks": false,
  "trigger_phrase": "TOK"
}
```

### Output результат

#### `diffusers_lora_file` *(required)*
- **Тип**: `File`
- **Описание**: URL к обученным diffusers LoRA весам

#### `config_file` *(required)*
- **Тип**: `File`
- **Описание**: URL к файлу конфигурации обучения

### Пример результата

```json
{
  "diffusers_lora_file": {
    "url": "https://fal.ai/files/trained_lora.safetensors",
    "content_type": "application/octet-stream",
    "file_name": "trained_lora.safetensors",
    "file_size": 144041920
  },
  "config_file": {
    "url": "https://fal.ai/files/training_config.json",
    "content_type": "application/json", 
    "file_name": "training_config.json",
    "file_size": 4404
  }
}
```

### File объект

```json
{
  "url": "string",           // URL для скачивания файла
  "content_type": "string",  // MIME тип файла
  "file_name": "string",     // Имя файла (автогенерация если не указано)
  "file_size": "integer",    // Размер файла в байтах
  "file_data": "string"      // Данные файла
}
```

## 🛠️ Интеграция в проект

### Класс для работы с FAL Portrait Trainer

```python
import fal_client
from typing import Optional, Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

class FALPortraitTrainer:
    """Класс для обучения портретных LoRA моделей через FAL AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            import os
            os.environ['FAL_KEY'] = api_key
    
    async def train_avatar(
        self,
        images_data_url: str,
        trigger_phrase: Optional[str] = None,
        learning_rate: float = 0.00009,
        steps: int = 2500,
        multiresolution_training: bool = True,
        subject_crop: bool = True,
        create_masks: bool = False
    ) -> Dict[str, Any]:
        """
        Запускает обучение портретной LoRA модели
        
        Args:
            images_data_url: URL к zip архиву с изображениями
            trigger_phrase: Триггерная фраза
            learning_rate: Скорость обучения
            steps: Количество шагов
            multiresolution_training: Мультиразрешающее обучение
            subject_crop: Автообрезка объекта
            create_masks: Создание масок
            
        Returns:
            Dict с результатами обучения
        """
        try:
            # Аргументы для обучения
            arguments = {
                "images_data_url": images_data_url,
                "learning_rate": learning_rate,
                "steps": steps,
                "multiresolution_training": multiresolution_training,
                "subject_crop": subject_crop,
                "create_masks": create_masks
            }
            
            if trigger_phrase:
                arguments["trigger_phrase"] = trigger_phrase
            
            logger.info(f"Запуск обучения FAL AI с параметрами: {arguments}")
            
            # Функция для обновлений из очереди
            def on_queue_update(update):
                if isinstance(update, fal_client.InProgress):
                    for log in update.logs:
                        logger.info(f"[FAL AI] {log['message']}")
            
            # Отправка запроса с подпиской на обновления
            result = fal_client.subscribe(
                "fal-ai/flux-lora-portrait-trainer",
                arguments=arguments,
                with_logs=True,
                on_queue_update=on_queue_update,
            )
            
            logger.info("Обучение FAL AI завершено успешно")
            return result
            
        except Exception as e:
            logger.exception(f"Ошибка при обучении FAL AI: {e}")
            raise
    
    async def train_avatar_async(
        self,
        images_data_url: str,
        webhook_url: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Асинхронный запуск обучения (только отправка, без ожидания)
        
        Args:
            images_data_url: URL к архиву с изображениями
            webhook_url: URL для webhook уведомлений
            **kwargs: Дополнительные параметры обучения
            
        Returns:
            request_id для отслеживания статуса
        """
        try:
            arguments = {
                "images_data_url": images_data_url,
                **kwargs
            }
            
            # Отправка без ожидания результата
            handler = fal_client.submit(
                "fal-ai/flux-lora-portrait-trainer",
                arguments=arguments,
                webhook_url=webhook_url
            )
            
            request_id = handler.request_id
            logger.info(f"Асинхронное обучение запущено: {request_id}")
            
            return request_id
            
        except Exception as e:
            logger.exception(f"Ошибка при асинхронном запуске обучения: {e}")
            raise
    
    async def check_training_status(self, request_id: str) -> Dict[str, Any]:
        """
        Проверяет статус обучения
        
        Args:
            request_id: ID запроса
            
        Returns:
            Dict со статусом обучения
        """
        try:
            status = fal_client.status(
                "fal-ai/flux-lora-portrait-trainer",
                request_id,
                with_logs=True
            )
            
            logger.debug(f"Статус обучения {request_id}: {status}")
            return status
            
        except Exception as e:
            logger.exception(f"Ошибка при проверке статуса: {e}")
            raise
    
    async def get_training_result(self, request_id: str) -> Dict[str, Any]:
        """
        Получает результат обучения
        
        Args:
            request_id: ID запроса
            
        Returns:
            Dict с результатами обучения
        """
        try:
            result = fal_client.result(
                "fal-ai/flux-lora-portrait-trainer",
                request_id
            )
            
            logger.info(f"Результат обучения получен для {request_id}")
            return result
            
        except Exception as e:
            logger.exception(f"Ошибка при получении результата: {e}")
            raise
    
    async def upload_training_data(self, file_path: str) -> str:
        """
        Загружает файл с тренировочными данными
        
        Args:
            file_path: Путь к zip файлу
            
        Returns:
            URL загруженного файла
        """
        try:
            url = fal_client.upload_file(file_path)
            logger.info(f"Файл загружен: {url}")
            return url
            
        except Exception as e:
            logger.exception(f"Ошибка при загрузке файла: {e}")
            raise
```

### Использование в сервисе аватаров

```python
# В app/services/avatar/training_service.py

from .fal_portrait_trainer import FALPortraitTrainer

class AvatarTrainingService:
    def __init__(self):
        self.fal_trainer = FALPortraitTrainer()
    
    async def start_training(self, avatar_id: UUID, training_data_url: str) -> str:
        """Запускает обучение аватара"""
        
        # Настройки для портретного обучения
        trigger_phrase = f"TOK_{avatar_id.hex[:8]}"  # Уникальный триггер
        
        request_id = await self.fal_trainer.train_avatar_async(
            images_data_url=training_data_url,
            trigger_phrase=trigger_phrase,
            steps=1000,  # Меньше шагов для быстрого результата
            learning_rate=0.0002,
            subject_crop=True,
            create_masks=True
        )
        
        return request_id
```

## 📚 Рекомендации

### Подготовка данных

1. **Количество изображений**: Минимум 10, оптимально 20-50
2. **Качество**: Высокое разрешение, хорошее освещение
3. **Разнообразие**: Разные углы, выражения лица, освещение
4. **Подписи**: Детальные описания помогают лучшему обучению

### Настройки обучения

- **Портреты**: `steps=1000-2500`, `learning_rate=0.0001-0.0002`
- **Стили**: `steps=2000-4000`, `learning_rate=0.00005-0.0001`
- **Быстрое обучение**: `steps=500-1000`, больше `learning_rate`
- **Качественное обучение**: `steps=3000+`, меньше `learning_rate`

### Обработка ошибок

```python
# Типичные ошибки и их обработка
try:
    result = await fal_trainer.train_avatar(...)
except Exception as e:
    if "insufficient images" in str(e):
        # Недостаточно изображений
        raise ValueError("Нужно минимум 10 изображений")
    elif "invalid format" in str(e):
        # Неверный формат архива
        raise ValueError("Архив должен быть в формате ZIP")
    else:
        # Общая ошибка
        raise
```

## 🔗 Полезные ссылки

- [Официальная документация FAL AI](https://fal.ai/models/fal-ai/flux-lora-portrait-trainer)
- [FAL AI Python Client](https://github.com/fal-ai/fal)
- [Руководство по загрузке файлов](https://fal.ai/docs/file-upload)
- [Серверная интеграция](https://fal.ai/docs/integrations/server-side) 