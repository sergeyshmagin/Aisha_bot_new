# 🤖 Aisha Bot v2 - AI-Powered Telegram Bot

> **Современный Telegram-бот с AI-аватарами и генерацией изображений**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.4.1-green.svg)](https://github.com/aiogram/aiogram)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![FAL AI](https://img.shields.io/badge/FAL_AI-Integrated-purple.svg)](https://fal.ai)

## ✨ Основные возможности

### 🎭 AI-Аватары
- **Создание персональных аватаров** - Обучение на ваших фотографиях через FAL AI
- **Портретные и художественные стили** - Два типа обучения моделей
- **Автоматическое обучение** - Загрузка 10-20 фото → готовый аватар
- **Галерея аватаров** - Управление созданными моделями

### 🖼️ Генерация изображений
- **Фото с аватаром** - Создание изображений с вашим лицом
- **Кинематографические промпты** - Автоматическое улучшение описаний
- **Анализ изображений** - GPT-4 Vision для создания промптов по фото
- **Качественные глаза** - Специальные улучшения для реалистичности

### 🔊 Транскрибация аудио
- **OpenAI Whisper** - Преобразование голосовых сообщений в текст
- **Smart chunking** - Умное разбиение длинных аудио
- **Сохранение результатов** - Персональная галерея транскриптов

### 💰 Система балансов
- **Кредитная система** - Оплата за AI-услуги
- **Гибкие тарифы** - Разные цены для разных функций
- **История операций** - Отслеживание трат

## 🚀 Быстрый старт

### Предварительные требования

- **Docker** и Docker Compose
- **Внешние сервисы:**
  - PostgreSQL (192.168.0.4:5432)
  - Redis (192.168.0.3:6379) 
  - MinIO (192.168.0.4:9000)
- **API ключи:**
  - Telegram Bot Token
  - OpenAI API Key
  - FAL AI API Key

### Установка

1. **Клонирование и настройка**
```bash
git clone <repo-url>
cd aisha-backend
cp .env.example .env
# Отредактируйте .env с вашими ключами
```

2. **Запуск для разработки**
```bash
# Используйте готовый скрипт
./scripts/run_dev_bot.sh

# Или вручную
docker-compose -f docker-compose.bot.dev.yml up -d --build
```

3. **Проверка статуса**
```bash
docker-compose -f docker-compose.bot.dev.yml logs -f aisha-bot-dev
```

## ⚙️ Конфигурация

### Основные переменные окружения

```bash
# Telegram Bot
TELEGRAM_TOKEN=ваш_токен_бота

# Database
DATABASE_URL=postgresql+asyncpg://aisha_user:пароль@192.168.0.4:5432/aisha

# Redis
REDIS_URL=redis://:пароль@192.168.0.3:6379/0

# OpenAI
OPENAI_API_KEY=ваш_ключ_openai

# FAL AI для аватаров
FAL_API_KEY=ваш_ключ_fal_ai
FAL_WEBHOOK_URL=https://ваш_домен:8443/api/v1/avatar/status_update

# MinIO файловое хранилище
MINIO_ENDPOINT=192.168.0.4:9000
MINIO_ACCESS_KEY=ваш_access_key
MINIO_SECRET_KEY=ваш_secret_key

# Настройки обучения аватаров
FAL_PORTRAIT_STEPS=1000
FAL_DEFAULT_QUALITY_PRESET=fast

# Стоимость услуг (в кредитах)
AVATAR_CREATION_COST=150.0
IMAGE_GENERATION_COST=5.0
TRANSCRIPTION_COST_PER_MINUTE=10.0
```

## 🏗️ Архитектура

```mermaid
graph TB
    U[👤 Пользователь] --> TB[🤖 Telegram Bot]
    
    TB --> AM[🎭 Avatar Manager]
    AM --> FAL[🎨 FAL AI Service]
    FAL --> FS[📁 File Storage]
    
    TB --> IG[🖼️ Image Generator]
    IG --> PE[✨ Prompt Enhancer]
    IG --> IA[👁️ Image Analyzer]
    
    TB --> AS[🔊 Audio Service]
    AS --> WR[🗣️ Whisper API]
    
    TB --> BS[💰 Balance Service]
    
    BS --> DB[(🗄️ PostgreSQL)]
    AM --> DB
    IG --> DB
    AS --> DB
    
    FS --> S3[(📦 MinIO)]
    TB --> R[(🔴 Redis)]
```

### Основные компоненты

- **🤖 Telegram Bot** - Обработка пользовательских команд (aiogram 3.x)
- **🎭 Avatar Manager** - Создание и управление AI-аватарами
- **🎨 FAL AI Service** - Интеграция с FAL AI для обучения моделей
- **🖼️ Image Generator** - Генерация изображений с аватарами
- **✨ Prompt Enhancer** - Улучшение промптов для лучших результатов
- **👁️ Image Analyzer** - Анализ изображений через GPT-4 Vision
- **🔊 Audio Service** - Обработка аудио с ffmpeg
- **🗣️ Whisper API** - Транскрибация через OpenAI
- **💰 Balance Service** - Управление кредитами пользователей
- **🗄️ PostgreSQL** - Основная база данных
- **🔴 Redis** - Кеширование и очереди
- **📦 MinIO** - S3-совместимое файловое хранилище

## 💳 Система тарификации

### Стоимость услуг
- **Создание аватара**: 150 кредитов
- **Генерация изображения**: 5 кредитов
- **Транскрибация**: 10 кредитов/минута
- **Видео (планируется)**: 20-60 кредитов

### Пакеты пополнения
- **Малый**: 250 кредитов - 490₽ / 2500₸
- **Средний**: 500 кредитов - 870₽ / 4900₸ ⭐
- **Большой**: 1000 кредитов - 1540₽ / 8800₸

## 🔧 Разработка

### Структура проекта

```
aisha-backend/
├── app/                           # Основной код
│   ├── handlers/                  # Обработчики команд
│   │   ├── avatar/               # Система аватаров
│   │   ├── generation/           # Генерация изображений
│   │   └── transcript_processing/ # Транскрибация
│   ├── services/                  # Бизнес-логика
│   │   ├── avatar/               # Управление аватарами
│   │   ├── generation/           # Генерация контента
│   │   ├── fal/                  # Интеграция FAL AI
│   │   └── audio_processing/     # Обработка аудио
│   ├── database/                  # Модели и миграции
│   └── core/                      # Конфигурация
├── scripts/                       # Утилиты и скрипты
│   ├── run_dev_bot.sh            # Запуск DEV бота
│   └── deployment/               # Скрипты деплоя
├── docs/                          # Документация
└── docker/                        # Docker конфигурации
```

### Команды разработки

```bash
# Запуск DEV бота (рекомендуется)
./scripts/run_dev_bot.sh

# Docker команды
docker-compose -f docker-compose.bot.dev.yml up -d --build
docker-compose -f docker-compose.bot.dev.yml logs -f aisha-bot-dev
docker-compose -f docker-compose.bot.dev.yml down

# Миграции БД
alembic upgrade head
alembic revision --autogenerate -m "описание_изменений"

# Тестирование
pytest tests/
python -m pytest tests/test_avatar_system.py -v
```

## 📊 Мониторинг и отладка

### Health Checks
- ✅ Подключение к Telegram API
- ✅ Доступность PostgreSQL
- ✅ Состояние Redis
- ✅ Подключение к MinIO
- ✅ Валидность FAL AI ключа

### Полезные скрипты
```bash
# Проверка аватаров
python scripts/testing/check_avatars.py

# Проверка здоровья приложения
python scripts/testing/test_app_health.py

# Запуск готовых к обучению аватаров
python scripts/testing/start_ready_training.py
```

### Логирование
- **Структурированные логи** с уровнями DEBUG/INFO/ERROR
- **Детальное логирование** процессов обучения и генерации
- **Автоматическое логирование** ошибок с трассировкой

## 🔒 Безопасность

- **Переменные окружения** для всех секретов
- **Автоматическая очистка** временных файлов
- **Rate limiting** через Redis
- **Валидация входных данных** на всех уровнях
- **Безопасные webhook** с проверкой подписи

## 🚀 Развертывание

### Development
```bash
./scripts/run_dev_bot.sh
```

### Production
```bash
# Webhook режим на продакшн сервере
docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env up -d
```

Подробнее: [Руководство по развертыванию](docs/DEPLOYMENT.md)

## 📋 Планы развития

### ✅ Реализовано
- Система AI-аватаров с FAL AI
- Генерация изображений с промпт-инжинирингом
- Анализ изображений через GPT-4 Vision
- Транскрибация аудио через OpenAI Whisper
- Система балансов и тарификация

### 🔄 В разработке
- Генерация видео с аватарами
- Web-интерфейс для управления
- Расширенная аналитика использования

### 📋 Планируется
- Интеграция платежных систем
- API для внешних разработчиков
- Мобильное приложение

## 📚 Документация

- **[Архитектура](docs/architecture.md)** - Техническая архитектура
- **[Развертывание](docs/DEPLOYMENT.md)** - Руководство по развертыванию
- **[Best Practices](docs/best_practices.md)** - Стандарты разработки
- **[API Reference](docs/reference/)** - Справочник по API

## 🆘 Поддержка

### Частые проблемы
- **Конфликт токенов**: Используйте `./scripts/run_dev_bot.sh`
- **Ошибки обучения**: Проверьте FAL_API_KEY и webhook URL
- **Проблемы с БД**: Убедитесь в доступности PostgreSQL

### Получение помощи
1. Проверьте логи: `docker-compose logs -f`
2. Изучите документацию в `docs/`
3. Запустите health check: `python scripts/testing/test_app_health.py`

---

**Создано с ❤️ командой Aisha Bot** | **Статус:** ✅ Активная разработка 