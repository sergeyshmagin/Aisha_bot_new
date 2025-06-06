# 🚀 Aisha Bot FAL Webhook API Server

Отдельный FastAPI сервер для обработки webhook уведомлений от FAL AI с SSL поддержкой.

## 🏗️ Архитектура

```
api_server/
├── app/
│   ├── core/
│   │   ├── config.py      # Конфигурация API сервера
│   │   └── logger.py      # Система логирования
│   ├── routers/
│   │   ├── __init__.py
│   │   └── fal_webhook.py # Webhook роутер
│   └── main.py            # Основное FastAPI приложение
├── ssl/                   # SSL сертификаты
├── logs/                  # Логи API сервера
├── requirements.txt       # Зависимости
├── env.example           # Пример конфигурации
└── run_api_server.py     # Скрипт запуска
```

## 🔧 Установка и настройка

### 1. Установка зависимостей
```bash
cd api_server
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
```bash
cp env.example .env
# Отредактируйте .env файл с вашими настройками
```

### 3. SSL сертификаты
SSL сертификаты уже скопированы в папку `ssl/`:
- `aibots_kz.crt` - основной сертификат
- `aibots.kz.key` - приватный ключ
- `aibots_kz.ca-bundle` - промежуточные сертификаты

## 🚀 Запуск

### Продакшн режим (с SSL)
```bash
python run_api_server.py
```

### Разработка (без SSL)
```bash
# В .env установите SSL_ENABLED=false
python -m app.main
```

## 📡 Endpoints

### Webhook
- **POST** `/api/v1/avatar/status_update` - Основной webhook для FAL AI
- **GET** `/api/v1/health` - Проверка здоровья сервера
- **GET** `/api/v1/webhook/status` - Статус webhook системы

### Мониторинг
- **GET** `/` - Корневая страница с информацией о сервере

## 🔒 Безопасность

- **SSL/TLS** - Обязательно для FAL AI webhook
- **TrustedHost** - Ограничение доменов
- **CORS** - Настроенный для продакшн
- **IP фильтрация** - Только IP адреса FAL AI

## 📊 Логирование

Логи сохраняются в папке `logs/`:
- `api_server.log` - Общие логи API сервера
- `webhook.log` - Специальные логи webhook

## 🔄 Интеграция с основным ботом

API сервер интегрируется с основным проектом через:
- Общую базу данных
- Сервисы обучения аватаров
- Telegram Bot для уведомлений

## 🧪 Тестирование

```bash
# Проверка здоровья
curl https://aibots.kz:8443/health

# Статус webhook
curl https://aibots.kz:8443/api/v1/webhook/status

# Тестовый webhook (POST)
curl -X POST https://aibots.kz:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{"request_id": "test_123", "status": "completed"}'
```

## 🔧 Конфигурация

Основные настройки в `app/core/config.py`:

- `API_HOST` - Хост сервера (0.0.0.0)
- `API_PORT` - Порт сервера (8443)
- `SSL_ENABLED` - Включение SSL (true)
- `DATABASE_URL` - URL базы данных
- `TELEGRAM_TOKEN` - Токен Telegram бота
- `FAL_API_KEY` - API ключ FAL AI

## 🚨 Важные замечания

1. **SSL обязателен** - FAL AI требует HTTPS для webhook
2. **Порт 8443** - Стандартный HTTPS порт для webhook
3. **Домен aibots.kz** - Настроен в SSL сертификатах
4. **Фоновая обработка** - Webhook обрабатывается асинхронно
5. **Автоматические уведомления** - Пользователи получают уведомления в Telegram

## 🔄 Развертывание

### Systemd сервис (Linux)
```bash
# Создайте файл /etc/systemd/system/aisha-webhook-api.service
[Unit]
Description=Aisha Bot FAL Webhook API
After=network.target

[Service]
Type=simple
User=aisha
WorkingDirectory=/path/to/api_server
ExecStart=/path/to/python run_api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker (опционально)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8443
CMD ["python", "run_api_server.py"]
``` 