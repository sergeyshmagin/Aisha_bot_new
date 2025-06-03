# 🤖 Aisha Bot v2

Современный Telegram-бот для транскрибации аудио и обработки текста с использованием AI/ML технологий.

## ✨ Возможности

- 🎤 **Транскрибация аудио** - преобразование голосовых сообщений и аудиофайлов в текст
- 📝 **Обработка текста** - работа с текстовыми файлами (.txt)
- 🤖 **AI форматирование** - создание кратких содержаний, списков задач и протоколов
- 📜 **История транскриптов** - сохранение и управление всеми транскриптами
- 🎨 **Дружелюбный интерфейс** - интуитивная навигация с эмодзи и inline-кнопками

## 🏗️ Архитектура

### Технологический стек
- **Backend**: Python 3.11+, aiogram 3.x, SQLAlchemy (async)
- **База данных**: PostgreSQL
- **Хранилище файлов**: MinIO
- **AI/ML**: OpenAI API
- **Кэширование**: Redis (планируется)
- **🐳 Контейнеризация**: Docker + Docker Compose (WSL2)

### Структура проекта
```
aisha_v2/
├── app/
│   ├── core/           # Основные компоненты (DI, настройки, БД)
│   ├── handlers/       # Обработчики Telegram
│   ├── services/       # Бизнес-логика
│   ├── database/       # Модели и репозитории
│   ├── keyboards/      # Клавиатуры
│   └── shared/         # Общие утилиты
├── docker/            # Docker конфигурации
│   ├── Dockerfile.bot # Основной бот
│   ├── Dockerfile.api # API сервер
│   └── nginx/         # Nginx конфигурация
└── docs/              # Документация
```

## 🚀 Быстрый старт

### Требования
- Python 3.11+
- PostgreSQL 15+
- MinIO
- OpenAI API ключ
- **🐳 WSL2 + Docker Desktop** (рекомендуется)

### Установка

1. **Клонирование репозитория**
```bash
git clone <repository-url>
cd Aisha_bot_new
```

2. **Создание виртуального окружения**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows
```

3. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

4. **Настройка переменных окружения**
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

5. **Запуск миграций**
```bash
cd aisha_v2
alembic upgrade head
```

6. **Запуск бота**
```bash
python run.py
```

## ⚙️ Конфигурация

### Переменные окружения

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/aisha_bot

# MinIO Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# OpenAI
OPENAI_API_KEY=sk-your_openai_key_here

# Optional
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
```

### 🐳 Docker развертывание

**📋 ПРИОРИТЕТ:** Unified Docker архитектура для простоты и единообразия dev↔prod.

#### Архитектура развертывания
```
🏠 Development (WSL2): Только приложения (bot + api) → внешние БД
🌐 Production: Только приложения (bot + api + nginx) → те же внешние БД
```

#### Быстрый старт Development (WSL2)
```bash
# 1. Убедитесь, что внешние сервисы доступны
# PostgreSQL, Redis, MinIO должны быть запущены

# 2. Настройка окружения
cp env.docker.template .env.docker.dev
# Отредактируйте с адресами ваших сервисов:
# DATABASE_HOST=localhost (или IP сервера)
# REDIS_HOST=localhost (или IP сервера) 
# MINIO_ENDPOINT=localhost:9000 (или IP:PORT)

# 3. Проверка внешних сервисов
chmod +x docker/scripts/health-check.sh
./docker/scripts/health-check.sh

# 4. Запуск приложений
docker-compose up -d

# 5. Инициализация БД
docker-compose exec aisha-bot alembic upgrade head

# 6. Проверка
docker-compose ps
curl http://localhost:8443/health
```

#### Production развертывание
```bash
# 1. На целевом сервере
cd /opt/aisha-v2
cp env.docker.template .env.docker.prod
# Настроить адреса ваших БД сервисов

# 2. Проверка внешних сервисов
./docker/scripts/health-check.sh

# 3. Развертывание
./docker/scripts/deploy.sh

# 4. Управление через systemd
sudo systemctl status aisha-bot
```

**📚 Подробная документация:**
- **Быстрый старт:** [`DOCKER_QUICKSTART.md`](DOCKER_QUICKSTART.md)
- **Полный план:** [`docs/plans/DOCKER_MIGRATION_PLAN.md`](docs/plans/DOCKER_MIGRATION_PLAN.md)

**🎯 Преимущества Unified архитектуры:**
- ✅ **Простота:** Одинаковый подход в dev и prod
- ✅ **Быстрота:** Запуск только приложений, не БД сервисов  
- ✅ **Надежность:** Использование существующих настроенных БД
- ✅ **Единообразие:** Одни и те же внешние сервисы везде
- ✅ **Масштабируемость:** Готовность к горизонтальному масштабированию

