# 🚀 Быстрый запуск системы обучения аватаров

## 📋 Что реализовано

✅ **Автовыбор API в зависимости от стиля аватара:**
- 🎭 **Портретный стиль** → `fal-ai/flux-lora-portrait-trainer`
- 🎨 **Художественный стиль** → `fal-ai/flux-pro-trainer`

✅ **Тестовый режим** - полная имитация без затрат на FAL AI

✅ **Webhook система** для уведомлений о готовности аватара

✅ **Автоматические уведомления** пользователям в Telegram

## ⚡ Быстрый запуск

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

```env
# Обязательные настройки
TELEGRAM_TOKEN=your_telegram_bot_token
FAL_API_KEY=your_fal_api_key

# Тестовый режим (рекомендуется для начала)
AVATAR_TEST_MODE=true
FAL_ENABLE_WEBHOOK_SIMULATION=true
FAL_MOCK_TRAINING_DURATION=30

# Webhook URL (замените на ваш домен)
FAL_WEBHOOK_URL=https://yourdomain.com/webhook/fal/status
```

### 3. Запуск системы

**Терминал 1 - Telegram бот:**
```bash
python -m app.main
```

**Терминал 2 - API сервер для webhook:**
```bash
python run_api_server.py
```

### 4. Тестирование

```bash
python test_avatar_training_system.py
```

## 🎯 Как это работает

### Выбор API

```python
# Автоматический выбор в зависимости от training_type
if training_type == "portrait":
    # Для селфи и портретов → быстрее и качественнее
    endpoint = "fal-ai/flux-lora-portrait-trainer"
else:
    # Для стилей и объектов → универсальнее
    endpoint = "fal-ai/flux-pro-trainer"
```

### Статусы аватара

1. **Отправка на обучение** → статус `TRAINING`
2. **Процесс обучения** → обновление прогресса
3. **Завершение** → статус `COMPLETED` + уведомление пользователю

### Уведомления

При завершении обучения пользователь получает сообщение:

```
🎉 Ваш аватар готов!

🎭 **Мой Аватар** (Портретный стиль)
✅ Обучение завершено успешно

Теперь вы можете использовать аватар для генерации изображений!
```

## 🧪 Тестовый режим

При `AVATAR_TEST_MODE=true`:

- ❌ Реальные запросы к FAL AI **НЕ отправляются**
- ✅ Полная имитация процесса обучения
- ✅ Тестирование webhook и уведомлений
- ✅ Нет затрат на API

**Логи в тестовом режиме:**
```
🧪 ТЕСТ РЕЖИМ: Пропускаем отправку на обучение для аватара abc123, тип: portrait
🧪 Сгенерирован тестовый request_id: test_abc123_def456
🧪 Имитация обучения portrait, завершение через 30 секунд
```

## 📡 Webhook endpoints

- **Health check:** `GET http://localhost:8000/health`
- **FAL webhook:** `POST http://localhost:8000/webhook/fal/status`
- **API info:** `GET http://localhost:8000/`

## 🔧 Troubleshooting

### Проблема: Webhook не приходят
```bash
# Проверьте что API сервер запущен
curl http://localhost:8000/health

# Для локальной разработки используйте ngrok
ngrok http 8000
```

### Проблема: Ошибки FAL API
```bash
# Включите тестовый режим
export AVATAR_TEST_MODE=true

# Проверьте API ключ
echo $FAL_API_KEY
```

### Проблема: Уведомления не приходят
```bash
# Проверьте токен бота
echo $TELEGRAM_TOKEN

# Проверьте логи API сервера
tail -f app_test.log
```

## 📊 Мониторинг

```bash
# Проверка здоровья системы
curl http://localhost:8000/health

# Логи Telegram бота
tail -f app_test.log

# Логи API сервера
# Смотрите в консоли где запущен run_api_server.py
```

## 🎉 Готово!

Система готова к использованию. В тестовом режиме вы можете полностью протестировать весь workflow без затрат на FAL AI.

Для продакшн использования:
1. Установите `AVATAR_TEST_MODE=false`
2. Настройте правильный `FAL_WEBHOOK_URL`
3. Убедитесь что у вас есть кредиты на FAL AI 