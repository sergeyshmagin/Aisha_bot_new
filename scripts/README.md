# 🚀 Scripts Directory

Комплексный набор скриптов для управления системой Aisha Bot.

## 📂 Структура

```
scripts/
├── deploy/                 # 🚀 Скрипты развертывания
│   ├── webhook-complete.sh  # Полное развертывание webhook API
│   ├── fix-registry.sh      # Исправление Docker Registry
│   ├── setup-autostart.sh   # Настройка автозапуска сервисов
│   ├── setup-registry.sh    # Быстрая настройка Registry
│   └── README.md           # Документация по развертыванию
├── infrastructure/         # 🏗️ Управление инфраструктурой
│   ├── nginx-management.sh  # Управление nginx
│   ├── production-setup.sh  # Настройка продакшн сервера
│   ├── registry-setup.sh    # Продвинутая настройка Registry
│   └── README.md           # Документация по инфраструктуре
├── maintenance/            # 🔧 Скрипты обслуживания
│   ├── check_*.py          # Проверки состояния системы
│   ├── fix_*.py           # Исправления и миграции
│   └── manage_*.py        # Управление компонентами
├── testing/               # 🧪 Тестирование
├── utils/                 # 🛠️ Утилиты
│   ├── make-executable.sh  # Установка прав исполнения
│   ├── cleanup.sh         # Очистка системы
│   ├── backup.sh          # Резервное копирование
│   ├── health-check.sh    # Комплексная проверка
│   └── log-analyzer.sh    # Анализ логов
├── production/            # 📦 Устаревшие продакшн скрипты
└── README.md             # Этот файл
```

## 🎯 Быстрый старт

### 1. Первичная настройка
```bash
# Сделать все скрипты исполняемыми
./scripts/utils/make-executable.sh

# Настроить продакшн сервер
./scripts/infrastructure/production-setup.sh
```

### 2. Настройка инфраструктуры
```bash
# Настроить Docker Registry
./scripts/infrastructure/registry-setup.sh

# Настроить автозапуск сервисов
./scripts/deploy/setup-autostart.sh
```

### 3. Развертывание
```bash
# Полное развертывание Webhook API
./scripts/deploy/webhook-complete.sh
```

## 🔧 Основные операции

### Развертывание системы
```bash
# Быстрое исправление Registry
./scripts/deploy/fix-registry.sh

# Полное развертывание с проверками
./scripts/deploy/webhook-complete.sh
```

### Управление инфраструктурой
```bash
# Управление nginx
./scripts/infrastructure/nginx-management.sh status
./scripts/infrastructure/nginx-management.sh restart

# Настройка продакшн сервера
./scripts/infrastructure/production-setup.sh
```

### Обслуживание системы
```bash
# Проверка здоровья системы
./scripts/utils/health-check.sh

# Очистка системы
./scripts/utils/cleanup.sh

# Анализ логов
./scripts/utils/log-analyzer.sh
```

### Работа с базой данных
```bash
# Проверка состояния БД
python scripts/maintenance/check_db_status.py

# Управление миграциями
python scripts/maintenance/manage_db.py

# Проверка Redis
python scripts/maintenance/check_redis.py
```

## 🌐 Серверная инфраструктура

### 192.168.0.3 - Redis Server
- Redis для кеширования и очередей
- Пароль: `wd7QuwAbG0wtyoOOw3Sm`

### 192.168.0.4 - Infrastructure Server
- PostgreSQL база данных
- MinIO объектное хранилище
- Docker Registry
- Автоматическое резервное копирование

### 192.168.0.10 - Production Server (aibots.kz)
- Webhook API сервисы
- Nginx reverse proxy с SSL
- Мониторинг и логирование

## 📋 Переменные окружения

### Основные конфигурации
```bash
# Redis
REDIS_HOST=192.168.0.3
REDIS_PASSWORD=wd7QuwAbG0wtyoOOw3Sm

# PostgreSQL
POSTGRES_HOST=192.168.0.4
POSTGRES_DB=aisha
POSTGRES_USER=aisha

# MinIO
MINIO_ENDPOINT=192.168.0.4:9000
MINIO_ACCESS_KEY=minioadmin

# Docker Registry
REGISTRY_URL=192.168.0.4:5000
```

## 🔒 Безопасность

### SSL Сертификаты
- Сертификаты хранятся в `ssl_certificate/`
- Автоматическое обновление через Let's Encrypt
- HTTPS на порту 8443

### Docker Security
- Insecure registry для внутренней сети
- Изоляция контейнеров
- Регулярные обновления образов

## 🚨 Устранение неполадок

