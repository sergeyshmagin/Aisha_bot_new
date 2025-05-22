# Работа с базой данных

## Настройка окружения

1. Убедитесь, что PostgreSQL запущен и доступен
2. Создайте `.env` файл на основе `.env.example`
3. Укажите корректные параметры подключения к БД

## Управление миграциями

### Проверка подключения
```bash
python scripts/manage_db.py check
```

### Создание новой миграции
```bash
python scripts/manage_db.py create --message "Описание изменений"
```

### Применение миграций
```bash
# Обновить до последней версии
python scripts/manage_db.py upgrade

# Обновить до конкретной ревизии
python scripts/manage_db.py upgrade --revision 20250520_initial
```

### Откат миграций
```bash
# Откатить до конкретной ревизии
python scripts/manage_db.py downgrade --revision 20250520_initial
```

### Просмотр списка миграций
```bash
python scripts/manage_db.py show
```

## Миграция данных

### Перенос данных из старой базы
```bash
python scripts/migrate_data.py
```

## Структура базы данных

### Таблицы

1. `users` - Пользователи
   - `id` - ID пользователя (PK)
   - `telegram_id` - Telegram ID (уникальный)
   - `first_name` - Имя
   - `last_name` - Фамилия (опционально)
   - `username` - Username в Telegram (опционально)
   - `language_code` - Код языка
   - `is_premium` - Премиум статус
   - `created_at` - Дата создания
   - `updated_at` - Дата обновления

2. `user_balances` - Балансы пользователей
   - `id` - ID баланса (PK)
   - `user_id` - ID пользователя (FK)
   - `coins` - Количество монет
   - `created_at` - Дата создания
   - `updated_at` - Дата обновления

3. `user_states` - Состояния пользователей
   - `id` - ID состояния (PK)
   - `user_id` - ID пользователя (FK)
   - `state_data` - Данные состояния (JSON)
   - `created_at` - Дата создания
   - `updated_at` - Дата обновления

4. `avatars` - Аватары
   - `id` - ID аватара (PK, UUID)
   - `user_id` - ID пользователя (FK)
   - `name` - Имя аватара
   - `gender` - Пол аватара
   - `status` - Статус аватара
   - `is_draft` - Черновик
   - `avatar_data` - Дополнительные данные (JSON)
   - `created_at` - Дата создания
   - `updated_at` - Дата обновления

5. `avatar_photos` - Фотографии аватаров
   - `id` - ID фото (PK, UUID)
   - `avatar_id` - ID аватара (FK)
   - `minio_key` - Ключ в MinIO
   - `order` - Порядковый номер
   - `created_at` - Дата создания
   - `updated_at` - Дата обновления

## Индексы

1. `users`
   - `telegram_id` (уникальный)

2. `user_balances`
   - `user_id` (уникальный)

3. `user_states`
   - `user_id` (уникальный)

4. `avatars`
   - `user_id`
   - `status`

5. `avatar_photos`
   - `avatar_id`
   - `order`

## Связи

1. `user_balances.user_id` → `users.id` (CASCADE)
2. `user_states.user_id` → `users.id` (CASCADE)
3. `avatars.user_id` → `users.id` (CASCADE)
4. `avatar_photos.avatar_id` → `avatars.id` (CASCADE)
