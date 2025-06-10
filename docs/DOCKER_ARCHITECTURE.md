# 🐳 Архитектура Docker контейнеров Aisha Bot

> **Обновлено:** 2025-06-10  
> **Статус:** ✅ Финальная архитектура

## 📋 Обзор архитектуры

### 🎯 Принципы
- **Один режим = один контейнер** (polling, worker, webhook)
- **Идентичность dev/prod** - разные только volumes и networks
- **Масштабируемость** - горизонтальное добавление worker'ов
- **Безопасность** - разделение обязанностей между контейнерами

## 🏗️ Структура контейнеров

### 📁 Активные файлы конфигурации

```
├── docker-compose.bot.dev.yml      # 🔧 Development (локально)
├── docker-compose.bot.simple.yml   # 🚀 Production bot cluster  
└── docker-compose.webhook.prod.yml # 🌐 Production webhook API
```

### 🤖 Bot Containers

#### Development Environment
```yaml
# docker-compose.bot.dev.yml
services:
  aisha-bot-dev:        # Polling + UI
    BOT_MODE: polling
    SET_POLLING: true
    
  aisha-worker-dev:     # Background tasks
    BOT_MODE: worker
    SET_POLLING: false
```

#### Production Environment  
```yaml
# docker-compose.bot.simple.yml
services:
  bot-primary:          # Polling + UI
    BOT_MODE: polling
    SET_POLLING: true
    
  worker-1:             # Background tasks
    BOT_MODE: worker
    SET_POLLING: false
```

### 🌐 Webhook Services (Production Only)
```yaml
# docker-compose.webhook.prod.yml
services:
  aisha-webhook-api-1:  # FAL AI webhook обработчик
  aisha-webhook-api-2:  # Load balancing
  aisha-nginx-webhook:  # Reverse proxy
```

## 🔄 Режимы работы контейнеров

### 1. **Bot Polling Mode** 
- **Назначение**: Основной интерфейс пользователя
- **Функции**: 
  - ✅ Получение сообщений от Telegram
  - ✅ Обработка команд и callback'ов
  - ✅ Быстрые операции (команды, меню)
- **Ограничения**: Только ОДИН контейнер может делать polling

### 2. **Worker Mode**
- **Назначение**: Фоновые вычислительные задачи
- **Функции**:
  - ✅ Транскрибация аудио
  - ✅ AI обработка
  - ✅ Тяжелые операции
- **Масштабирование**: Можно запускать несколько worker'ов

### 3. **Webhook Mode** (Production)
- **Назначение**: Обработка внешних webhook'ов
- **Функции**:
  - ✅ FAL AI callback'и
  - ✅ API endpoint'ы
- **Балансировка**: Load balancer + 2 экземпляра

## 🌐 Сетевая архитектура

### Development
```
Local Machine (WSL2)
├── aisha-bot-dev     [polling]   127.0.0.1
├── aisha-worker-dev  [worker]    127.0.0.1
│
├── PostgreSQL        [external]  192.168.0.4:5432
├── Redis            [external]  192.168.0.3:6379
└── MinIO            [external]  192.168.0.4:9000
```

### Production
```
Production Cluster (192.168.0.10)
├── bot-primary      [polling]   172.26.0.10  
├── worker-1         [worker]    172.26.0.20
├── webhook-api-1    [webhook]   172.26.0.30
├── webhook-api-2    [webhook]   172.26.0.31  
└── nginx-webhook    [proxy]     172.26.0.40

External Services:
├── PostgreSQL       192.168.0.4:5432
├── Redis            192.168.0.3:6379  
├── MinIO            192.168.0.4:9000
└── Registry         192.168.0.4:5000
```

## 💾 Хранилище данных

### Volume mapping
```yaml
Development:
  - bot_dev_storage_temp:/app/storage/temp    # Временные файлы
  - bot_dev_storage_audio:/app/storage/audio  # Аудио кэш
  - bot_dev_logs:/app/logs                    # Логи
  
Production:
  - bot_storage_temp:/app/storage/temp        # Общие временные файлы
  - bot_storage_audio:/app/storage/audio      # Общий аудио кэш
  - bot_logs:/app/logs                        # Общие логи
```

