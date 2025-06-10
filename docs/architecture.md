# 🏗️ Архитектура Aisha Bot v2

## 📋 Общий обзор

Aisha Bot v2 - это современный Telegram-бот для транскрибации аудио с использованием OpenAI Whisper API и системой платных услуг.

## 🎯 Текущая функциональность

### ✅ Реализовано
- 🔊 **Транскрибация аудио** - Преобразование голосовых сообщений в текст через OpenAI Whisper
- 💰 **Платная система** - Система балансов и оплата за транскрибацию
- 📝 **Сохранение транскриптов** - Хранение результатов в MinIO и PostgreSQL
- ⚡ **Асинхронная обработка** - Быстрая обработка через aiogram 3.x
- 🔄 **Smart chunking** - Умное разбиение длинных аудио на части

### 🎭 Планируется (AI-аватары)
- Создание персональных аватаров
- Генерация изображений по описанию
- Интеграция с FAL AI

## 🏗️ Компоненты системы

### 🤖 Bot Layer

#### Main Bot Service (aisha-bot-dev)
- **Режим**: Polling для разработки
- **Функции**:
  - Обработка входящих сообщений
  - Транскрибация аудио через OpenAI Whisper
  - Управление пользовательскими балансами
  - Система платных услуг
- **Endpoint**: Telegram Bot API
- **Health Check**: Проверка Telegram connection

#### Worker Service (aisha-worker-dev)
- **Режим**: Background worker (в разработке)
- **Функции**:
  - Обработка тяжелых задач
  - Очередь заданий через Redis
  - Параллельная обработка

### 🌐 API Layer

#### FastAPI Webhook Service
- **Порт**: 8000 (в планах)
- **Назначение**: Обработка webhook от внешних сервисов
- **Функции**:
  - OpenAI API callbacks
  - Health checks
  - API endpoints

### 🗄️ Data Layer

#### PostgreSQL
- **Host**: 192.168.0.4:5432
- **База**: aisha
- **Схемы**:
  - **users** - Пользователи и их данные
  - **user_balances** - Система балансов
  - **transactions** - История платежей
  - **transcripts** - Сохраненные транскрипты
  - **audio_files** - Метаданные аудиофайлов

#### Redis
- **Host**: 192.168.0.3:6379
- **Использование**:
  - Кеширование пользовательских сессий
  - Rate limiting
  - Task queue для воркеров
  - Временные данные

#### MinIO
- **Host**: 192.168.0.4:9000
- **Bucket**: aisha
- **Структура**:
  ```
  aisha/
  ├── {user_id}/
  │   ├── {transcript_id}/
  │   │   ├── audio.mp3      # Исходный аудиофайл
  │   │   └── transcript.txt # Результат транскрипции
  │   └── temp/              # Временные файлы
  ```

## 🔄 Основные процессы

### 🔊 Транскрибация аудио

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bot
    participant AS as AudioService
    participant WR as WhisperRecognizer
    participant O as OpenAI API
    participant M as MinIO
    participant DB as PostgreSQL
    
    U->>B: Голосовое сообщение
    B->>AS: process_audio(audio_data)
    AS->>AS: Конвертация в MP3 (ffmpeg)
    AS->>AS: Разбиение на чанки (60 сек)
    
    loop Каждый чанк
        AS->>WR: transcribe_chunk(chunk)
        WR->>O: POST /audio/transcriptions
        O->>WR: Результат транскрипции
        WR->>AS: TranscribeResult
    end
    
    AS->>AS: Склеивание результатов
    AS->>M: Сохранение аудио и транскрипта
    AS->>DB: Сохранение метаданных
    AS->>B: Итоговый результат
    B->>U: Транскрибированный текст
```

### 💰 Система оплаты

```mermaid
sequenceDiagram
    participant U as User
    participant B as Bot
    participant TS as TranscriptionService
    participant BS as BalanceService
    participant DB as PostgreSQL
    
    U->>B: Длинное аудио (>3 мин)
    B->>TS: check_balance_and_estimate()
    TS->>BS: get_balance(user_id)
    BS->>DB: SELECT balance FROM user_balances
    TS->>TS: Расчет стоимости (цена за минуту)
    
    alt Достаточно средств
        TS->>BS: charge_balance(amount)
        BS->>DB: UPDATE user_balances SET balance = balance - amount
        TS->>B: Начало транскрибации
    else Недостаточно средств
        TS->>B: Ошибка недостатка средств
        B->>U: Предложение пополнить баланс
    end
```

### 📁 Управление файлами

```mermaid
graph TB
    A[Входящее аудио] --> B[Временное сохранение /app/storage/temp]
    B --> C[ffmpeg конвертация в MP3]
    C --> D[Разбиение на чанки]
    D --> E[Транскрибация через OpenAI]
    E --> F[Склеивание результатов]
    F --> G[Сохранение в MinIO]
    G --> H[Запись метаданных в DB]
    H --> I[Очистка временных файлов]
