# Aisha Bot v2

Telegram-бот для обработки аудио и текста с использованием AI.

## Основные возможности

- 🎤 Транскрибация аудио в текст
- 📝 Обработка текстовых файлов
- 🔄 Форматирование транскриптов (summary, todo, protocol)
- 🖼 Работа с изображениями
- 👤 Генерация аватаров

## Технологии

- Python 3.9+
- aiogram 3.x
- SQLAlchemy 2.x
- Pydantic 2.x
- MinIO
- Redis
- PostgreSQL

## Установка и запуск

1. Клонируем репозиторий:
```bash
git clone https://github.com/your-username/aisha-bot.git
cd aisha-bot
```

2. Создаем виртуальное окружение:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. Устанавливаем зависимости:
```bash
pip install -r requirements.txt
```

4. Настраиваем переменные окружения:
```bash
cp .env.example .env
# Редактируем .env
```

5. Запускаем бота:
```bash
python -m aisha_v2.app.main
```

## Структура проекта

```
aisha_v2/
├── app/
│   ├── core/           # Конфигурация и базовые компоненты
│   ├── handlers/       # Обработчики команд
│   ├── keyboards/      # Клавиатуры
│   ├── models/         # Модели данных
│   ├── services/       # Бизнес-логика
│   └── utils/          # Утилиты
├── docs/               # Документация
├── tests/              # Тесты
└── migrations/         # Миграции БД
```

## Документация

- [Best Practices](docs/best_practices.md) - лучшие практики разработки
- [Architecture](docs/architecture.md) - архитектура проекта
- [API Reference](docs/api.md) - документация API

## Разработка

### Требования

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- MinIO

### Тестирование

```bash
# Запуск тестов
pytest

# Проверка типов
mypy .

# Линтинг
flake8
black .
isort .
```

### Миграции

```bash
# Создание миграции
alembic revision --autogenerate -m "description"

# Применение миграций
alembic upgrade head
```

## Лицензия

MIT

## Контакты

- Telegram: @your_username
- Email: your.email@example.com 