## ⚙️ Переменные окружения

### 🔑 Критичные для работы
```bash
# Telegram
TELEGRAM_BOT_TOKEN=XXX        # Bot token
TELEGRAM_TOKEN=XXX            # Дублирование для совместимости

# AI APIs  
OPENAI_API_KEY=XXX           # Для транскрибации Whisper
FAL_API_KEY=XXX              # Для генерации изображений

# External Services
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
MINIO_ENDPOINT=192.168.0.4:9000
```

### 🏷️ Режим работы
```bash
BOT_MODE=polling             # polling | worker | webhook
SET_POLLING=true             # true только для polling контейнера
INSTANCE_ID=bot-primary      # Уникальный ID экземпляра
```

## 🚀 Команды управления

### Development
```bash
# Запуск development окружения
docker-compose -f docker-compose.bot.dev.yml up -d --build

# Просмотр логов
docker-compose -f docker-compose.bot.dev.yml logs -f aisha-bot-dev

# Остановка
docker-compose -f docker-compose.bot.dev.yml down
```

### Production  
```bash
# Запуск bot кластера
docker-compose -f docker-compose.bot.simple.yml up -d

# Запуск webhook сервисов
docker-compose -f docker-compose.webhook.prod.yml up -d

# Мониторинг
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
```

## 🎯 Ответы на вопросы

### ❓ Нужен ли worker на локальной машине?
**✅ ДА** - worker нужен для:
- Тестирования транскрибации
- Отладки AI функций  
- Полного воспроизведения продакшн среды

### ❓ Идентичность dev/prod?
**✅ ДОСТИГНУТА** - отличия только в:
- Именах контейнеров (`aisha-bot-dev` vs `bot-primary`)
- Networks (local bridge vs external cluster)
- Volumes (dev vs prod)
- Image source (build vs registry)

### ❓ Какие файлы нужны?
**3 файла:**
- ✅ `docker-compose.bot.dev.yml` - Development
- ✅ `docker-compose.bot.simple.yml` - Production bots
- ✅ `docker-compose.webhook.prod.yml` - Production webhooks

**Удален избыточный:**
- ❌ `docker-compose.bot.local.yml` - дублировал dev.yml

## 🔄 Процесс деплоя

### 1. Development → Registry
```bash
# Сборка и тест
docker-compose -f docker-compose.bot.dev.yml up -d --build

# Тегирование и пуш  
docker tag aisha-backend-aisha-bot-dev 192.168.0.4:5000/aisha/bot:latest
docker push 192.168.0.4:5000/aisha/bot:latest
```

### 2. Registry → Production
```bash
# На продакшн сервере
docker pull 192.168.0.4:5000/aisha/bot:latest
docker-compose -f docker-compose.bot.simple.yml up -d
```

## 📊 Мониторинг и здоровье

### Health Checks
```yaml
healthcheck:
  test: ["CMD", "pgrep", "-f", "python3"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

### Логирование
- **Development**: `LOG_LEVEL=DEBUG` с детальными логами
- **Production**: `LOG_LEVEL=INFO` с ротацией

## 🔐 Безопасность

### Container Security
- ✅ Non-root пользователь `aisha:aisha`
- ✅ Read-only файловая система где возможно
- ✅ Ограниченные ресурсы в продакшн

### Network Security  
- ✅ Изолированные networks
- ✅ Только необходимые порты
- ✅ Internal communication between containers

## 🎉 Заключение

Архитектура обеспечивает:
- **🔄 Идентичность dev/prod** - простой деплой без изменений
- **⚡ Производительность** - разделение polling/worker нагрузки  
- **📈 Масштабируемость** - легкое добавление worker'ов
- **🛡️ Надежность** - изоляция компонентов и fault tolerance 