```

## 🛠️ Технический стек

### Backend
- **Python 3.12** - Основной язык
- **aiogram 3.4.1** - Telegram Bot API
- **aiohttp 3.9.5** - HTTP клиент (зафиксированная версия для совместимости)
- **SQLAlchemy 2.0** - ORM (async)
- **Alembic** - Миграции БД

### Audio Processing
- **ffmpeg** - Конвертация и обработка аудио
- **OpenAI Whisper API** - Транскрибация речи
- **pydub** - Python библиотека для аудио (вспомогательная)

### Infrastructure
- **PostgreSQL** - Основная БД
- **Redis** - Кеширование и очереди
- **MinIO** - Файловое хранилище S3-совместимое
- **Docker** - Контейнеризация

## 🔧 Конфигурация

### Основные переменные окружения

```bash
# ==================== TELEGRAM BOT ====================
TELEGRAM_BOT_TOKEN=ваш_токен_бота

# ==================== DATABASE ====================
DATABASE_URL=postgresql://aisha_user:пароль@192.168.0.4:5432/aisha

# ==================== REDIS ====================
REDIS_URL=redis://:пароль@192.168.0.3:6379/0

# ==================== OPENAI ====================
OPENAI_API_KEY=ваш_ключ_openai

# ==================== MINIO ====================
MINIO_ENDPOINT=192.168.0.4:9000
MINIO_ACCESS_KEY=ваш_access_key
MINIO_SECRET_KEY=ваш_secret_key
MINIO_BUCKET=aisha

# ==================== PRICING ====================
TRANSCRIPTION_COST_PER_MINUTE=15.0  # монет за минуту
FREE_MINUTES_PER_DAY=3.0             # бесплатные минуты в день
```

### Docker Compose Services

```yaml
services:
  aisha-bot-dev:
    build:
      dockerfile: Dockerfile.bot
    environment:
      - BOT_MODE=polling
      - SET_POLLING=true
      - INSTANCE_ID=bot-dev
    volumes:
      - ./storage:/app/storage
    
  aisha-worker-dev:
    build:
      dockerfile: Dockerfile.bot
    environment:
      - BOT_MODE=worker
      - SET_POLLING=false
      - INSTANCE_ID=worker-dev
```

## 📊 Структура данных

### Таблицы БД

```sql
-- Пользователи
CREATE TABLE users (
    id UUID PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Балансы пользователей
CREATE TABLE user_balances (
    user_id UUID REFERENCES users(id),
    balance DECIMAL(10,2) DEFAULT 100.00,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Транскрипты
CREATE TABLE transcripts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    audio_key VARCHAR(500),      -- Путь в MinIO
    transcript_key VARCHAR(500), -- Путь к транскрипту в MinIO
    transcript_metadata JSONB,   -- Метаданные (длительность, стоимость)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Транзакции
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    amount DECIMAL(10,2),
    transaction_type VARCHAR(50), -- 'charge', 'refund', 'bonus'
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🚀 Развертывание

### Development
```bash
# Настройка окружения
cp env.docker.template .env
# Отредактируйте .env

# Запуск в разработке
docker-compose -f docker-compose.bot.dev.yml up -d --build

# Проверка логов
docker-compose -f docker-compose.bot.dev.yml logs -f aisha-bot-dev
```

### Production (планируется)
```bash
# Продакшн развертывание
docker-compose -f docker-compose.prod.yml up -d
```

## 🔍 Мониторинг

### Health Checks
- **Bot**: Проверка connection к Telegram API
- **Database**: Проверка подключения к PostgreSQL
- **Redis**: Проверка доступности кеша
- **MinIO**: Проверка файлового хранилища

### Логирование
- **Структурированные логи** с уровнями INFO/WARNING/ERROR
- **Детальное логирование** процесса транскрибации
- **Логи ошибок** с stack trace
- **Ротация логов** в продакшене

### Метрики (планируется)
- Количество транскрибаций в день
- Средняя длительность обработки
- Использование баланса пользователями
- Ошибки API

## 🛡️ Безопасность

### API Keys
- Все ключи через переменные окружения
- Никаких секретов в коде
- Rotatable tokens

### Rate Limiting
- Ограничение запросов на пользователя
- Защита от спама
- Graceful degradation

### Data Privacy
- Автоматическая очистка временных файлов
- Шифрование в MinIO
- GDPR compliance (планируется)

## 🔄 Планы развития

### Ближайшие задачи
1. ✅ Стабилизация транскрибации
2. 🔄 Оптимизация обработки длинных аудио
3. 📊 Добавление метрик и мониторинга
4. 💳 Интеграция платежных систем

### Долгосрочные планы
1. 🎭 Возврат к AI-аватарам (FAL AI)
2. 🖼️ Генерация изображений
3. 📱 Web интерфейс
4. 🌍 Мультиязычность

---

**Последнее обновление:** Декабрь 2024  
**Статус:** ✅ Активная разработка