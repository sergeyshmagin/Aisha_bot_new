# 📁 Скрипты проекта AISHA Backend

**Дата обновления**: 04.06.2025  
**Статус**: ✅ Актуализировано

## 📂 Структура

### 🧪 `testing/` - Тестовые скрипты
- `check_completed_avatars.py` - Проверка завершенных аватаров и их готовности к генерации
- `start_ready_training.py` - Запуск обучения готовых аватаров
- `check_avatars.py` - Общая проверка состояния аватаров в системе
- `test_app_health.py` - Проверка здоровья приложения и всех компонентов

### 🔧 `maintenance/` - Обслуживание системы
- `check_db_status.py` - Проверка статуса базы данных
- `fix_minio_urls.py` - Исправление URL'ов MinIO в базе данных
- `check_db.py` - Быстрая проверка подключения к БД
- `check_migration_status.py` - Проверка статуса миграций Alembic
- `check_redis.py` - Проверка подключения и состояния Redis
- `create_migration.py` - Создание новой миграции Alembic
- `manage_db.py` - Управление базой данных (создание, удаление, миграции)

### 🚀 `production/` - Продакшн скрипты
- `deploy_production_minimal.sh` - Минимальный скрипт развертывания
- `init_generation_data.py` - Инициализация данных для генерации

## 🎯 Основные команды

### Проверка системы
```bash
# Проверка здоровья всех компонентов
python scripts/testing/test_app_health.py

# Проверка состояния аватаров
python scripts/testing/check_avatars.py

# Проверка завершенных аватаров
python scripts/testing/check_completed_avatars.py
```

### Обслуживание
```bash
# Проверка базы данных
python scripts/maintenance/check_db_status.py

# Проверка Redis
python scripts/maintenance/check_redis.py

# Проверка миграций
python scripts/maintenance/check_migration_status.py
```

### Развертывание
```bash
# Развертывание в продакшн
bash scripts/production/deploy_production_minimal.sh

# Инициализация данных генерации
python scripts/production/init_generation_data.py
```

## 📋 Использование

### Перед запуском скриптов:
```bash
# Активация виртуального окружения
source .venv/bin/activate

# Установка PYTHONPATH
export PYTHONPATH=/opt/aisha-backend

# Или запуск с PYTHONPATH
PYTHONPATH=/opt/aisha-backend python scripts/testing/check_avatars.py
```

### Переменные окружения:
Убедитесь что настроены:
- `DATABASE_URL` - подключение к PostgreSQL
- `REDIS_URL` - подключение к Redis  
- `MINIO_*` - настройки MinIO
- `FAL_API_KEY` - ключ FAL AI

## 🔄 Регулярное обслуживание

### Ежедневно:
- `test_app_health.py` - проверка здоровья системы
- `check_avatars.py` - мониторинг состояния аватаров

### Еженедельно:
- `check_db_status.py` - проверка состояния БД
- `check_migration_status.py` - проверка миграций

### По необходимости:
- `fix_minio_urls.py` - исправление URL'ов при изменении MinIO
- `start_ready_training.py` - запуск отложенного обучения

## 📝 Примечания

- Все скрипты поддерживают асинхронную работу
- Используют единую систему конфигурации из `app.core.config`
- Интегрированы с системой логирования
- Безопасны для запуска в продакшн окружении

**Система скриптов готова к использованию!** 🚀 