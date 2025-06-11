# 🚀 Деплоймент Aisha Bot

> **Версия**: 2.0 (2025-06-11) - Через Docker Registry

## 📋 Основной скрипт

### `deploy-via-registry.sh`

Современный скрипт деплоя через Docker Registry.

**Использование:**
```bash
./scripts/deployment/deploy-via-registry.sh [ОПЦИИ] [ТЕГ]
```

**Примеры:**
```bash
# Полный деплой (сборка + загрузка + деплой)
./scripts/deployment/deploy-via-registry.sh

# Только сборка и загрузка образа
./scripts/deployment/deploy-via-registry.sh --build-only v1.2.0

# Только деплой существующего образа
./scripts/deployment/deploy-via-registry.sh --deploy-only latest

# Проверка состояния
./scripts/deployment/deploy-via-registry.sh --check-health
```

## 🏗️ Процесс деплоя

1. **Проверка предварительных условий**
   - Docker установлен и работает
   - SSH доступ к продакшн серверу
   - Docker Registry доступен

2. **Сборка образа** (если не `--deploy-only`)
   - Сборка из `docker/Dockerfile.bot`
   - Тегирование для реестра
   - Пуш в Registry

3. **Деплой на продакшн** (если не `--build-only`)
   - Обновление docker-compose файла
   - Загрузка нового образа
   - Перезапуск контейнеров

4. **Проверка здоровья**
   - Статус контейнеров
   - Проверка логов

## 🌐 Инфраструктура

- **Registry**: `192.168.0.4:5000`
- **Production**: `aisha@192.168.0.10`
- **Docker Compose**: `docker-compose.bot.simple.yml`

## 🔧 Локальная разработка

Используйте `docker-compose.local.yml` для локальной разработки:

```bash
# Запуск только бота
docker-compose -f docker-compose.local.yml up aisha-bot-dev

# Запуск с webhook API
docker-compose -f docker-compose.local.yml --profile webhook up

# Остановка
docker-compose -f docker-compose.local.yml down
``` 