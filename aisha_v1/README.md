# Aisha Bot

Telegram-бот для обработки аватаров и транскрипции аудио с использованием асинхронного подхода.

## Технологии

- Python 3.9+
- PostgreSQL 14+
- SQLAlchemy 2.0+
- Alembic для миграций
- Telebot (async)
- MinIO для хранения файлов

## Структура проекта

```
.
├── database/           # Модели и репозитории БД
├── migrations/         # Миграции Alembic
├── services/          # Бизнес-логика
├── texts/            # Шаблоны сообщений
├── keyboards/        # Клавиатуры бота
├── shared/           # Общие утилиты
├── tests/            # Тесты
└── docs/             # Документация
```

## База данных

### Модели

- **UserProfile**: Основная информация о пользователе
  - user_id (PK): ID пользователя в Telegram
  - telegram_id: Уникальный ID в Telegram
  - first_name: Имя пользователя
  - last_name: Фамилия пользователя
  - username: Username в Telegram
  - language_code: Код языка
  - is_premium: Премиум статус
  - registered_at: Дата регистрации
  - updated_at: Дата обновления

- **UserState**: Состояние FSM пользователя
  - id (PK): Уникальный ID
  - user_id (FK): ID пользователя
  - state_data: JSON с данными состояния
  - created_at: Дата создания
  - updated_at: Дата обновления

- **UserBalance**: Баланс пользователя
  - id (PK): Уникальный ID
  - user_id (FK): ID пользователя
  - coins: Количество монет
  - created_at: Дата создания
  - updated_at: Дата обновления

- **UserAvatar**: Аватары пользователя
  - id (PK): UUID
  - user_id (FK): ID пользователя
  - avatar_data: JSON с данными аватара
  - created_at: Дата создания
  - updated_at: Дата обновления

- **UserTranscript**: Транскрипты пользователя
  - id (PK): UUID
  - user_id (FK): ID пользователя
  - transcript_data: JSON с данными транскрипта
  - created_at: Дата создания
  - updated_at: Дата обновления

- **Transaction**: История транзакций
  - id (PK): UUID
  - user_id (FK): ID пользователя
  - amount: Сумма
  - type: Тип (credit/debit)
  - description: Описание
  - created_at: Дата создания

- **UserHistory**: История действий пользователя
  - id (PK): UUID
  - user_id (FK): ID пользователя
  - action_type: Тип действия
  - action_data: JSON с данными действия
  - created_at: Дата создания
  - updated_at: Дата обновления

### Миграции

Для управления миграциями используется Alembic. Основные команды:

```bash
# Создание новой миграции
alembic revision --autogenerate -m "description"

# Применение миграций
alembic upgrade head

# Откат последней миграции
alembic downgrade -1

# Просмотр истории миграций
alembic history
```

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/aisha_bot.git
cd aisha_bot
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

3. Создайте файл `.env` с необходимыми переменными окружения:
```env
# Telegram
BOT_TOKEN=your_bot_token

# PostgreSQL
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_db_name
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# MinIO
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_BUCKET=your_bucket
```

4. Примените миграции:
```bash
alembic upgrade head
```

5. Запустите бота:
```bash
python main.py
```

## Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск с покрытием
pytest --cov=.

# Запуск конкретного теста
pytest tests/test_specific.py
```

## Документация

Подробная документация доступна в директории `docs/`:

- [Архитектура](docs/architecture.md)
- [Лучшие практики](docs/best_practices.md)
- [Асинхронность и безопасность](docs/async_and_safety.md)

## Лицензия

MIT

## Разработка

### Тесты
```bash
# Запуск всех тестов
pytest

# Запуск конкретного теста
pytest tests/test_postgres_models.py
```

### Линтеры
```bash
# Проверка кода
flake8
mypy .
black .
isort .
```

## Лицензия

MIT

## Структура хранения

### MinIO Buckets

Проект использует следующие бакеты в MinIO:

1. `avatars` - для хранения аватаров пользователей
   - Срок хранения: бессрочно
   - Структура: `users/{user_id}/avatars/{avatar_id}`

2. `transcripts` - для хранения транскриптов
   - Срок хранения: 90 дней
   - Структура: `users/{user_id}/transcripts/{transcript_id}`

3. `documents` - для хранения документов
   - Срок хранения: бессрочно
   - Структура: `users/{user_id}/documents/{document_id}`

4. `temp` - для временных файлов
   - Срок хранения: 3 дня
   - Структура: `temp/{user_id}/{file_id}`

### Утилиты хранения

Для работы с хранилищем используются утилиты из модуля `shared_storage.storage_utils`:

```python
from shared_storage.storage_utils import (
    upload_file,
    download_file,
    delete_file,
    generate_presigned_url,
    get_file_metadata,
    get_object_path
)

# Загрузка файла
await upload_file(
    bucket="avatars",
    object_name=get_object_path("avatars", user_id=123, avatar_id="abc"),
    data=image_data,
    content_type="image/jpeg",
    metadata={"name": "avatar.jpg"}
)

# Получение presigned URL
url = await generate_presigned_url(
    bucket="avatars",
    object_name=get_object_path("avatars", user_id=123, avatar_id="abc"),
    expires=3600  # 1 час
)
```

## Кратко
- Все состояния и фото аватаров — только через PostgreSQL и MinIO
- Нет локальных json-файлов, нет legacy FSM
- Все детали архитектуры и best practices см. в:
  - [docs/architecture.md](docs/architecture.md)
  - [docs/best_practices.md](docs/best_practices.md)