# 🔄 Миграция на новый API сервер для FAL AI Webhook

## 📋 Обзор изменений

Создан отдельный FastAPI сервер для обработки webhook от FAL AI с полной SSL поддержкой, заменяющий старую реализацию из `archive/backend_api`.

## 🏗️ Новая архитектура

### Разделение ответственности
- **Основной бот** (`app/`) - Telegram интерфейс и бизнес-логика
- **API сервер** (`api_server/`) - Webhook обработка с SSL

### Преимущества разделения
1. **Масштабируемость** - Можно развернуть на разных серверах
2. **Безопасность** - Изолированный SSL endpoint
3. **Производительность** - Независимые процессы
4. **Мониторинг** - Отдельные логи и метрики

## 🔄 Что было улучшено

### Из старой реализации взято:
- ✅ Парсинг комментариев FAL AI
- ✅ Логирование webhook событий  
- ✅ Отправка уведомлений в Telegram
- ✅ Обработка статусов обучения

### Новые возможности:
- 🆕 **SSL/TLS поддержка** - Обязательно для FAL AI
- 🆕 **Фоновая обработка** - BackgroundTasks для быстрого ответа
- 🆕 **Интеграция с новой системой** - Работа с AvatarTrainingService
- 🆕 **Улучшенная безопасность** - TrustedHost, CORS, IP фильтрация
- 🆕 **Мониторинг** - Health check и status endpoints
- 🆕 **Типизация** - Полная поддержка типов Python

## 📡 Изменения в webhook URL

### Старый endpoint:
```
http://domain/api/avatar/status_update
```

### Новый endpoint:
```
https://aibots.kz:8443/api/v1/avatar/status_update
```

### Ключевые изменения:
- **HTTPS** вместо HTTP (SSL обязателен)
- **Порт 8443** для webhook
- **Версионирование API** (/api/v1/)
- **Домен aibots.kz** с SSL сертификатом

## 🔧 Настройка развертывания

### 1. Два процесса
```bash
# Процесс 1: Основной Telegram бот
python -m app.main

# Процесс 2: API сервер для webhook
cd api_server && python run_api_server.py
```

### 2. Переменные окружения
Добавить в основной `.env`:
```env
# FAL AI Webhook (теперь использует отдельный API сервер)
FAL_WEBHOOK_URL=https://aibots.kz:8443/api/v1/avatar/status_update
```

### 3. SSL сертификаты
Сертификаты скопированы в `api_server/ssl/`:
- `aibots_kz.crt`
- `aibots.kz.key` 
- `aibots_kz.ca-bundle`

## 🔄 Процесс миграции

### Шаг 1: Остановка старого сервера
```bash
# Остановите старый backend_api если он запущен
```

### Шаг 2: Установка зависимостей
```bash
cd api_server
pip install -r requirements.txt
```

### Шаг 3: Настройка конфигурации
```bash
cd api_server
cp env.example .env
# Отредактируйте .env с вашими настройками
```

### Шаг 4: Запуск нового API сервера
```bash
cd api_server
python run_api_server.py
```

### Шаг 5: Обновление FAL AI webhook URL
В настройках FAL AI обновите webhook URL на:
```
https://aibots.kz:8443/api/v1/avatar/status_update
```

## 🧪 Тестирование миграции

### 1. Проверка SSL
```bash
curl https://aibots.kz:8443/health
```

### 2. Проверка webhook статуса
```bash
curl https://aibots.kz:8443/api/v1/webhook/status
```

### 3. Тестовый webhook
```bash
curl -X POST https://aibots.kz:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test_123",
    "status": "completed",
    "training_type": "portrait"
  }'
```

## 📊 Мониторинг

### Логи API сервера
```bash
tail -f api_server/logs/api_server.log
tail -f api_server/logs/webhook.log
```

### Проверка процессов
```bash
# Проверка что оба процесса запущены
ps aux | grep python
```

## 🚨 Важные замечания

1. **Обязательный SSL** - FAL AI требует HTTPS для webhook
2. **Порт 8443** - Убедитесь что порт открыт в firewall
3. **Домен aibots.kz** - SSL сертификат привязан к этому домену
4. **База данных** - API сервер использует ту же БД что и основной бот
5. **Telegram токен** - Нужен для отправки уведомлений

## 🔄 Откат (если нужен)

Если возникнут проблемы, можно временно вернуться к старой схеме:

1. Остановить новый API сервер
2. Запустить старый backend_api (без SSL)
3. Обновить webhook URL в FAL AI на старый
4. Исправить проблемы в новом API сервере
5. Повторить миграцию

## 📈 Планы развития

- **Docker контейнеризация** API сервера
- **Load balancer** для высокой доступности  
- **Метрики и мониторинг** (Prometheus/Grafana)
- **Rate limiting** для защиты от спама
- **Webhook retry механизм** для надежности 