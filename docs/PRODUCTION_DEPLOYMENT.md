# 🚀 Развертывание в продакшн через Docker Registry

Полная инструкция по развертыванию кластера Aisha Bot на продакшн сервере 192.168.0.10 с использованием Docker Registry.

## 📋 Архитектура инфраструктуры

```
┌─────────────────────────────────────────────────────────────┐
│                 Разработка (WSL/Local)                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐                                       │
│  │ Сборка образов  │ ─────────────────┐                   │
│  └─────────────────┘                   │                   │
└─────────────────────────────────────────┼───────────────────┘
                                          │
                  ┌───────────────────────▼───────────────┐
                  │         Docker Registry               │
                  │         192.168.0.4:5000             │
                  │  ┌─────────────┬─────────────────┐    │
                  │  │ nginx:tag   │ webhook:tag     │    │
                  │  │ bot:tag     │ ...             │    │
                  │  └─────────────┴─────────────────┘    │
                  └───────────────────┬───────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────┐
│                Продакшн (192.168.0.10)                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐                                       │
│  │ Nginx LB        │  :80, :8443                          │
│  │ (SSL Termination)│                                      │
│  └─────────┬───────┘                                       │
│            │                                               │
│  ┌─────────▼───────┬─────────────────┐                    │
│  │ Webhook API     │ Webhook API     │                    │
│  │ Instance 1      │ Instance 2      │                    │
│  └─────────────────┴─────────────────┘                    │
│                                                            │
│  ┌─────────────────┬─────────────────┬─────────────────┐  │
│  │ Bot Polling 1   │ Bot Polling 2   │ Background      │  │
│  │ (Primary)       │ (Standby)       │ Worker          │  │
│  └─────────────────┴─────────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Redis           │  │ PostgreSQL      │  │ MinIO           │
│ 192.168.0.3     │  │ 192.168.0.4     │  │ 192.168.0.4     │
│ (Sessions/Cache)│  │ (Database)      │  │ (Files)         │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 🔧 Предварительная настройка

### 1. Настройка Docker Registry

На сервере 192.168.0.4 должен быть запущен Docker Registry:

```bash
# На сервере 192.168.0.4
docker run -d -p 5000:5000 --restart=always --name registry registry:2
```

### 2. Настройка SSH доступа

Убедитесь, что у вас есть SSH доступ к продакшн серверу:

```bash
# Тест SSH подключения
ssh aisha@192.168.0.10 "echo 'SSH works'"
```

### 3. Подготовка SSL сертификатов

Разместите SSL сертификаты в директории `ssl/`:

```
ssl/
├── aibots_kz.crt    # Основной сертификат
└── aibots_kz.key    # Приватный ключ
```

## 🚀 Процесс развертывания

### Шаг 1: Сборка и пуш образов

```bash
# Сборка и пуш всех образов с тегом latest
./scripts/deployment/push-images.sh

# Сборка и пуш с конкретной версией
./scripts/deployment/push-images.sh v2.1.0

# Только пуш существующих образов (без пересборки)
./scripts/deployment/push-images.sh --push-only

# Принудительная пересборка и пуш
./scripts/deployment/push-images.sh --force-build
```

**Что происходит:**
1. ✅ Проверяется доступность Docker Registry
2. 🔍 Проверяются существующие локальные образы
3. 🏗️ Собираются Docker образы (если не --push-only)
4. 🏷️ Тегируются образы для registry
5. 📤 Пушатся образы в registry
6. ✅ Проверяется наличие образов в registry
7. 🧹 Очищаются локальные теги registry

### Шаг 2: Развертывание на продакшн

```bash
# Развертывание latest версии
./scripts/deployment/deploy-production.sh

# Развертывание конкретной версии
./scripts/deployment/deploy-production.sh v2.1.0

# Локальное развертывание (для тестирования)
./scripts/deployment/deploy-production.sh --local

# Принудительная загрузка образов
./scripts/deployment/deploy-production.sh --force-pull
```

**Что происходит:**
1. 🌐 Проверяется доступность продакшн сервера
2. 🐳 Проверяется доступность Docker Registry
3. 🔧 Настраивается Docker на продакшн сервере
4. 📄 Копируются конфигурационные файлы
5. 🌐 Создаются Docker сети
6. 📥 Загружаются образы из registry
7. 🛑 Останавливаются старые контейнеры
8. 🚀 Разворачивается Webhook API кластер
9. 🤖 Разворачивается Bot кластер
10. 🔍 Проводится финальная проверка

## 📊 Мониторинг развертывания

### Проверка статуса контейнеров

```bash
# Через SSH
ssh aisha@192.168.0.10 "docker ps --filter 'name=aisha'"

