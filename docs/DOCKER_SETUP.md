# 🐳 Настройка Docker окружения для Aisha Bot v2

## 📋 Содержание
1. [Архитектура](#архитектура)
2. [Настройка Development](#настройка-development)
3. [Рекомендации по разработке](#рекомендации-по-разработке)
4. [Production развертывание](#production-развертывание)
5. [Интеграция с существующим nginx](#интеграция-с-существующим-nginx)
6. [Troubleshooting](#troubleshooting)

---

## 🏗️ Архитектура

### Унифицированный подход
- **Development (Windows WSL2)**: Контейнеры приложений + внешние БД
- **Production (Ubuntu 24 + aibots.kz)**: Контейнеры приложений + nginx + внешние БД

### Компоненты
- 🤖 **aisha-bot**: Telegram бот
- 🌐 **aisha-api**: FastAPI сервер (для webhook)
- 🔄 **nginx**: Reverse proxy с SSL (уже настроен)
- 🗄️ **PostgreSQL**: Внешний (уже настроен)
- 💾 **Redis**: Внешний (уже настроен)
- 📁 **MinIO**: Внешний (уже настроен)

---

## 🛠️ Настройка Development

### 1. Подготовка окружения

#### Windows + WSL2 (Рекомендуется)
```bash
# 1. Установить Docker Desktop
# Скачать с https://www.docker.com/products/docker-desktop/

# 2. Включить WSL2 integration в Docker Desktop
# Settings → Resources → WSL Integration → Enable Ubuntu-22.04

# 3. В WSL2:
cd /mnt/c/dev/Aisha_bot_new  # или куда установлен проект
```

#### Альтернатива: Docker в Windows
```cmd
# Если используете Windows CMD/PowerShell:
cd C:\dev\Aisha_bot_new
```

### 2. Конфигурация

#### Копирование шаблона переменных
```bash
cp env.docker.dev.template .env.docker.dev
```

#### Редактирование .env.docker.dev
```bash
# Отредактируйте файл с вашими настройками:
nano .env.docker.dev
```

**Основные переменные для изменения:**
```env
# Хосты ваших внешних сервисов
DATABASE_HOST=192.168.1.100  # IP вашего PostgreSQL сервера
REDIS_HOST=192.168.1.101      # IP вашего Redis сервера
MINIO_ENDPOINT=192.168.1.102:9000  # IP:PORT вашего MinIO

# Пароли и ключи
POSTGRES_PASSWORD=ваш_postgres_пароль
MINIO_ACCESS_KEY=ваш_minio_access_key
MINIO_SECRET_KEY=ваш_minio_secret_key
TELEGRAM_BOT_TOKEN=ваш_telegram_bot_token
OPENAI_API_KEY=ваш_openai_key
FAL_API_KEY=ваш_fal_key
```

### 3. Проверка доступности сервисов

```bash
# Проверка внешних сервисов
./docker/scripts/health-check.sh
```

### 4. Запуск в development режиме

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Статус контейнеров
docker-compose ps
```

### 5. Работа с приложением

#### Доступные сервисы:
- 🤖 **Bot**: Работает автоматически (polling/webhook)
- 🌐 **API**: http://localhost:8443/docs (Swagger UI)

#### Полезные команды:
```bash
# Перезапуск отдельного сервиса
docker-compose restart aisha-bot

# Подключение к контейнеру
docker-compose exec aisha-bot bash

# Просмотр логов отдельного сервиса
docker-compose logs -f aisha-bot

# Остановка всех сервисов
docker-compose down

# Очистка volumes (если нужно)
docker-compose down -v
```

---

## 💻 Рекомендации по разработке

### Выбор окружения разработки

#### ✅ Рекомендуется: WSL2 + Docker
**Преимущества:**
- Нативная производительность Linux в Windows
- Единая среда с production
- Лучшая совместимость с Docker
- Файловая система Linux для проекта

**Настройка:**
1. Установите WSL2: `wsl --install Ubuntu-22.04`
2. Перенесите проект в WSL2: `/home/user/projects/Aisha_bot_new`
3. Используйте VS Code с WSL extension

#### ⚠️ Альтернатива: Docker в Windows
**Преимущества:**
- Простота настройки
- Работает с существующей файловой системой

**Недостатки:**
- Медленная работа с bind mounts
- Проблемы с правами файлов

### Workflow разработки

#### 1. Hot Reload
```bash
# Изменения в коде автоматически подхватываются благодаря volumes:
# - .:/app (для бота)
# - ./api_server:/app/api_server (для API)
```

#### 2. Отладка
```bash
# Подключение отладчика к контейнеру
docker-compose exec aisha-bot python -m pdb app/main.py

# Или добавьте breakpoint() в код
```

#### 3. Тестирование
```bash
# Запуск тестов в контейнере
docker-compose exec aisha-bot python -m pytest

# Или создайте отдельный test сервис в docker-compose.yml
```

### IDE конфигурация

#### VS Code + WSL
```json
// .vscode/settings.json
{
    "python.interpreterPath": "/usr/bin/python3",
    "python.defaultInterpreterPath": "/app/.venv/bin/python",
    "remote.WSL.fileWatcher.polling": true
}
```

#### Подключение к контейнеру
- Используйте "Dev Containers" extension
- Или Remote-SSH к WSL2

---

## 🚀 Production развертывание

### 1. Подготовка сервера aibots.kz

```bash
# На сервере aibots.kz (Ubuntu 24)
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io docker-compose-plugin git -y
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Клонирование в существующую директорию

```bash
# Переходим в рабочую директорию
cd /opt/aisha-backend

# Клонируем проект (или обновляем git pull)
git clone <repository-url> .
# или если уже есть: git pull origin main
```

### 3. Конфигурация production

```bash
# Копирование и настройка переменных
cp env.docker.prod.template .env.docker.prod

# Редактирование production настроек
nano .env.docker.prod
```

**Production переменные:**
```env
COMPOSE_PROJECT_NAME=aisha-v2-prod
DATABASE_HOST=localhost  # или IP PostgreSQL сервера
REDIS_HOST=localhost     # или IP Redis сервера
MINIO_ENDPOINT=localhost:9000  # или IP:PORT MinIO сервера
DEBUG=false
ENVIRONMENT=production
TELEGRAM_BOT_TOKEN=ваш_продакшн_токен
# остальные реальные ключи...
```

### 4. Развертывание с автоматизацией

```bash
# Проверка сервисов
./docker/scripts/health-check.sh

# Автоматическое развертывание
chmod +x docker/scripts/deploy-prod.sh
./docker/scripts/deploy-prod.sh

# Или ручной запуск
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🌐 Интеграция с существующим nginx

### Ваша текущая конфигурация готова!

Ваш nginx уже настроен правильно в `/etc/nginx/sites-enabled/aisha-webhook`:

```nginx
# Upstream указывает на localhost:8000 - именно туда Docker пробросит API
upstream aisha_api {
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
}

# SSL уже настроен с вашими сертификатами
ssl_certificate /opt/aisha-backend/ssl/aibots_kz_full.crt;
ssl_certificate_key /opt/aisha-backend/ssl/aibots.kz.key;
```

### Интеграция с Docker

1. **API контейнер** пробрасывает порт `127.0.0.1:8000:8000`
2. **Nginx upstream** уже настроен на `127.0.0.1:8000`
3. **SSL сертификаты** уже есть в `/opt/aisha-backend/ssl/`
4. **Логи nginx** уже настроены в `/var/log/aisha/`

**Никаких изменений в nginx не требуется!** 🎉

### Проверка интеграции

```bash
# После запуска Docker контейнеров проверьте:

# 1. API отвечает локально
curl http://localhost:8000/health

# 2. API отвечает через nginx
curl -k https://aibots.kz:8443/health

# 3. Webhook endpoint работает
curl -k -X POST https://aibots.kz:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

---

## 🔧 Troubleshooting

### Проблемы с подключением к БД

```bash
# Проверка доступности PostgreSQL
telnet $DATABASE_HOST 5432

# Проверка из контейнера
docker-compose -f docker-compose.prod.yml exec aisha-bot nc -zv $DATABASE_HOST 5432

# Логи подключения
docker-compose -f docker-compose.prod.yml logs aisha-bot | grep -i database
```

### Проблемы с Redis

```bash
# Проверка Redis
redis-cli -h $REDIS_HOST ping

# Из контейнера
docker-compose -f docker-compose.prod.yml exec aisha-bot nc -zv $REDIS_HOST 6379
```

### Проблемы с MinIO

```bash
# Проверка MinIO API
curl http://$MINIO_ENDPOINT/minio/health/live

# Проверка доступа
mc alias set local http://$MINIO_ENDPOINT $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
mc ls local/
```

### Проблемы с nginx интеграцией

```bash
# Проверка nginx конфигурации
sudo nginx -t

# Проверка логов nginx
sudo tail -f /var/log/aisha/nginx_error.log

# Проверка upstream
curl -v http://127.0.0.1:8000/health

# Перезагрузка nginx
sudo systemctl reload nginx
```

### Проблемы с Docker

```bash
# Очистка Docker системы
docker system prune -a

# Пересборка контейнеров
docker-compose -f docker-compose.prod.yml build --no-cache

# Просмотр всех контейнеров
docker ps -a

# Логи конкретного контейнера
docker-compose -f docker-compose.prod.yml logs -f aisha-api
```

---

## 📊 Мониторинг

### Логи

```bash
# Все логи Docker
docker-compose -f docker-compose.prod.yml logs -f

# Логи приложения
tail -f /opt/aisha-backend/logs/app.log

# Логи nginx
tail -f /var/log/aisha/nginx_access.log
tail -f /var/log/aisha/webhook_access.log
```

### Метрики

```bash
# Использование ресурсов
docker stats

# Информация о контейнерах
docker-compose -f docker-compose.prod.yml ps
```

### Healthchecks

```bash
# Статус здоровья контейнеров
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Health}}"

# Проверка endpoints
curl http://localhost:8000/health
curl -k https://aibots.kz:8443/health
```

### Systemd интеграция

```bash
# Статус сервиса
sudo systemctl status aisha-v2

# Запуск/остановка/перезапуск
sudo systemctl start aisha-v2
sudo systemctl stop aisha-v2
sudo systemctl restart aisha-v2

# Автозапуск
sudo systemctl enable aisha-v2
```

---

## 🎯 Следующие шаги

1. **Тестирование на реальном сервере** aibots.kz
2. **Настройка мониторинга** (Prometheus + Grafana)
3. **Автоматизация CI/CD** для автоматического деплоя
4. **Backup стратегия** для логов и конфигураций
5. **Rolling updates** для zero-downtime деплоя

---

**🚀 Docker окружение готово к интеграции с вашей продакшн инфраструктурой!** 