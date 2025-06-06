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