# Локально (если развертывание --local)
docker ps --filter 'name=aisha'
```

### Проверка логов

```bash
# Логи nginx
ssh aisha@192.168.0.10 "docker logs aisha-nginx-prod"

# Логи webhook API
ssh aisha@192.168.0.10 "docker logs aisha-webhook-api-1"

# Логи основного бота
ssh aisha@192.168.0.10 "docker logs aisha-bot-polling-1"
```

### Проверка health check

```bash
# Проверка health check всех сервисов
ssh aisha@192.168.0.10 "docker ps --filter 'health=healthy'"

# Проверка доступности HTTP/HTTPS
curl -f http://192.168.0.10/
curl -f -k https://192.168.0.10:8443/
```

## 🔄 Обновление сервисов

### 1. Обновление кода

```bash
# Сборка и пуш новой версии
./scripts/deployment/push-images.sh v2.1.1 --force-build

# Развертывание новой версии
./scripts/deployment/deploy-production.sh v2.1.1
```

### 2. Откат к предыдущей версии

```bash
# Откат к предыдущей версии
./scripts/deployment/deploy-production.sh v2.1.0
```

### 3. Обновление конфигурации

```bash
# Обновление только конфигурации (без пересборки)
./scripts/deployment/deploy-production.sh --skip-registry --force-pull
```

## 🚨 Устранение неполадок

### Проблемы с Docker Registry

```bash
# Проверка доступности registry
curl -f http://192.168.0.4:5000/v2/

# Проверка образов в registry
curl http://192.168.0.4:5000/v2/aisha/nginx/tags/list
curl http://192.168.0.4:5000/v2/aisha/webhook/tags/list
curl http://192.168.0.4:5000/v2/aisha/bot/tags/list
```

### Проблемы с insecure registry

```bash
# На продакшн сервере, проверка настройки
ssh aisha@192.168.0.10 "cat /etc/docker/daemon.json"

# Перезапуск Docker daemon
ssh aisha@192.168.0.10 "sudo systemctl restart docker"
```

### Проблемы с сетями

```bash
# Очистка конфликтующих сетей
ssh aisha@192.168.0.10 "docker network rm aisha_cluster aisha_bot_cluster"

# Повторное развертывание
./scripts/deployment/deploy-production.sh --force-pull
```

### Проблемы с SSL

```bash
# Проверка SSL сертификатов
ssh aisha@192.168.0.10 "ls -la /opt/aisha-backend/ssl/"
ssh aisha@192.168.0.10 "openssl x509 -in /opt/aisha-backend/ssl/aibots_kz.crt -text -noout"
```

## 📝 Конфигурационные файлы

### `docker-compose.registry.yml`
Конфигурация Webhook API кластера с образами из registry

### `docker-compose.bot.registry.yml`
Конфигурация Bot кластера с образами из registry

### `cluster.env`
Переменные окружения для всего кластера

## 🔐 Безопасность

### Переменные окружения

Убедитесь, что все секретные ключи обновлены в `cluster.env`:

```bash
# Обязательные к обновлению
TELEGRAM_BOT_TOKEN=your-real-token
OPENAI_API_KEY=your-real-key
FAL_API_KEY=your-real-key
JWT_SECRET_KEY=your-real-secret
PASSWORD_SALT=your-real-salt
```

### Файрволл

Убедитесь, что на продакшн сервере открыты нужные порты:

```bash
# HTTP и HTTPS для внешнего доступа
sudo ufw allow 80/tcp
sudo ufw allow 8443/tcp

# SSH для администрирования
sudo ufw allow 22/tcp
```

## ✅ Чек-лист развертывания

- [ ] Docker Registry запущен на 192.168.0.4:5000
- [ ] SSH доступ к 192.168.0.10 настроен
- [ ] SSL сертификаты размещены в `ssl/`
- [ ] Файл `cluster.env` обновлен с продакшн значениями
- [ ] Внешние сервисы доступны (Redis, PostgreSQL, MinIO)
- [ ] Файрволл настроен на продакшн сервере
- [ ] DNS записи для aibots.kz указывают на 192.168.0.10
- [ ] Образы собраны и запушены в registry
- [ ] Кластер развернут на продакшн сервере
- [ ] Health checks проходят успешно
- [ ] HTTP/HTTPS доступ работает

## 🔗 Связанные документы

- [`../scripts/README.md`](../scripts/README.md) - Документация скриптов
- [`CLUSTER_DEPLOYMENT.md`](CLUSTER_DEPLOYMENT.md) - Документация локального развертывания
- [`../cluster.env`](../cluster.env) - Конфигурация кластера 