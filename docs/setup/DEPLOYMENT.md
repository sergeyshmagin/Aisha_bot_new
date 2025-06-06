# 🚀 Руководство по развертыванию Aisha Bot v2

> **Статус:** ✅ Production Ready  
> **Обновлено:** Декабрь 2024

## 📋 Обзор

Полное руководство по развертыванию системы Aisha Bot в production окружении с использованием Docker и современных DevOps практик.

## 🏗️ Архитектура развертывания

### Компоненты системы
- **🤖 Telegram Bot** - Основной бот (Python/aiogram)
- **🔗 Webhook API** - FastAPI сервер для обработки webhook'ов
- **🗄️ PostgreSQL** - Основная база данных
- **📦 Redis** - Кэширование и очереди
- **💾 MinIO** - Объектное хранилище файлов
- **🌐 Nginx** - Reverse proxy с SSL

### Серверная архитектура
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Server  │    │ Infrastructure  │    │ Production      │
│   192.168.0.3   │    │   192.168.0.4   │    │  192.168.0.10   │
│                 │    │                 │    │                 │
│ • Redis         │    │ • PostgreSQL    │    │ • Webhook API   │
│ • Кэширование   │    │ • MinIO         │    │ • Nginx + SSL   │
│ • Очереди       │    │ • Registry      │    │ • Мониторинг    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Быстрое развертывание

### Предварительные требования
- Docker 20.10+
- Docker Compose v2
- SSH доступ к серверам
- SSL сертификаты
- Настроенные переменные окружения

### 1. Подготовка
```bash
# Клонирование репозитория
git clone <repo> && cd aisha-backend

# Настройка скриптов
chmod +x scripts/utils/make-executable.sh
./scripts/utils/make-executable.sh

# Проверка SSH доступа
ssh aisha@192.168.0.3 "echo 'Redis OK'"
ssh aisha@192.168.0.4 "echo 'Infrastructure OK'"
ssh aisha@192.168.0.10 "echo 'Production OK'"
```

### 2. Настройка окружения
```bash
# Копирование и настройка конфигурации
cp prod.env.example prod.env
# Отредактируйте prod.env с вашими настройками

# Проверка SSL сертификатов
ls -la ssl_certificate/
# Должны быть: aibots.kz.crt, aibots.kz.key
```

### 3. Развертывание инфраструктуры
```bash
# Настройка Docker Registry
./scripts/deploy/setup-registry.sh

# Настройка production сервера
./scripts/infrastructure/production-setup.sh

# Настройка автозапуска
./scripts/deploy/setup-autostart.sh
```

### 4. Развертывание приложения
```bash
# Проверка готовности системы
./scripts/utils/health-check.sh

# Полное развертывание Webhook API
./scripts/deploy/webhook-complete.sh
```

### 5. Проверка
```bash
# Проверка endpoints
curl -k https://aibots.kz:8443/health
curl -k https://aibots.kz:8443/webhook/fal

# Проверка сервисов
docker ps
sudo systemctl status webhook-api
```

## �� Управление системой

### Ежедневные операции

#### Мониторинг здоровья
```bash
# Комплексная проверка
./scripts/utils/health-check.sh

# Проверка логов
./scripts/utils/log-analyzer.sh

# Метрики системы
docker stats
```

#### Управление сервисами
```bash
# Nginx
./scripts/infrastructure/nginx-management.sh status
./scripts/infrastructure/nginx-management.sh restart
./scripts/infrastructure/nginx-management.sh logs

# Webhook API
ssh aisha@192.168.0.10 'sudo systemctl status webhook-api'
ssh aisha@192.168.0.10 'sudo systemctl restart webhook-api'
```

#### База данных
```bash
# Проверка состояния
python scripts/maintenance/check_db_status.py

# Миграции
alembic upgrade head
python scripts/maintenance/check_migration_status.py

# Бэкап
pg_dump aisha_v2 > backup_$(date +%Y%m%d).sql
```

### Обновление системы

#### Обновление кода
```bash
# Получение изменений
git pull origin main

# Пересборка и развертывание
./scripts/deploy/webhook-complete.sh

# Применение миграций
alembic upgrade head
```