## 📖 Использование

### Основные команды
- `/start` - Запуск бота и главное меню
- `/transcribe` - Меню транскрибации
- `/history` - История транскриптов

### Навигация
```
Главное меню
    ↓ 🎤 Транскрибация
Меню транскрибации
    ├── 🎤 Аудио          # Обработка аудио/голосовых
    ├── 📝 Текст          # Обработка .txt файлов
    └── 📜 История        # Просмотр сохраненных транскриптов
        ↓ Выбор транскрипта
    Карточка транскрипта
        ├── 📄 Краткое содержание
        ├── ✅ Список задач
        └── 📋 Протокол
```

### Поддерживаемые форматы
- **Аудио**: MP3, WAV, OGG, M4A (голосовые сообщения Telegram)
- **Текст**: TXT файлы в UTF-8

## 🔧 Разработка

### Архитектурные принципы
- **Async везде** - все I/O операции асинхронные
- **Dependency Injection** - внедрение зависимостей через DI контейнер
- **Разделение ответственности** - handlers, services, repositories
- **Типизация** - полная поддержка type hints

### Структура обработчиков
```python
# Современная архитектура (без Legacy)
handlers/
├── main.py                     # Главное меню
├── transcript_main.py          # История и навигация
└── transcript_processing.py    # Обработка аудио/текста
```

### Запуск тестов
```bash
# Unit тесты
pytest tests/unit/

# Интеграционные тесты
pytest tests/integration/

# Все тесты с покрытием
pytest --cov=aisha_v2 --cov-report=html
```

### Линтинг и форматирование
```bash
# Проверка стиля
flake8 aisha_v2/
mypy aisha_v2/

# Форматирование
black aisha_v2/
isort aisha_v2/
```

## 📚 Документация

- [`docs/architecture.md`](docs/architecture.md) - Архитектура проекта
- [`docs/best_practices.md`](docs/best_practices.md) - Лучшие практики разработки
- [`docs/async_and_safety.md`](docs/async_and_safety.md) - Async Python и безопасность
- [`docs/navigation_transcript.md`](docs/navigation_transcript.md) - Архитектура навигации

### 🎨 Система аватаров
- [`docs/avatars_architecture.md`](docs/avatars_architecture.md) - Архитектура системы аватаров
- [`docs/avatar_implementation_plan.md`](docs/avatar_implementation_plan.md) - План реализации аватаров

### 🤖 FAL AI Knowledge Base
- [`docs/fal_knowlege_base/README.md`](docs/fal_knowlege_base/README.md) - Полная база знаний FAL AI
- [`docs/fal_knowlege_base/flux-lora-portrait-trainer-api.md`](docs/fal_knowlege_base/flux-lora-portrait-trainer-api.md) - Portrait Trainer API
- [`docs/fal_knowlege_base/flux-pro-trainer.md`](docs/fal_knowlege_base/flux-pro-trainer.md) - Pro Trainer API
- [`docs/fal_knowlege_base/fal-ai-models-comparison.md`](docs/fal_knowlege_base/fal-ai-models-comparison.md) - Сравнение моделей

## 🐛 Отладка

### Логирование
Все компоненты используют структурированное логирование с префиксами:
```
[AUDIO] Начало обработки для user_id=123
[DB] Ошибка подключения к базе данных
[MINIO] Файл загружен: transcripts/user123/file.txt
```

### Частые проблемы

1. **"Bad Request: there is no text in the message to edit"**
   - Решение: Fallback на новые сообщения при ошибках редактирования

2. **Конфликт типов BaseModel**
   - Решение: Явные импорты `from aiogram.types import InlineKeyboardButton`

3. **Ошибки MinIO подключения**
   - Проверьте настройки MINIO_ENDPOINT и доступность сервиса

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте feature-ветку (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

### Стандарты кода
- Следуйте PEP8
- Добавляйте type hints
- Пишите docstrings для публичных методов
- Покрывайте код тестами
- Используйте async/await для I/O операций

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🙏 Благодарности

- [aiogram](https://github.com/aiogram/aiogram) - Современный фреймворк для Telegram Bot API
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit
- [MinIO](https://min.io/) - Высокопроизводительное объектное хранилище
- [OpenAI](https://openai.com/) - AI/ML API для обработки текста

---

**Версия**: 2.0.0  
**Последнее обновление**: 2025-05-23  
**Статус**: ✅ Активная разработка 