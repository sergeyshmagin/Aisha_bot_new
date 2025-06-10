# 🤖 Aisha Bot v2 - Транскрибация аудио

> **Современный Telegram-бот для транскрибации голосовых сообщений**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.4.1-green.svg)](https://github.com/aiogram/aiogram)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

## ✨ Возможности

- 🔊 **Транскрибация аудио** - Преобразование голосовых сообщений в текст через OpenAI Whisper
- 💰 **Платная система** - Система балансов для оплаты транскрибации
- 📝 **Сохранение результатов** - Все транскрипты сохраняются в персональной галерее
- ⚡ **Быстрая обработка** - Асинхронная обработка с умным разбиением длинных аудио
- 🔄 **Smart chunking** - Автоматическое разбиение аудио на оптимальные части

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- PostgreSQL (192.168.0.4:5432)
- Redis (192.168.0.3:6379)
- MinIO (192.168.0.4:9000)
- OpenAI API ключ

### Установка

1. **Клонирование репозитория**
```bash
git clone <repo-url>
cd aisha-backend
```

2. **Настройка окружения**
```bash
cp env.docker.template .env
# Отредактируйте .env файл с вашими ключами
```

3. **Запуск в development режиме**
```bash
docker-compose -f docker-compose.bot.dev.yml up -d --build
```

4. **Проверка статуса**
```bash
docker-compose -f docker-compose.bot.dev.yml ps
docker-compose -f docker-compose.bot.dev.yml logs -f aisha-bot-dev
```

## ⚙️ Конфигурация

### Основные переменные окружения

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=ваш_токен_бота

# Database
DATABASE_URL=postgresql://aisha_user:пароль@192.168.0.4:5432/aisha

# Redis
REDIS_URL=redis://:пароль@192.168.0.3:6379/0

# OpenAI для транскрибации
OPENAI_API_KEY=ваш_ключ_openai

# MinIO файловое хранилище
MINIO_ENDPOINT=192.168.0.4:9000
MINIO_ACCESS_KEY=ваш_access_key
MINIO_SECRET_KEY=ваш_secret_key

# Настройки цен
TRANSCRIPTION_COST_PER_MINUTE=15.0
FREE_MINUTES_PER_DAY=3.0
```

## 🏗️ Архитектура

```mermaid
graph TB
    U[👤 Пользователь] --> TB[🤖 Telegram Bot]
    TB --> AS[🎵 AudioService]
    AS --> FF[📽️ FFmpeg]
    AS --> WR[🗣️ WhisperRecognizer]
    WR --> OAI[🤖 OpenAI API]
    
    TB --> BS[💰 BalanceService]
    TB --> TS[📝 TranscriptService]
    
    BS --> DB[(🗄️ PostgreSQL)]
    TS --> DB
    TS --> S3[(📦 MinIO)]
    
    TB --> R[(🔴 Redis)]
```

### Основные компоненты

- **🤖 Telegram Bot** - Обработка пользовательских сообщений (aiogram 3.x)
- **🎵 AudioService** - Обработка аудио файлов с ffmpeg
- **🗣️ WhisperRecognizer** - Транскрибация через OpenAI Whisper API
- **💰 BalanceService** - Управление балансами пользователей
- **📝 TranscriptService** - Сохранение результатов в MinIO и БД
- **🗄️ PostgreSQL** - Основная база данных
- **🔴 Redis** - Кеширование и очереди задач
- **📦 MinIO** - S3-совместимое файловое хранилище

## 💳 Система оплаты

### Тарифы
- **Бесплатно**: 3 минуты в день
- **Платно**: 15 монет за минуту транскрибации

### Процесс оплаты
1. Пользователь отправляет длинное аудио (>3 мин)
2. Система рассчитывает стоимость
3. Проверка баланса
4. Списание средств при достаточном балансе
5. Транскрибация или предложение пополнить баланс

## 🔧 Разработка

### Структура проекта

```
aisha-backend/
├── app/                        # Основной код приложения
│   ├── handlers/              # Обработчики команд бота
│   ├── services/              # Бизнес-логика
│   │   ├── audio_processing/  # Обработка аудио
│   │   ├── balance/          # Система балансов
│   │   └── transcript/       # Управление транскриптами
│   ├── models/               # SQLAlchemy модели
│   ├── repositories/         # Слой доступа к данным
│   └── core/                 # Конфигурация и утилиты
├── alembic/                   # Миграции БД
├── docs/                      # Документация
├── scripts/                   # Скрипты для развертывания
└── docker/                    # Docker конфигурации
```

### Команды разработки

```bash
# Запуск в dev режиме
docker-compose -f docker-compose.bot.dev.yml up -d

# Перестройка контейнеров
docker-compose -f docker-compose.bot.dev.yml up -d --build

# Просмотр логов
docker-compose -f docker-compose.bot.dev.yml logs -f aisha-bot-dev

# Остановка
docker-compose -f docker-compose.bot.dev.yml down

# Запуск миграций
docker-compose -f docker-compose.bot.dev.yml exec aisha-bot-dev alembic upgrade head
```

## 📊 Мониторинг

### Health Checks
- Проверка подключения к Telegram API
- Проверка доступности PostgreSQL
- Проверка состояния Redis
- Проверка MinIO storage

### Логирование
- Структурированные логи с уровнями
- Детальное логирование процесса транскрибации
- Автоматическое логирование ошибок

### Метрики (планируется)
- Количество транскрибаций
- Использование баланса
- Производительность API

## 🔒 Безопасность

- Все API ключи через переменные окружения
- Автоматическая очистка временных файлов
- Rate limiting через Redis
- Валидация входных данных

## 📋 Планы развития

### Ближайшие цели
1. ✅ Стабилизация транскрибации
2. 🔄 Оптимизация длинных аудио
3. 📊 Система метрик
4. 💳 Интеграция платежей

### Долгосрочные планы
1. 🎭 AI-аватары (FAL AI)
2. 🖼️ Генерация изображений
3. 📱 Web интерфейс
4. 🌍 Мультиязычность

## 📚 Документация

- **[Архитектура](docs/architecture.md)** - Техническая архитектура системы
- **[Deployment](docs/DEPLOYMENT.md)** - Руководство по развертыванию
- **[Best Practices](docs/best_practices.md)** - Стандарты разработки
- **[Planning](docs/PLANNING.md)** - Планы развития

## 🆘 Поддержка

### Частые проблемы
- **Контейнер перезапускается**: Проверьте корректность токенов в .env
- **Транскрибация зависает**: Проверьте OpenAI API ключ и лимиты
- **Ошибки БД**: Убедитесь в доступности PostgreSQL

### Получение помощи
- Проверьте логи: `docker-compose logs`
- Изучите документацию в папке `docs/`
- Создайте issue с описанием проблемы

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Следуйте стандартам в `docs/best_practices.md`
4. Создайте Pull Request

## 📄 Лицензия

Проект разрабатывается для внутреннего использования.

---

**Создано с ❤️ командой Aisha Bot** | **Последнее обновление:** Декабрь 2024 