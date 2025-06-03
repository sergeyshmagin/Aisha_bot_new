# ✅ Docker Infrastructure Ready!

Docker инфраструктура для Aisha Bot v2 настроена и готова к использованию.

## 🎯 Что было настроено

### ✅ Архитектура
- **Unified Architecture**: И dev, и prod используют внешние сервисы
- **Внешние сервисы**: PostgreSQL, Redis, MinIO уже настроены
- **Контейнеризация**: Только приложения (bot + api)

### ✅ Docker файлы
- `docker/Dockerfile.bot` - Multi-stage сборка бота (dev/prod)
- `docker/Dockerfile.api` - Multi-stage сборка API (dev/prod) 
- `docker-compose.yml` - Development окружение
- `docker-compose.prod.yml` - Production окружение с Nginx

### ✅ Environment Templates
- `docker/env-templates/dev.env.template` - С реальными API ключами
- `docker/env-templates/prod.env.template` - Для production деплоя
- Полная конфигурация FAL AI, OpenAI, Telegram

### ✅ Production Infrastructure
- **Nginx** с SSL поддержкой
- **Health checks** для всех сервисов
- **Resource limits** и автоматический restart
- **Replicas** для API (2 инстанса)

### ✅ Automation Scripts
- `scripts/health-check.sh` - Проверка внешних сервисов
- `scripts/deploy.sh` - Автоматизация деплоя
- `scripts/wait-for-it.sh` - Утилита ожидания сервисов

## 🚀 Быстрый старт

### 1. Создайте .env файлы:

```bash
cp docker/env-templates/dev.env.template .env.docker.dev
cp docker/env-templates/prod.env.template .env.docker.prod
```

### 2. Проверьте внешние сервисы:

```bash
chmod +x scripts/health-check.sh
./scripts/health-check.sh
```

### 3. Запустите development:

```bash
# Сборка и запуск
docker-compose up -d

# Проверка логов
docker-compose logs -f

# Остановка
docker-compose down
```

### 4. Запуск production:

```bash
# Обновите секреты в .env.docker.prod перед запуском!
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Подключения

### Development:
- **API**: http://localhost:8000
- **Bot**: работает через polling/webhook
- **Logs**: `./logs/` папка

### Production:
- **HTTPS**: https://aibots.kz (через Nginx)
- **Health check**: `/health` endpoint
- **SSL**: требуются сертификаты в `./ssl_certificate/`

## 📊 Архитектура подключений

```
[Docker Containers]              [External Services]
┌─────────────────┐             ┌─────────────────┐
│  aisha-bot      │◄────────────┤ PostgreSQL      │
│  (container)    │             │ 192.168.0.4:5432│
└─────────────────┘             └─────────────────┘
┌─────────────────┐             ┌─────────────────┐
│  aisha-api      │◄────────────┤ Redis           │
│  (container)    │             │ 192.168.0.3:6379│
└─────────────────┘             └─────────────────┘
┌─────────────────┐             ┌─────────────────┐
│  nginx          │◄────────────┤ MinIO           │
│  (prod only)    │             │ 192.168.0.4:9000│
└─────────────────┘             └─────────────────┘
```

## 🔐 Важные настройки

### Для production обязательно обновите:
- `JWT_SECRET_KEY` - безопасный JWT секрет
- `PASSWORD_SALT` - соль для паролей  
- `TELEGRAM_WEBHOOK_SECRET` - секрет webhook
- `FAL_WEBHOOK_SECRET` - секрет FAL webhook

### Проверьте SSL сертификаты:
```bash
# Должны быть в папке ./ssl_certificate/
ls -la ssl_certificate/
```

## 🛠️ Полезные команды

```bash
# Перестроить контейнеры
docker-compose build --no-cache

# Логи конкретного сервиса
docker-compose logs -f aisha-bot

# Выполнить команду в контейнере
docker-compose exec aisha-bot bash

# Проверить статус
docker-compose ps

# Очистить все
docker-compose down -v
docker system prune -f
```

## 🎉 Готово!

Теперь у вас есть полноценная Docker инфраструктура для разработки и production деплоя Aisha Bot v2 с подключением к существующим внешним сервисам.

**Следующие шаги:**
1. Запустите development окружение
2. Протестируйте функциональность
3. Настройте production секреты
4. Деплойте на production сервер 