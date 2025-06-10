# 🚀 Активные файлы проекта Aisha

## 📦 Docker Compose файлы

### Продакшн
- `docker-compose.bot.simple.yml` - **Основной продакшн файл**
  - Запускает aisha-bot-primary (polling) + aisha-worker-1 (background tasks)
  - Использует Docker volumes для постоянного хранения
  - Подключается к внешним сервисам (PostgreSQL, Redis, MinIO)

### Локальная разработка
- `docker-compose.bot.local.yml` - **Локальное тестирование**
  - Тестирование перед развертыванием на продакшн
  - Подключается к продакшн сервисам
  - Изолированные локальные volumes

## 📜 Активные скрипты

### Продакшн операции
- `scripts/production/deploy-fixed-bot.sh` - Развертывание исправленного бота
- `scripts/production/monitor-errors.sh` - Мониторинг ошибок в реальном времени
- `scripts/production/check-transcription.sh` - Проверка логов транскрибации
- `scripts/production/restart-with-logs.sh` - Перезапуск с мониторингом
- `scripts/production/setup-logging.sh` - Настройка детального логирования

### Обслуживание
- `scripts/cleanup/organize-project.sh` - Организация и очистка проекта

## 🗂️ Архив

Все устаревшие файлы перемещены в:
- `archive/legacy_compose/` - Старые docker-compose файлы
- `archive/legacy_scripts/` - Устаревшие скрипты
- `archive/old_deployments/` - Старые файлы развертывания
- `archive/deprecated_configs/` - Устаревшие конфигурации

## 🎯 Быстрые команды

### Локальное тестирование
```bash
# Запуск локального тестирования
docker-compose -f docker-compose.bot.local.yml up -d

# Проверка логов
docker logs aisha-bot-primary-local --tail 20 -f
```

### Продакшн управление
```bash
# Развертывание на продакшн
./scripts/production/deploy-fixed-bot.sh

# Мониторинг ошибок
ssh aisha@192.168.0.10 'cd /opt/aisha-backend && ./scripts/production/monitor-errors.sh'

# Проверка транскрибации
ssh aisha@192.168.0.10 'cd /opt/aisha-backend && ./scripts/production/check-transcription.sh'
```

## 🔧 Инфраструктура

### Сервисы
- **PostgreSQL**: 192.168.0.4:5432
- **Redis**: 192.168.0.3:6379  
- **MinIO**: 192.168.0.4:9000
- **Docker Registry**: 192.168.0.4:5000
- **Продакшн сервер**: 192.168.0.10

### Контейнеры на продакшн
- `aisha-bot-primary` - Основной бот (polling)
- `aisha-worker-1` - Фоновые задачи
- `aisha-webhook-api-1/2` - FAL AI webhooks

## 📊 Статус

✅ Все основные проблемы решены:
- Конфликты polling устранены
- Storage permissions исправлены  
- Worker модуль создан
- Детальное логирование настроено

