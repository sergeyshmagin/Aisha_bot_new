# Конфигурация и параметры

## .env

| Переменная         | Пример                | Описание                       |
|--------------------|----------------------|--------------------------------|
| TELEGRAM_TOKEN     | xxxxx                | Токен Telegram-бота            |
| POSTGRES_DB        | aisha                | Имя основной БД (production)    |
| POSTGRES_USER      | aisha_user           | Пользователь БД                |
| POSTGRES_PASSWORD  | KbZZGJHX09KSH7r9ev4m | Пароль пользователя БД         |
| POSTGRES_HOST      | 192.168.0.4          | Адрес сервера PostgreSQL       |
| POSTGRES_PORT      | 5432                 | Порт PostgreSQL                |
| ...                | ...                  | ...                            |

## config.py

| Параметр           | Пример                | Описание                      |
|--------------------|----------------------|-------------------------------|
| DATABASE_URL       | postgresql://aisha_user:KbZZGJHX09KSH7r9ev4m@192.168.0.4:5432/aisha | DSN для Alembic и sync-ORM |
| ASYNC_DATABASE_URL | postgresql+asyncpg://aisha_user:KbZZGJHX09KSH7r9ev4m@192.168.0.4:5432/aisha | DSN для async-ORM        |
| ...                | ...                  | ...                           |

## Рекомендации по настройке
- Для dev-окружения: используйте отдельную БД (например, `aisha_dev`).
- Для prod-окружения: используйте переменные окружения как выше.
- Все параметры подключения к БД должны задаваться только через .env или переменные окружения.

---

TODO: Заполнить таблицы и рекомендации.
