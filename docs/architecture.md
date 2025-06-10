# 🏗️ Архитектура Aisha Bot

## 📋 Общий обзор

Aisha Bot - это распределенная система для создания AI аватаров пользователей с поддержкой голосовых сообщений, развернутая в продакшн кластере.

## 🌐 Топология сети

```
📡 Internet
    ↓
🔄 Load Balancer (192.168.0.10:80/443)
    ↓
┌─────────────────────────────────────────────┐
│            Продакшн кластер                 │
│                192.168.0.10                │
├─────────────────────────────────────────────┤
│ 🌐 Nginx Proxy                             │
│ ├── Webhook API (8001)                     │
│ └── Static Files                           │
├─────────────────────────────────────────────┤
│ 🤖 Bot Cluster                             │
│ ├── Primary Bot (polling)                  │
│ ├── Standby Bot (failover)                 │
│ └── Background Worker                       │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│          Внешние сервисы                    │
├─────────────────────────────────────────────┤
│ 🗄️  PostgreSQL (192.168.0.4:5432)          │
│ 🔴 Redis (192.168.0.3:6379)                │
│ 🐳 Docker Registry (192.168.0.4:5000)       │
│ 📦 MinIO (192.168.0.4:9000)                │
└─────────────────────────────────────────────┘
```

## 🏗️ Компоненты системы

### 🤖 Bot Layer

#### Primary Bot (aisha-bot-polling-1)
- **Назначение**: Основной бот для polling Telegram API
- **Режим**: `BOT_MODE=polling`, `SET_POLLING=true`
- **Функции**:
  - Обработка входящих сообщений
  - Управление пользовательскими сессиями
  - Транскрибация голосовых сообщений
- **Health Check**: Проверка Telegram API

#### Standby Bot (aisha-bot-polling-2)
- **Назначение**: Резервный бот для failover
- **Режим**: `BOT_MODE=polling_standby`, `SET_POLLING=false`
- **Функции**:
  - Режим ожидания
  - Автоматическое переключение при сбое primary
  - Синхронизация состояния
- **Health Check**: Готовность к переключению

#### Background Worker (aisha-worker-1)
- **Назначение**: Обработка фоновых задач
- **Режим**: `BOT_MODE=worker`
- **Функции**:
  - Обработка тяжелых вычислений
  - Генерация аватаров
  - Очередь задач через Redis
- **Health Check**: Проверка очереди Redis

### 🌐 API Layer

#### Webhook API
- **Порт**: 8001
- **Назначение**: Обработка webhook от внешних сервисов
- **Функции**:
  - FAL AI callbacks
  - MinIO events
  - Health checks
- **Framework**: FastAPI + uvicorn

#### Nginx Reverse Proxy
- **Порт**: 80, 443
- **Назначение**: Маршрутизация запросов
- **Функции**:
  - SSL termination
  - Static files serving
  - Load balancing
  - Rate limiting

### 🗄️ Data Layer

#### PostgreSQL (Внешний)
- **Host**: 192.168.0.4:5432
- **База**: aisha
- **Пользователь**: aisha_user
- **Назначение**: Основное хранилище данных
- **Схемы**:
  - Пользователи и сессии
  - Аватары и метаданные
  - История сообщений
  - Billing и транзакции

#### Redis (Внешний)
- **Host**: 192.168.0.3:6379
- **Назначение**: Кеширование и очереди
- **Использование**:
  - Session storage
  - Task queue (Celery)
  - Rate limiting
  - Temporary data

#### MinIO (Внешний)
- **Host**: 192.168.0.4:9000
- **Bucket**: aisha
- **Назначение**: Файловое хранилище
- **Содержимое**:
  - Загруженные фото пользователей
  - Сгенерированные аватары
  - Голосовые файлы
  - Временные файлы

### 🐳 Infrastructure Layer

#### Docker Registry
- **Host**: 192.168.0.4:5000
- **Тип**: HTTP Insecure Registry
- **Назначение**: Хранение Docker образов
- **Web UI**: 192.168.0.4:8080

#### Docker Networks
- **aisha_cluster**: Основная сеть для API компонентов
- **aisha_bot_cluster**: Сеть для bot компонентов (172.26.0.0/16)

## 🔄 Процессы и workflow

### 📱 Обработка сообщений

