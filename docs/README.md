# 📚 Документация Aisha Bot v2

> **AI-Powered Telegram Bot с персональными аватарами и генерацией изображений**

## 🚀 Быстрая навигация

### 📖 Основные руководства
- **[🏠 Главная](../README.md)** - Обзор проекта и быстрый старт
- **[🏗️ Архитектура](architecture.md)** - Техническая архитектура системы
- **[🚀 Развертывание](DEPLOYMENT.md)** - Полное руководство по развертыванию
- **[📋 Best Practices](best_practices.md)** - Стандарты разработки

### 🔧 Для разработчиков
- **[🛠️ Настройка окружения](setup/)** - Локальная разработка
- **[🧪 Тестирование](development/)** - Тесты и отладка
- **[📊 API Reference](reference/)** - Справочник по API

### 🎯 Функциональность

#### 🎭 AI-Аватары
- **Создание персональных моделей** через FAL AI
- **Портретные и художественные стили** 
- **Автоматическое обучение** на пользовательских фото
- **Галерея аватаров** с управлением

#### 🖼️ Генерация изображений
- **Фото с аватаром** по текстовому описанию
- **Кинематографические промпты** с автоулучшением
- **Анализ изображений** через GPT-4 Vision
- **Качественные глаза** со специальными улучшениями

#### 🔊 Транскрибация аудио
- **OpenAI Whisper** для преобразования речи в текст
- **Smart chunking** для длинных аудиофайлов
- **Персональная галерея** результатов

#### 💰 Система балансов
- **Кредитная система** для оплаты AI-услуг
- **Гибкие тарифы** для разных операций
- **История транзакций** и управление

## 🏗️ Архитектура

```mermaid
graph TB
    subgraph "🤖 Bot Layer"
        TB[Telegram Bot]
        WH[Webhook Handler]
    end
    
    subgraph "🎯 Business Logic"
        AM[Avatar Manager]
        IG[Image Generator]
        AS[Audio Service]
        BS[Balance Service]
    end
    
    subgraph "💾 Data Layer"
        DB[(PostgreSQL)]
        RD[(Redis)]
        S3[(MinIO)]
    end
    
    subgraph "🌐 External APIs"
        FAL[FAL AI]
        OAI[OpenAI]
        GPT4V[GPT-4 Vision]
    end
    
    TB --> AM
    TB --> IG
    TB --> AS
    TB --> BS
    
    AM --> FAL
    IG --> FAL
    AS --> OAI
    IG --> GPT4V
    
    AM --> DB
    IG --> DB
    AS --> DB
    BS --> DB
    
    TB --> RD
    AM --> S3
    IG --> S3
```

## 🛠️ Технический стек

### Backend
- **Python 3.12** - Основной язык
- **aiogram 3.4.1** - Telegram Bot framework
- **FastAPI** - REST API для webhook
- **SQLAlchemy 2.0** - Async ORM
- **Alembic** - Миграции БД

### AI & ML
- **FAL AI** - Обучение аватаров и генерация
- **OpenAI GPT-4 Vision** - Анализ изображений
- **OpenAI Whisper** - Транскрибация аудио

### Infrastructure
- **PostgreSQL** - Основная БД
- **Redis** - Кеш и очереди
- **MinIO** - Файловое хранилище
- **Docker** - Контейнеризация

## 🚀 Быстрый старт

### 1. Клонирование и настройка
```bash
git clone <repo-url>
cd aisha-backend
cp .env.example .env
# Отредактируйте .env с вашими API ключами
```

### 2. Запуск для разработки
```bash
# Рекомендуемый способ
./scripts/run_dev_bot.sh

# Или через Docker
docker-compose -f docker-compose.bot.dev.yml up -d --build
```

### 3. Проверка работы
```bash
# Логи бота
docker-compose -f docker-compose.bot.dev.yml logs -f aisha-bot-dev

# Health check
python scripts/testing/test_app_health.py
```

## ⚙️ Конфигурация

### Основные переменные
```bash
# Telegram
TELEGRAM_TOKEN=ваш_токен_бота

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@192.168.0.4:5432/aisha

# AI Services
FAL_API_KEY=ваш_ключ_fal_ai
OPENAI_API_KEY=ваш_ключ_openai

# Storage
MINIO_ENDPOINT=192.168.0.4:9000
REDIS_URL=redis://:pass@192.168.0.3:6379/0

# Costs (в кредитах)
AVATAR_CREATION_COST=150.0
IMAGE_GENERATION_COST=5.0
TRANSCRIPTION_COST_PER_MINUTE=10.0
```

## 📊 Мониторинг

### Health Checks
- ✅ Telegram API подключение
- ✅ PostgreSQL доступность
- ✅ Redis состояние
- ✅ MinIO подключение
- ✅ FAL AI валидность ключа

### Полезные команды
```bash
# Проверка аватаров
python scripts/testing/check_avatars.py

# Проверка системы
python scripts/testing/test_app_health.py

# Запуск обучения
python scripts/testing/start_ready_training.py
```

## 🔧 Разработка

### Структура проекта
```
aisha-backend/
├── app/                    # Основной код
│   ├── handlers/          # Telegram обработчики
│   ├── services/          # Бизнес-логика
│   ├── database/          # Модели и миграции
│   └── core/              # Конфигурация
├── scripts/               # Утилиты
├── docs/                  # Документация
└── docker/                # Docker конфигурации
```

### Команды разработки
```bash
# Запуск DEV бота
./scripts/run_dev_bot.sh

# Миграции
alembic upgrade head
alembic revision --autogenerate -m "описание"

# Тестирование
pytest tests/
python -m pytest tests/test_avatar_system.py -v
```

## 💳 Тарификация

### Стоимость услуг
- **Создание аватара**: 150 кредитов
- **Генерация изображения**: 5 кредитов  
- **Транскрибация**: 10 кредитов/минута

### Пакеты пополнения
- **Малый**: 250 кредитов - 490₽ / 2500₸
- **Средний**: 500 кредитов - 870₽ / 4900₸ ⭐
- **Большой**: 1000 кредитов - 1540₽ / 8800₸

## 🔒 Безопасность

- **Переменные окружения** для всех секретов
- **Валидация данных** на всех уровнях
- **NSFW фильтрация** изображений
- **Rate limiting** через Redis
- **Автоочистка** временных файлов

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
- Расширенная аналитика

### 📋 Планируется
- Интеграция платежных систем
- API для внешних разработчиков
- Мобильное приложение

## 🆘 Поддержка

### Частые проблемы
- **Конфликт токенов**: Используйте `./scripts/run_dev_bot.sh`
- **Ошибки обучения**: Проверьте FAL_API_KEY и webhook URL
- **Проблемы с БД**: Убедитесь в доступности PostgreSQL

### Получение помощи
1. Проверьте логи: `docker-compose logs -f`
2. Запустите health check: `python scripts/testing/test_app_health.py`
3. Изучите документацию в соответствующих разделах

## 📚 Дополнительные ресурсы

- **[Troubleshooting](reference/troubleshooting.md)** - Решение проблем
- **[Performance](development/PERFORMANCE.md)** - Оптимизация производительности
- **[FAL AI Knowledge Base](reference/fal_knowlege_base/)** - Документация по FAL AI

---

**Документация актуализирована:** Июнь 2025 | **Версия:** 2.0  
**Создано с ❤️ командой Aisha Bot** 