#### Обновление зависимостей
```bash
# Обновление Python пакетов
pip install -r requirements.txt --upgrade

# Пересборка Docker образов
docker build --no-cache -f docker/Dockerfile.webhook -t aisha-webhook:latest .
```

## 🚨 Устранение неполадок

### Частые проблемы

#### 1. Registry недоступен
```bash
# Диагностика
curl http://192.168.0.4:5000/v2/_catalog

# Исправление
./scripts/deploy/fix-registry.sh

# Проверка логов
ssh aisha@192.168.0.4 'sudo docker logs registry-server'
```

#### 2. Webhook API не отвечает
```bash
# Проверка статуса
ssh aisha@192.168.0.10 'sudo systemctl status webhook-api'

# Перезапуск
ssh aisha@192.168.0.10 'sudo systemctl restart webhook-api'

# Логи
ssh aisha@192.168.0.10 'sudo journalctl -u webhook-api -f'
```

#### 3. SSL проблемы
```bash
# Проверка сертификата
openssl x509 -in ssl_certificate/aibots.kz.crt -text -noout

# Тест соединения
openssl s_client -connect aibots.kz:8443 -servername aibots.kz

# Обновление nginx конфигурации
./scripts/infrastructure/nginx-management.sh reload
```

#### 4. База данных недоступна
```bash
# Проверка подключения
python scripts/maintenance/check_db.py

# Проверка PostgreSQL
ssh aisha@192.168.0.4 'sudo systemctl status postgresql'

# Проверка миграций
python scripts/maintenance/check_migration_status.py
```

### Логи и диагностика

#### Основные логи
```bash
# Системные логи
sudo journalctl -u webhook-api -f
sudo journalctl -u nginx -f

# Docker логи
docker-compose -f docker-compose.webhook.prod.yml logs -f

# Логи приложения
tail -f /var/log/aisha/app.log
tail -f /var/log/aisha/webhook.log
```

#### Анализ производительности
```bash
# Метрики Docker
docker stats

# Системные ресурсы
htop
df -h
free -h

# Сетевые соединения
netstat -tulpn | grep :8443
```

## 🔐 Безопасность

### SSL/TLS
- Использование валидных SSL сертификатов
- Принудительное HTTPS перенаправление
- Современные TLS протоколы

### Сетевая безопасность
- Firewall настройки
- Ограничение доступа по IP
- Безопасные SSH ключи

### Мониторинг безопасности
```bash
# Проверка открытых портов
nmap -sT -O localhost

# Анализ логов безопасности
sudo grep "Failed password" /var/log/auth.log

# Проверка SSL конфигурации
./scripts/utils/ssl-check.sh
```

## 📊 Мониторинг и метрики

### Ключевые метрики
- **Время отклика API**: < 500ms
- **Доступность**: > 99.9%
- **Использование памяти**: < 80%
- **Использование диска**: < 85%

### Настройка мониторинга
```bash
# Healthcheck endpoints
curl -k https://aibots.kz:8443/health

# Метрики Docker
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Системные метрики
./scripts/utils/system-metrics.sh
```

## 🔄 Резервное копирование

### Автоматическое резервное копирование
```bash
# Настройка cron задач
./scripts/utils/setup-backup.sh

# Ручное создание бэкапа
./scripts/utils/backup.sh
```

### Восстановление из бэкапа
```bash
# Восстановление базы данных
psql aisha_v2 < backup_20241201.sql

# Восстановление конфигураций
./scripts/utils/restore-config.sh
```

## 📚 Дополнительные ресурсы

### Документация
- [Архитектура системы](../architecture.md)
- [Best Practices](../best_practices.md)
- [Troubleshooting](../reference/troubleshooting.md)

### Полезные команды
```bash
# Быстрая диагностика
./scripts/utils/quick-check.sh

# Полная проверка системы
./scripts/utils/full-system-check.sh

# Обновление всей системы
./scripts/deploy/full-update.sh
```

---

**🎯 Результат:** Полностью функциональная production система Aisha Bot готова к использованию! 