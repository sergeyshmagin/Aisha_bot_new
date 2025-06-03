# TestModeSimulator

**Файл:** `app/services/avatar/fal_training_service/test_simulator.py`

## Описание

Симулятор тестового режима для FAL Training Service. Предназначен для разработки и тестирования без затрат на FAL AI. Выделен из основного сервиса для соблюдения правила ≤500 строк.

## Архитектура

```
TestModeSimulator
├── __init__(webhook_url)
├── simulate_training()          # Имитация процесса обучения
├── _simulate_webhook_callback() # Приватный метод webhook
├── simulate_status_check()      # Проверка статуса обучения
├── simulate_training_result()   # Результат обучения
└── simulate_general_training_result() # Универсальный результат
```

## API Методы

### `__init__(webhook_url: str)`
Инициализация симулятора с URL для webhook уведомлений.

**Параметры:**
- `webhook_url` (str): URL для отправки webhook уведомлений

### `simulate_training(avatar_id: UUID, training_type: str) -> str`
Имитация запуска процесса обучения аватара.

**Параметры:**
- `avatar_id` (UUID): Идентификатор аватара
- `training_type` (str): Тип обучения ("portrait", etc.)

**Возвращает:**
- `str`: Мок request_id в формате `test_{avatar_id[:8]}_{uuid[:8]}`

**Поведение:**
- Генерирует уникальный тестовый request_id
- Имитирует 1-секундную задержку
- Опционально запускает webhook callback (если включен `FAL_ENABLE_WEBHOOK_SIMULATION`)

### `simulate_status_check(request_id: str, training_type: str) -> Dict[str, Any]`
Проверка статуса имитируемого обучения.

**Параметры:**
- `request_id` (str): Идентификатор запроса
- `training_type` (str): Тип обучения

**Возвращает:**
```python
{
    "status": "in_progress" | "completed" | "unknown",
    "progress": int,  # 0-100
    "logs": List[str],
    "request_id": str
}
```

**Логика:**
- Для тестовых request_id (начинающихся с "test_"): имитирует прогресс
- Для неизвестных request_id: возвращает статус "unknown"

### `simulate_training_result(request_id: str, training_type: str) -> Dict[str, Any]`
Генерация мок-результата обучения.

**Возвращает:**
```python
{
    "test_mode": True,
    "request_id": str,
    "training_type": str,
    "mock_model_url": str,
    "diffusers_lora_file": {
        "url": str,
        "file_name": str
    }
}
```

### `simulate_general_training_result(avatar_id: UUID, training_type: str) -> Dict[str, Any]`
Универсальный мок-результат для совместимости.

**Возвращает:**
```python
{
    "finetune_id": str,
    "request_id": str
}
```

## Конфигурация

### Переменные окружения
- `FAL_ENABLE_WEBHOOK_SIMULATION` (bool): Включить webhook симуляцию
- `FAL_MOCK_TRAINING_DURATION` (int): Длительность имитации в секундах (по умолчанию: 30)

## Приватные методы

### `_simulate_webhook_callback(request_id, avatar_id, training_type)`
Асинхронная имитация webhook callback после завершения "обучения".

**Поведение:**
- Ждет `FAL_MOCK_TRAINING_DURATION` секунд
- Отправляет POST запрос на webhook URL с результатами
- Использует `WebhookURLBuilder` для построения URL

## Использование

```python
from app.services.avatar.fal_training_service.test_simulator import TestModeSimulator

# Инициализация
simulator = TestModeSimulator("https://api.example.com/webhook")

# Запуск имитации обучения
request_id = await simulator.simulate_training(avatar_id, "portrait")

# Проверка статуса
status = await simulator.simulate_status_check(request_id, "portrait")

# Получение результата
result = simulator.simulate_training_result(request_id, "portrait")
```

## Зависимости

- `asyncio`: Асинхронные операции
- `aiohttp`: HTTP клиент для webhook
- `uuid`: Генерация уникальных идентификаторов
- `app.core.config.settings`: Конфигурация приложения
- `app.core.logger`: Логирование

## Примечания

- Класс предназначен только для разработки/тестирования
- Все URL и результаты являются мок-данными
- Webhook callback запускается в фоновой задаче
- Прогресс обучения имитируется линейно

## Статус

✅ **Активный** - Используется в тестовом режиме FAL Training Service 