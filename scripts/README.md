# Скрипты AISHA Backend

## Структура

### 🔧 Обслуживание (maintenance/)
Скрипты для поддержки инфраструктуры:

- **`check_db.py`** - Проверка подключения к базе данных
- **`check_redis.py`** - Проверка подключения к Redis
- **`check_db_status.py`** - Проверка статуса БД и миграций
- **`check_migration_status.py`** - Детальная проверка миграций
- **`manage_db.py`** - Управление базой данных
- **`create_migration.py`** - Создание новых миграций

### 🧪 Тестирование (testing/)
Скрипты для отладки и тестирования:

- **`test_app_health.py`** - Комплексная проверка здоровья приложения
- **`test_generation_flow.py`** - Тестирование процесса генерации
- **`test_final_generation.py`** - Финальное тестирование генерации
- **`test_generation_check.py`** - Быстрая проверка генерации
- **`debug_generation_issue.py`** - Отладка проблем генерации
- **`debug_avatar_gallery.py`** - Отладка галереи аватаров
- **`check_avatars.py`** - Проверка состояния аватаров
- **`check_completed_avatars.py`** - Проверка завершенных аватаров

### 🚀 Продакшн (production/)
Скрипты для продакшн окружения:

- **`deploy_production_minimal.sh`** - Минимальное развертывание в продакшн
- **`init_generation_data.py`** - Инициализация данных для генерации

## Использование

### Обслуживание

```bash
# Активируйте виртуальное окружение
source .venv/bin/activate

# Проверка всех подключений
python scripts/maintenance/check_db.py
python scripts/maintenance/check_redis.py

# Управление миграциями
python scripts/maintenance/manage_db.py --help
```

### Тестирование

```bash
# Комплексная проверка
python scripts/testing/test_app_health.py

# Тестирование генерации
python scripts/testing/test_generation_flow.py

# Отладка проблем
python scripts/testing/debug_generation_issue.py
```

### Продакшн

```bash
# Развертывание (только администраторы)
bash scripts/production/deploy_production_minimal.sh

# Инициализация данных
python scripts/production/init_generation_data.py
```

## Требования

Все скрипты требуют:
- Python 3.11+
- Активированное виртуальное окружение
- Правильно настроенный `.env` файл
- Доступ к базе данных и Redis

## Добавление новых скриптов

1. Поместите скрипт в соответствующую категорию
2. Добавьте описание в этот README
3. Убедитесь что скрипт имеет docstring и help
4. Протестируйте в безопасном окружении

## Устаревшие скрипты

Следующие скрипты удалены как устаревшие:
- `*enum*.py` - исправления enum (больше не нужны)
- `*avatar_status*.py` - исправления статусов (исправлено)
- `create_test_db.py` - создание тестовой БД (заменено на Docker) 