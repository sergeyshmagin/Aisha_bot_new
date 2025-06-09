# 🤖 Aisha Bot v2

Современный Telegram-бот для транскрибации аудио, обработки текста и создания AI аватаров с использованием продвинутых ML технологий.

## ✨ Возможности

- 🎤 **Транскрибация аудио** - преобразование голосовых сообщений и аудиофайлов в текст
  - ✅ **Бесплатная транскрипция** - аудио до 1 минуты  
  - 💰 **Платная транскрипция** - аудио свыше 1 минуты (10 монет/минута)
  - 🎁 **Система промо-кодов** - пополнение баланса и скидки
- 🎨 **AI Аватары** - создание персонализированных аватаров через FAL AI
  - 🖼️ **Портретные аватары** - на основе ваших фотографий
  - 🎭 **Стилизация** - художественные стили и направления
  - 🚀 **LoRA и DreamBooth** обучение
- 📝 **Обработка текста** - работа с текстовыми файлами
- 🤖 **AI форматирование** - создание кратких содержаний через OpenAI
- 🖼️ **Галерея** - управление созданными изображениями
- 📜 **История** - сохранение и управление всеми материалами

## 🏗️ Архитектура

### Технологический стек
- **Backend**: Python 3.12, aiogram 3.x, FastAPI
- **База данных**: PostgreSQL (async SQLAlchemy)
- **Кэширование**: Redis
- **Хранилище файлов**: MinIO
- **AI/ML**: OpenAI API, FAL AI
- **🐳 Контейнеризация**: Docker + Docker Compose
- **🔄 Оркестрация**: Docker Swarm ready

### 🎯 Продакшн кластер (масштабируемая архитектура)

```
📡 Load Balancer (Nginx)
     ├── 🌐 Webhook API Cluster
     │   ├── aisha-webhook-api-1  (FAL AI webhooks)
     │   └── aisha-webhook-api-2  (Load balanced)
     │
     └── 🤖 Bot Cluster
         ├── aisha-bot-polling-1   (Active - получает сообщения)
         ├── aisha-bot-polling-2   (Standby - failover)
         └── aisha-worker-1        (Background processing)
```

**Преимущества архитектуры:**
- ✅ **Failover**: автоматическое переключение при падении
- ✅ **Load balancing**: распределение нагрузки webhook API
- ✅ **Horizontal scaling**: масштабирование worker'ов
- ✅ **Health monitoring**: контроль состояния сервисов

### Структура проекта
```
aisha-backend/
├── app/                    # Основное приложение
│   ├── core/              # Ядро (DI, настройки, исключения)
│   ├── handlers/          # Telegram обработчики (модульная структура)
│   ├── services/          # Бизнес-логика
│   ├── database/          # Модели и репозитории
│   └── workers/           # Background workers
├── docker/                # Docker конфигурации
│   ├── Dockerfile.bot     # Bot контейнер
│   ├── Dockerfile.webhook # Webhook API контейнер
│   └── nginx/            # Nginx конфигурация
├── scripts/              # Скрипты управления
│   ├── production/       # Продакшн деплой
│   ├── monitoring/       # Мониторинг
│   └── utils/           # Утилиты
└── docs/                # Документация
```

## 🚀 Развертывание

### 📋 Продакшн деплой (финальная версия)

**1. Быстрый деплой на продакшн сервер:**
```bash
# Установите токен бота
export TELEGRAM_BOT_TOKEN=your_bot_token_here

# Запустите финальный скрипт деплоя
./scripts/production/deploy-production-final.sh
```

Скрипт автоматически:
- ✅ Проверит валидность Telegram токена  
- 🔨 Соберет исправленные Docker образы
- 📤 Отправит на продакшн регистр
- 🚀 Развернет кластер с правильными переменными
- 🏥 Проверит здоровье всех сервисов

**2. Мониторинг продакшн системы:**
```bash
# Полная проверка
./scripts/monitoring/monitor-production.sh

# Быстрая проверка
./scripts/monitoring/monitor-production.sh quick

# Только логи
./scripts/monitoring/monitor-production.sh logs
```

