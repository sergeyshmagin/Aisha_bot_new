### Alembic: строка подключения

- Alembic использует строку подключения из `app.core.config.settings.DATABASE_URL` (Pydantic Settings).
- Значение из alembic.ini (sqlalchemy.url) игнорируется, если определён settings.DATABASE_URL.
- Для корректной работы миграций переменная окружения `DATABASE_URL` должна быть определена (см. `.env`).
- Все модели должны быть импортированы в `app.database.models.Base` для поддержки autogenerate.
- Перед применением миграций делать бэкап БД. 