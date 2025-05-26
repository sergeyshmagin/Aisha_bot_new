# 🎭 Настройка системы обучения аватаров

## 📋 Обзор

Система поддерживает два типа обучения аватаров с автоматическим выбором API:

- **🎭 Портретный стиль** → `fal-ai/flux-lora-portrait-trainer`
- **🎨 Художественный стиль** → `fal-ai/flux-pro-trainer`

## ⚙️ Конфигурация

### 1. Переменные окружения

```env
# FAL AI API
FAL_API_KEY=your_fal_api_key_here
FAL_WEBHOOK_URL=https://yourdomain.com/webhook/fal/status

# Тестовый режим (отключает реальные запросы к FAL AI)
AVATAR_TEST_MODE=true

# Настройки webhook симуляции для тестирования
FAL_ENABLE_WEBHOOK_SIMULATION=true
FAL_MOCK_TRAINING_DURATION=30

# Telegram Bot
TELEGRAM_TOKEN=your_telegram_bot_token
```

### 2. Настройки качества обучения

В `app/core/config.py` настроены пресеты качества:

```python
# Быстрое обучение (3-5 минут)
FAL_PRESET_FAST = {
    "portrait": {"steps": 500, "learning_rate": 0.0003},
    "general": {"iterations": 200, "learning_rate": 2e-4, "priority": "speed"}
}

# Сбалансированное обучение (5-15 минут)
FAL_PRESET_BALANCED = {
    "portrait": {"steps": 1000, "learning_rate": 0.0002},
    "general": {"iterations": 500, "learning_rate": 1e-4, "priority": "quality"}
}

# Качественное обучение (15-30 минут)
FAL_PRESET_QUALITY = {
    "portrait": {"steps": 2500, "learning_rate": 0.0001},
    "general": {"iterations": 1000, "learning_rate": 5e-5, "priority": "quality"}
}
```

## 🚀 Запуск системы

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Запуск Telegram бота

```bash
python -m app.main
```

### 3. Запуск API сервера для webhook

```bash
python run_api_server.py
```

Или через uvicorn:

```bash
uvicorn app.api_server:app --host 0.0.0.0 --port 8000 --reload
```

## 🔄 Workflow обучения

### 1. Выбор типа обучения

Пользователь выбирает тип аватара:
- **Портретный** → оптимизирован для фотографий людей
- **Художественный** → универсальный для любого контента

### 2. Автоматический выбор API

```python
if training_type == "portrait":
    # 🎭 Flux LoRA Portrait Trainer
    endpoint = "fal-ai/flux-lora-portrait-trainer"
    config = {
        "trigger_phrase": f"TOK_{avatar_id}",
        "steps": preset["steps"],
        "learning_rate": preset["learning_rate"],
        "multiresolution_training": True,
        "subject_crop": True,
        "create_masks": True
    }
else:
    # 🎨 Flux Pro Trainer  
    endpoint = "fal-ai/flux-pro-trainer"
    config = {
        "trigger_word": f"TOK_{avatar_id}",
        "iterations": preset["iterations"],
        "learning_rate": preset["learning_rate"],
        "auto_captioning": True,
        "create_masks": True
    }
```

### 3. Обновление статусов

1. **Отправка на обучение** → статус `TRAINING`
2. **Получение webhook** → обновление прогресса
3. **Завершение обучения** → статус `COMPLETED` + уведомление пользователю

## 📡 Webhook система

### Endpoint

```
POST /webhook/fal/status
```

### Формат webhook от FAL AI

```json
{
    "request_id": "req_123456789",
    "status": "completed",
    "progress": 100,
    "training_type": "portrait",
    "result": {
        "diffusers_lora_file": {
            "url": "https://fal.ai/files/model.safetensors",
            "file_name": "avatar_model.safetensors"
        }
    }
}
```

### Обработка webhook

1. **Получение webhook** → быстрый ответ `200 OK`
2. **Фоновая обработка** → обновление БД
3. **Уведомление пользователя** → отправка сообщения в Telegram

## 🧪 Тестовый режим

При `AVATAR_TEST_MODE=true`:

- ❌ Реальные запросы к FAL AI **не отправляются**
- ✅ Имитация обучения с настраиваемой длительностью
- ✅ Симуляция webhook для тестирования UX
- ✅ Полное тестирование без затрат

### Логи тестового режима

```
🧪 ТЕСТ РЕЖИМ: Пропускаем отправку на обучение для аватара abc123, тип: portrait
🧪 Сгенерирован тестовый request_id: test_abc123_def456
🧪 Имитация обучения portrait, завершение через 30 секунд
🧪 Тестовый webhook отправлен: 200
```

## 📊 Мониторинг

### Health check

```bash
curl http://localhost:8000/health
```

### Проверка статуса обучения

```python
from app.services.avatar.fal_training_service import FALTrainingService

service = FALTrainingService()
status = await service.check_training_status(request_id, training_type)
```

## 🔧 Troubleshooting

### 1. Webhook не приходят

- Проверьте `FAL_WEBHOOK_URL` в настройках
- Убедитесь что API сервер запущен на правильном порту
- Проверьте доступность URL извне (ngrok для локальной разработки)

### 2. Ошибки FAL API

- Проверьте `FAL_API_KEY`
- Убедитесь что у вас достаточно кредитов на FAL AI
- Включите тестовый режим для отладки: `AVATAR_TEST_MODE=true`

### 3. Уведомления не приходят

- Проверьте `TELEGRAM_TOKEN`
- Убедитесь что бот имеет права отправлять сообщения пользователю
- Проверьте логи API сервера

## 📈 Производительность

### Время обучения

| Тип | Пресет | Время | Качество |
|-----|--------|-------|----------|
| Портретный | Fast | 3-5 мин | ⭐⭐⭐ |
| Портретный | Balanced | 5-15 мин | ⭐⭐⭐⭐ |
| Портретный | Quality | 15-30 мин | ⭐⭐⭐⭐⭐ |
| Художественный | Fast | 5-10 мин | ⭐⭐⭐ |
| Художественный | Balanced | 10-20 мин | ⭐⭐⭐⭐ |
| Художественный | Quality | 20-45 мин | ⭐⭐⭐⭐⭐ |

### Рекомендации

- **Портретные аватары**: используйте для селфи и фотографий людей
- **Художественные аватары**: используйте для стилей, объектов, архитектуры
- **Тестовый режим**: всегда тестируйте новые функции перед продакшн 