```mermaid
sequenceDiagram
    participant U as User
    participant T as Telegram
    participant B as Primary Bot
    participant R as Redis
    participant DB as PostgreSQL
    participant W as Worker
    
    U->>T: Отправка сообщения
    T->>B: Webhook/Polling
    B->>R: Проверка rate limit
    B->>DB: Загрузка пользователя
    B->>W: Добавление в очередь
    W->>DB: Обработка и сохранение
    W->>B: Результат
    B->>T: Ответ пользователю
    T->>U: Получение ответа
```

### 🎭 Создание аватара

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bot
    participant M as MinIO
    participant F as FAL AI
    participant W as Worker
    
    U->>B: Загрузка фото
    B->>M: Сохранение фото
    B->>W: Задача на обучение
    W->>F: Отправка на FAL AI
    F-->>W: Webhook callback
    W->>M: Сохранение результата
    W->>B: Уведомление
    B->>U: Аватар готов
```

### 🔊 Транскрибация аудио

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bot
    participant T as Temp Storage
    participant O as OpenAI
    
    U->>B: Голосовое сообщение
    B->>T: Сохранение в /app/storage/temp
    B->>O: Отправка на Whisper API
    O->>B: Результат транскрибации
    B->>T: Очистка временного файла
    B->>U: Текст + ответ AI
```

## 🔧 Конфигурация

### Переменные окружения

#### Обязательные
```bash
# Telegram
TELEGRAM_BOT_TOKEN=<bot_token>

# Database
DATABASE_URL=postgresql+asyncpg://aisha_user:pass@192.168.0.4:5432/aisha

# Redis
REDIS_URL=redis://:pass@192.168.0.3:6379/0

# OpenAI
OPENAI_API_KEY=<api_key>

# FAL AI
FAL_KEY=<fal_key>

# MinIO
MINIO_ENDPOINT=192.168.0.4:9000
MINIO_ACCESS_KEY=<access_key>
MINIO_SECRET_KEY=<secret_key>
MINIO_BUCKET_NAME=aisha
```

#### Опциональные
```bash
# Режимы работы бота
BOT_MODE=polling|polling_standby|worker
SET_POLLING=true|false

# Webhook
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8443

# Логирование
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR

# Окружение
ENVIRONMENT=production|development
```

## 🚀 Deployment

### Docker Compose файлы

#### `docker-compose.bot.registry.yml`
- **Назначение**: Bot кластер с registry образами
- **Сервисы**: bot-polling-1, bot-polling-2, worker
- **Сеть**: aisha_bot_cluster

#### `docker-compose.registry.yml`
- **Назначение**: Webhook API и Nginx
- **Сервисы**: webhook-api, nginx
- **Сеть**: aisha_cluster

### Процесс деплоя

1. **Сборка образов**: `docker build -f docker/Dockerfile.bot`
2. **Push в registry**: `docker push 192.168.0.4:5000/aisha/bot:tag`
3. **Деплой на продакшн**: `scripts/production/deploy-with-registry.sh`
4. **Health checks**: Автоматическая проверка статуса
5. **Rollback**: При необходимости откат к предыдущей версии

## 🔒 Безопасность

### Network Security
- Изоляция через Docker networks
- Firewall правила для внешних подключений
- Insecure registry только для внутренней сети

### Data Security
- Encrypted соединения с внешними API
- Secure storage секретов в .env
- Automatic cleanup временных файлов

### Application Security
- Rate limiting через Redis
- Input validation
- Error handling без раскрытия внутренней информации

## 📊 Мониторинг и логирование

### Health Checks
- **Bot containers**: Telegram API connectivity
- **Webhook API**: HTTP 200 response на /health
- **External services**: Network connectivity tests

### Логирование
- **Уровни**: INFO, DEBUG, WARNING, ERROR
- **Ротация**: Автоматическая через Docker
- **Хранение**: Local files + centralized logging

### Метрики
- Container health status
- Resource usage (CPU, Memory)
- API response times
- Error rates

## 🔄 Backup и Recovery

### Данные для бэкапа
- PostgreSQL database dumps
- MinIO bucket contents
- Docker registry images
- Configuration files (.env)

### Recovery процедуры
- Database restore from dumps
- Image rebuild from source
- Configuration restore
- Service restart procedures

## 📈 Масштабирование

### Горизонтальное
- Добавление worker экземпляров
- Multiple webhook API instances
- Load balancer configuration

### Вертикальное
- CPU/Memory limits увеличение
- Storage expansion
- Network bandwidth optimization

## 🔄 Последнее обновление

**Дата**: 2025-06-10  
**Версия**: v2.0  
**Статус**: ✅ Актуально  
**Автор**: AI Assistant