# Aisha Bot

## Описание
Aisha Bot - это Telegram бот с расширенными возможностями обработки изображений, документов и аудио.

## Требования
- Python 3.9+
- Docker и Docker Compose
- PostgreSQL 15+
- Redis 7+
- MinIO

## Установка и запуск

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/aisha-bot.git
cd aisha-bot
```

### 2. Настройка переменных окружения
```bash
cp .env.example .env
# Отредактируйте .env файл, указав необходимые значения
```

### 3. Запуск сервисов через Docker Compose
```bash
docker-compose up -d
```

### 4. Установка зависимостей Python
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
pip install -r requirements.txt
```

### 5. Инициализация базы данных
```bash
alembic upgrade head
```

### 6. Запуск бота
```bash
python main.py
```

## Мониторинг

### Prometheus
- URL: http://localhost:9090
- Метрики:
  - PostgreSQL
  - Redis
  - MinIO
  - Aisha Bot

### Grafana
- URL: http://localhost:3000
- Логин: admin
- Пароль: указан в .env файле

## Структура проекта

```
aisha-bot/
├── alembic/              # Миграции базы данных
├── frontend_bot/         # Основной код бота
│   ├── handlers/         # Обработчики команд
│   ├── services/         # Бизнес-логика
│   ├── models/          # Модели данных
│   └── utils/           # Утилиты
├── tests/               # Тесты
├── prometheus/          # Конфигурация Prometheus
├── docker-compose.yml   # Конфигурация Docker
├── requirements.txt     # Зависимости Python
└── README.md           # Документация
```

## Разработка

### Запуск тестов
```bash
pytest tests/ -v
```

### Проверка стиля кода
```bash
flake8 frontend_bot/
black frontend_bot/
isort frontend_bot/
mypy frontend_bot/
```

### Миграции базы данных
```bash
# Создание миграции
alembic revision --autogenerate -m "description"

# Применение миграций
alembic upgrade head
```

## Мониторинг и логирование

### Prometheus метрики
- `/metrics` - эндпоинт с метриками
- Метрики PostgreSQL через `pg_exporter`
- Метрики Redis через `redis_exporter`
- Метрики MinIO через встроенный экспортер

### Логирование
- Логи приложения в `logs/`
- Логи Docker контейнеров через `docker-compose logs`

## Безопасность

### Переменные окружения
- Все секретные данные хранятся в `.env`
- `.env` добавлен в `.gitignore`

### SSL/TLS
- MinIO настроен с SSL/TLS
- PostgreSQL использует SSL соединения
- Redis использует SSL соединения

## Резервное копирование

### PostgreSQL
```bash
# Создание бэкапа
pg_dump -U aisha_user -d aisha > backup.sql

# Восстановление
psql -U aisha_user -d aisha < backup.sql
```

### MinIO
- Настроена репликация
- Версионирование объектов включено
- Политики жизненного цикла настроены

## Лицензия
MIT

Telegram-бот для создания и управления аватарами с помощью ИИ, транскрибации аудио/видео, улучшения фото и бизнес-ассистента.

## Основные возможности
- Транскрибация аудио и генерация текстовых/Word-протоколов
- Автоматизация MoM, ToDo, summary
- История файлов, удаление, работа с аватарами
- Асинхронная архитектура, поддержка highload

## Архитектура и best practices
- Хендлеры — только маршрутизация, бизнес-логика в сервисах
- Все шаблоны сообщений, caption, ошибки — централизованы в `frontend_bot/texts/` и его подпапках
- Все клавиатуры — централизованы в keyboards/
- Все shared-утилиты и прогресс-бары — в shared/
- Все операции с файлами — только через aiofiles (async)
- [UPD 2024-07-09] Все sync open заменены на aiofiles.open в async-коде, код приведён к PEP8
- Внешние процессы — только через asyncio.create_subprocess_exec
- Поддержка конкурентного доступа (asyncio.Lock, план на Redis)
- [UPD 2024-07-09] user_transcripts теперь хранится persistent через async JSON store (user_transcripts_store), не теряется между рестартами
- [UPD 2024-07-09] Все протоколы (MoM, summary, todo, Word) покрыты smoke-тестами, которые проверяют только факт отправки файла/сообщения и что файл не пустой, не завися от конкретного текста
- Для составных ключей в словарях используйте только tuple или str, но не list.
- После изменений структуры ключей — обязательно обновляйте все места использования и тесты.