### Частые проблемы

#### Docker Registry недоступен
```bash
./scripts/deploy/fix-registry.sh
```

#### Webhook API не отвечает
```bash
./scripts/infrastructure/nginx-management.sh restart
./scripts/utils/health-check.sh
```

#### Проблемы с базой данных
```bash
python scripts/maintenance/check_db_status.py
python scripts/maintenance/manage_db.py
```

### Логи и мониторинг
```bash
# Анализ логов
./scripts/utils/log-analyzer.sh

# Проверка всех сервисов
./scripts/utils/health-check.sh

# Мониторинг nginx
./scripts/infrastructure/nginx-management.sh logs
```

## 📚 Документация

- **[Deploy README](deploy/README.md)** - Подробная документация по развертыванию
- **[Infrastructure README](infrastructure/README.md)** - Управление инфраструктурой
- **[Utils README](utils/README.md)** - Описание утилит
- **[Maintenance Scripts](maintenance/)** - Python скрипты обслуживания

## 🔄 Автоматизация

### Systemd Services
- `docker-registry.service` - Docker Registry
- `infrastructure.service` - PostgreSQL + MinIO
- `webhook-api.service` - Webhook API

### Мониторинг
```bash
# Статус всех сервисов
systemctl status docker-registry infrastructure webhook-api

# Логи сервисов
journalctl -u webhook-api.service -f
```

## 🤝 Вклад в проект

1. Все новые скрипты должны быть в соответствующих подкаталогах
2. Добавляйте документацию в README.md каждого каталога
3. Используйте единый стиль логирования и обработки ошибок
4. Тестируйте скрипты перед коммитом

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `./scripts/utils/log-analyzer.sh`
2. Запустите диагностику: `./scripts/utils/health-check.sh`
3. Проверьте документацию в соответствующем каталоге

---

*Обновлено автоматически скриптом `scripts/utils/make-executable.sh`*

# 🛠️ Скрипты инфраструктуры Aisha Bot

Набор скриптов для автоматизации развертывания, мониторинга и обслуживания кластера Aisha Bot.

## 📁 Структура директорий

```
scripts/
├── deployment/     # Скрипты развертывания
├── cleanup/        # Скрипты очистки системы
├── monitoring/     # Скрипты мониторинга
└── README.md       # Эта документация
```

## 🚀 Развертывание (`deployment/`)

### `deploy-cluster.sh`
Основной скрипт развертывания кластера с локальными образами

### `push-images.sh`
Скрипт сборки и пуша образов в Docker Registry (192.168.0.4:5000)

### `deploy-production.sh`
Скрипт развертывания на продакшн сервере 192.168.0.10 с использованием образов из registry

**Использование deploy-cluster.sh:**
```bash
./scripts/deployment/deploy-cluster.sh [опции]
```

**Использование push-images.sh:**
```bash
./scripts/deployment/push-images.sh [версия] [опции]
```

**Использование deploy-production.sh:**
```bash
./scripts/deployment/deploy-production.sh [версия] [опции]
```

**Опции:**
- `--clean-aggressive` - Агрессивная очистка Docker (удаление всех неиспользуемых ресурсов)
- `--skip-build` - Пропустить сборку образов (использовать существующие)
- `--verbose` - Подробный вывод команд Docker
- `--help` - Показать справку

**Примеры:**
```bash
# Обычное развертывание
./scripts/deployment/deploy-cluster.sh

# Развертывание с полной очисткой Docker
./scripts/deployment/deploy-cluster.sh --clean-aggressive

# Быстрое развертывание без пересборки образов
./scripts/deployment/deploy-cluster.sh --skip-build

# Развертывание с подробным выводом
./scripts/deployment/deploy-cluster.sh --verbose --clean-aggressive
```

**Что делает:**
1. ✅ Проверяет предварительные условия
2. 🔐 Подготавливает SSL сертификаты
3. 🏗️ Собирает Docker образы (опционально)
4. 🌐 Проверяет внешние сервисы
5. 🛑 Останавливает старые контейнеры
6. 🌐 Создает Docker сети
7. 🚀 Разворачивает Webhook API кластер
8. 🤖 Разворачивает Bot кластер
9. 🔍 Проводит финальную проверку

## 🧹 Очистка (`cleanup/`)

### `cleanup-docker.sh`
Утилита для очистки Docker окружения от старых образов и контейнеров

**Использование:**
```bash
./scripts/cleanup/cleanup-docker.sh [режим]
```