### 🛠️ Разработка

**Требования:**
- Python 3.12+
- PostgreSQL 15+
- Redis 7+
- MinIO
- Docker & Docker Compose

**Локальная разработка:**
```bash
# 1. Клонирование
git clone <repository-url>
cd aisha-backend

# 2. Виртуальное окружение
python -m venv .venv
source .venv/bin/activate

# 3. Зависимости
pip install -r requirements.txt

# 4. Настройки
cp env.example .env
# Отредактируйте .env

# 5. Миграции
alembic upgrade head

# 6. Запуск
python main.py
```

## ⚙️ Конфигурация

### Обязательные переменные окружения

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# База данных  
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=aisha_db
POSTGRES_USER=aisha
POSTGRES_PASSWORD=your_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# AI APIs
OPENAI_API_KEY=sk-your_openai_key
FAL_API_KEY=your_fal_key

# Продакшн
INSTANCE_ID=polling-1  # Уникальный ID экземпляра
BOT_MODE=polling       # polling, polling_standby, worker, webhook
```

## 📖 Использование

### Основные функции
- `/start` - Главное меню
- 🎤 **Транскрибация** - аудио в текст
- 🎨 **Аватары** - создание AI аватаров  
- 🖼️ **Галерея** - управление изображениями
- 👤 **Профиль** - баланс и настройки

### Навигация по меню
```
🏠 Главное меню
├── 🎤 Транскрибация
│   ├── 🎤 Аудио (< 1 мин - бесплатно, > 1 мин - платно)
│   ├── 📝 Текст (.txt файлы)
│   └── 📜 История транскриптов
├── 🎨 Аватары  
│   ├── ➕ Создать новый
│   ├── 📋 Мои аватары
│   └── 🎓 Обучение моделей
├── 🖼️ Галерея
│   ├── 🖼️ Мои изображения
│   └── 🔍 Фильтры
└── 👤 Профиль
    ├── 💰 Баланс монет
    ├── 🎁 Промо-коды
    └── ⚙️ Настройки
```

## 🔧 Администрирование

### Создание промо-кодов
```bash
# Создать промо-код на 100 монет
python scripts/utils/create_promo_code.py --coins 100 --code PROMO100

# Создать промо-код со скидкой 50%
python scripts/utils/create_promo_code.py --discount 50 --code DISCOUNT50
```

### Мониторинг и логи
```bash
# Проверить статус кластера
./scripts/monitoring/monitor-production.sh summary

# Посмотреть логи бота
ssh aisha@192.168.0.10 "docker logs aisha-bot-polling-1 --tail 50"

# Проверить использование ресурсов
./scripts/monitoring/monitor-production.sh system
```

## 🐛 Решение проблем

### Известные проблемы и решения

1. **"Token is invalid!"**
   - ✅ **Решено**: Добавлена переменная `TELEGRAM_TOKEN` в docker-compose
   - Убедитесь что `TELEGRAM_BOT_TOKEN` установлен

2. **Webhook контейнеры перезапускаются**  
   - ✅ **Решено**: Удален неправильный параметр `--worker-class` из uvicorn
   - Исправлены права доступа на `/app/storage`

3. **"Conflict: terminated by other getUpdates request"**
   - ✅ **Решено**: Реализован standby режим для второго бота
   - Только один polling активен одновременно

4. **ImportError в обработчиках**
   - ✅ **Решено**: Исправлены импорты `show_main_menu`
   - Обновлена модульная структура handlers

## 📚 Документация

- 📋 [Планы разработки](docs/PLANNING.md)
- 🏗️ [Архитектура](docs/architecture.md)  
- ⚡ [Лучшие практики](docs/best_practices.md)
- 🧪 [Тестирование](docs/TESTING.md)

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

---

**Статус проекта:** ✅ **СТАБИЛЬНАЯ ПРОДАКШН ВЕРСИЯ**  
**Последнее обновление:** 2025-06-09  
**Версия кластера:** 2.0 PRODUCTION READY 