### Работа с утилитами и общими функциями
- Все общие утилиты размещаются в директории `shared/`
- Утилиты группируются по функциональности в отдельные модули:
  - `file_utils.py` - работа с файлами
  - `image_utils.py` - обработка изображений
  - `text_utils.py` - работа с текстом
  - `utils.py` - общие утилиты
- При рефакторинге утилит:
  1. Проверяйте все импорты в проекте
  2. Обновляйте документацию
  3. Пишите тесты
  4. Используйте абсолютные импорты
  5. Следите за циклическими зависимостями
- Все утилиты должны иметь:
  - Type hints
  - Docstrings
  - Обработку исключений
  - Тесты
  - Примеры использования

## Тестирование
- Каждый смысловой блок (summary, mom, todo, word, history, delete) — отдельный файл в tests/handlers/
- Все общие фикстуры — в conftest.py
- Все тесты async-compatible, используют pytest-asyncio и async-моки
- Для моков файловых операций используются только async-compatible моки (AsyncMock, patch, собственные async-контекстные менеджеры), мок aiofiles.open применяется только внутри области теста
- Smoke-тесты не зависят от конкретного текста, а только от факта отправки файла/сообщения
- Покрываются все edge-cases, ошибки снабжены user-friendly assert-сообщениями

## Документация
- [Архитектура](docs/architecture.md)
- [Лучшие практики](docs/best_practices.md)
- [Тестирование](docs/testing.md)
- [Безопасность и асинхронность](docs/async_and_safety.md)
- [Быстрый старт](docs/quickstart.md)
- [Конфигурация](docs/configuration.md)
- [Логирование](docs/logging.md)
- [Changelog](docs/changelog.md)
- [FAQ](docs/faq.md)

## Запуск тестов

Для корректного запуска тестов и избежания ошибок импорта (например, `ModuleNotFoundError: No module named 'frontend_bot'`), используйте следующую команду из корня проекта:

```bash
PYTHONPATH=. pytest --maxfail=1 --disable-warnings -q
```

Это добавит корень проекта в PYTHONPATH и обеспечит корректную работу абсолютных импортов.

---

Для подробностей и расширения — см. docs/ и комментарии в коде.

## Установка

1. Клонировать репозиторий
```bash
git clone https://github.com/yourusername/Aisha_bot_new.git
cd Aisha_bot_new
```

2. Создать виртуальное окружение
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Установить зависимости
```bash
pip install -r requirements.txt
```

4. Создать файл .env и заполнить переменные окружения
```bash
cp .env.example .env
# Отредактировать .env
```

## Запуск

```bash
# Запуск бота
python main.py

# Запуск тестов
pytest tests/

# Запуск с покрытием
pytest --cov=frontend_bot tests/

# Запуск линтера
flake8 frontend_bot/
mypy frontend_bot/
```

## Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# Тесты конкретного модуля
pytest tests/handlers/test_menu_transitions.py

# С подробным выводом
pytest -v

# С покрытием
pytest --cov=frontend_bot

# Параллельный запуск
pytest -n auto

# Конкретные маркеры
pytest -m menu
pytest -m avatar
pytest -m transcribe
pytest -m business
pytest -m photo
```

### Маркеры тестов

- `menu`: тесты переходов между меню
- `avatar`: тесты функционала аватаров
- `transcribe`: тесты функционала транскрибации
- `business`: тесты функционала бизнес-ассистента
- `photo`: тесты функционала улучшения фото
- `integration`: интеграционные тесты
- `slow`: медленные тесты
- `flaky`: нестабильные тесты

### Структура тестов

```
tests/
├── handlers/
│   ├── test_menu_transitions.py
│   ├── test_transcribe_menu_transitions.py
│   ├── test_business_assistant_menu_transitions.py
│   └── test_photo_enhance_menu_transitions.py
├── services/
├── utils/
└── conftest.py
```

### Требования к покрытию

- Строки кода: ≥80%
- Ветки: ≥80%
- Условия: ≥80%

## Разработка

### Линтинг и форматирование

```bash
# Проверка типов
mypy frontend_bot/