**Режимы:**
- `safe` (по умолчанию) - Безопасная очистка (только Aisha ресурсы)
- `aggressive` - Агрессивная очистка (все неиспользуемые ресурсы кроме томов)
- `full` - Полная очистка (ВСЕ неиспользуемые ресурсы ВКЛЮЧАЯ ТОМА!)

**Примеры:**
```bash
# Безопасная очистка
./scripts/cleanup/cleanup-docker.sh

# Агрессивная очистка
./scripts/cleanup/cleanup-docker.sh aggressive

# Полная очистка (ОПАСНО!)
./scripts/cleanup/cleanup-docker.sh full
```

## 📊 Мониторинг (`monitoring/`)

### `monitor-cluster.sh`
Интерактивная утилита мониторинга состояния кластера

**Использование:**
```bash
./scripts/monitoring/monitor-cluster.sh [команда]
```

**Команды:**
- `status` - Показать текущий статус кластера
- `logs` - Показать логи всех сервисов
- `health` - Проверить здоровье сервисов
- `interactive` - Интерактивный режим мониторинга

**Примеры:**
```bash
# Быстрая проверка статуса
./scripts/monitoring/monitor-cluster.sh status

# Просмотр логов
./scripts/monitoring/monitor-cluster.sh logs

# Интерактивный мониторинг
./scripts/monitoring/monitor-cluster.sh
```

## 🌐 Архитектура развернутого кластера

```
┌─────────────────────────────────────────────────────────────┐
│                    Сервер 192.168.0.10 (aibots.kz)         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐                                        │
│  │ Nginx LB        │  :80, :8443                           │
│  │ (SSL Termination)│                                       │
│  └─────────┬───────┘                                        │
│            │                                                │
│  ┌─────────▼───────┬─────────────────┐                     │
│  │ Webhook API     │ Webhook API     │                     │
│  │ Instance 1      │ Instance 2      │                     │
│  │ (Primary)       │ (Secondary)     │                     │
│  └─────────────────┴─────────────────┘                     │
│                                                             │
│  ┌─────────────────┬─────────────────┬─────────────────┐   │
│  │ Bot Polling 1   │ Bot Polling 2   │ Background      │   │
│  │ (Primary)       │ (Standby)       │ Worker          │   │
│  └─────────────────┴─────────────────┴─────────────────┘   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Redis           │  │ PostgreSQL      │  │ MinIO           │
│ 192.168.0.3     │  │ 192.168.0.4     │  │ 192.168.0.4     │
│ (Sessions/Cache)│  │ (Database)      │  │ (Files)         │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 🔧 Конфигурация

### Переменные окружения
Все конфигурации хранятся в файле `cluster.env` в корне проекта.

### SSL сертификаты
Сертификаты должны находиться в директории `ssl/`:
- `aibots_kz.crt` - Основной сертификат
- `aibots_kz.key` - Приватный ключ

### Docker Compose файлы
- `docker-compose.prod.yml` - Webhook API кластер и Nginx
- `docker-compose.bot.prod.yml` - Bot кластер

## 🚨 Устранение неполадок

### Проблемы с сетями
```bash
# Очистка конфликтующих сетей
docker network rm aisha_cluster aisha_bot_cluster
./scripts/deployment/deploy-cluster.sh
```

### Проблемы с образами
```bash
# Полная пересборка образов
./scripts/cleanup/cleanup-docker.sh aggressive
./scripts/deployment/deploy-cluster.sh --clean-aggressive
```

### Проверка логов
```bash
# Логи конкретного сервиса
docker logs aisha-nginx-prod
docker logs aisha-webhook-api-1
docker logs aisha-bot-polling-1

# Или через мониторинг
./scripts/monitoring/monitor-cluster.sh logs
```

## 📋 Чек-лист развертывания

- [ ] Сервер 192.168.0.10 настроен и доступен
- [ ] Docker и Docker Compose установлены
- [ ] SSL сертификаты размещены в `ssl/`
- [ ] Файл `cluster.env` заполнен правильными значениями
- [ ] Внешние сервисы (Redis, PostgreSQL, MinIO) доступны
- [ ] Порты 80 и 8443 открыты в файрволле
- [ ] DNS записи для aibots.kz настроены

## 🔗 Связанные файлы

- [`../docs/CLUSTER_DEPLOYMENT.md`](../docs/CLUSTER_DEPLOYMENT.md) - Подробная документация по развертыванию
- [`../cluster.env`](../cluster.env) - Конфигурация кластера
- [`../docker-compose.prod.yml`](../docker-compose.prod.yml) - API кластер
- [`../docker-compose.bot.prod.yml`](../docker-compose.bot.prod.yml) - Bot кластер 