# Линтер
flake8 frontend_bot/

# Форматирование
black frontend_bot/
isort frontend_bot/
```

### Pre-commit хуки

```bash
# Установка
pre-commit install

# Запуск вручную
pre-commit run --all-files
```

## Лицензия

MIT

## Авторы

- [Your Name](https://github.com/yourusername)

## Благодарности

- [OpenAI](https://openai.com/) - за GPT API
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - за отличную библиотеку
- [pytest](https://docs.pytest.org/) - за фреймворк тестирования

## Особенности

- Создание аватаров из фотографий
- Галерея аватаров
- Асинхронная обработка файлов
- Безопасное хранение данных
- Полное покрытие тестами

## Требования

- Python 3.8+
- Redis
- PostgreSQL
- FFmpeg

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/aisha_bot.git
cd aisha_bot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env`:
```env
BOT_TOKEN=your_bot_token
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
STORAGE_DIR=storage
MAX_FILE_SIZE=10485760  # 10MB
```

5. Создайте необходимые директории:
```bash
mkdir -p storage/avatars
mkdir -p storage/transcripts
```

## Структура проекта

```
frontend_bot/
├── config/                 # Конфигурация
├── handlers/              # Обработчики команд
├── services/             # Бизнес-логика
├── shared/               # Общие утилиты
│   ├── file_operations.py  # Асинхронные операции с файлами
│   ├── state_manager.py    # Управление состоянием
│   └── image_processing.py # Обработка изображений
├── tests/                # Тесты
└── utils/                # Вспомогательные функции
```

## Работа с файлами

### AsyncFileManager
- Централизованный класс для всех файловых операций
- Асинхронные методы для работы с файлами
- Безопасное удаление файлов и директорий
- Логирование всех операций

### Основные операции
- `ensure_dir`: Создание директории
- `safe_remove`: Безопасное удаление файла
- `safe_rmtree`: Безопасное удаление директории
- `exists`: Проверка существования
- `get_size`: Получение размера файла
- `list_dir`: Получение списка файлов
- `read_file`: Чтение текстового файла
- `write_file`: Запись текстового файла
- `read_binary`: Чтение бинарного файла
- `write_binary`: Запись бинарного файла

### Безопасность
- Все пути типа `Path`
- Проверка размеров файлов
- Валидация типов файлов
- Уникальные имена файлов

### Обработка ошибок
- Обработка всех исключений
- Безопасное удаление
- Логирование ошибок
- Проверка существования

## Запуск

1. Запустите Redis:
```bash
redis-server
```

2. Запустите PostgreSQL:
```bash
pg_ctl -D /path/to/data start
```

3. Запустите бота:
```bash
python -m frontend_bot
```

## Тестирование

1. Установите зависимости для тестирования:
```bash
pip install -r requirements-test.txt
```

2. Запустите тесты:
```bash
pytest
```

## Документация

- [Архитектура](docs/architecture.md)
- [Лучшие практики](docs/best_practices.md)
- [Планирование](docs/PLANNING.md)
- [Задачи](docs/TASK.md)

## Лицензия

MIT

## Интеграция с Redis

Для работы с состояниями, кэшем и очередями используется Redis. Все интеграционные тесты требуют реального Redis-сервера.

### Переменные окружения для Redis

- `REDIS_HOST` — адрес сервера Redis (например, 192.168.0.3)
- `REDIS_PORT` — порт Redis (по умолчанию 6379)
- `REDIS_DB` — номер базы (по умолчанию 0)
- `REDIS_PASSWORD` — пароль для подключения (если установлен)

Пример для `.env`:
```
REDIS_HOST=192.168.0.3
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<ваш_пароль>
```

### Запуск интеграционных тестов Redis

Перед запуском убедитесь, что Redis доступен по сети и переменные окружения заданы. Пример запуска:

```bash
set REDIS_HOST=192.168.0.3 && set REDIS_PORT=6379 && set REDIS_PASSWORD=<ваш_пароль> && python -m pytest frontend_bot/tests/shared/test_redis_integration.py -v
```

Тесты используют реальные подключения и требуют доступности Redis. Для pub/sub тестов реализован polling для стабильности.
