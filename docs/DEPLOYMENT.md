# 🚀 Руководство по развертыванию Aisha v2

**Обновлено:** 15.01.2025  
**Статус:** ✅ Готово к продакшн развертыванию  
**Версия:** v2.0 с FAL AI интеграцией

## 📋 Обзор развертывания

Полное руководство по развертыванию Telegram-бота Aisha v2 в продакшн среде. Включает настройку всех компонентов, внешних сервисов и мониторинга.

### 🎯 Архитектура развертывания
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   API Server    │    │   Database      │
│   (Port 8000)   │    │   (Port 8443)   │    │   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
         │     MinIO       │    │     Redis       │    │    FAL AI       │
         │  (Port 9000)    │    │  (Port 6379)    │    │   (External)    │
         └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Предварительные требования

### Системные требования
- **OS:** Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM:** Минимум 2GB, рекомендуется 4GB
- **CPU:** 2+ ядра
- **Диск:** 20GB+ свободного места
- **Python:** 3.11+

### Необходимые сервисы
- **PostgreSQL 15+** - основная база данных
- **Redis 7+** - кэширование и сессии
- **MinIO** - объектное хранилище файлов
- **Nginx** - reverse proxy (опционально)

## 📦 Установка зависимостей

### 1. Системные пакеты
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git curl wget

# CentOS/RHEL
sudo dnf install -y python3.11 python3-pip git curl wget
```

### 2. PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создание базы данных
sudo -u postgres psql
CREATE DATABASE aisha_v2;
CREATE USER aisha_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE aisha_v2 TO aisha_user;
\q
```

### 3. Redis
```bash
# Ubuntu/Debian
sudo apt install -y redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Проверка
redis-cli ping
```

### 4. MinIO
```bash
# Скачивание и установка
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Создание пользователя и директорий
sudo useradd -r minio-user -s /sbin/nologin
sudo mkdir -p /opt/minio/data
sudo chown minio-user:minio-user /opt/minio/data

# Systemd сервис
sudo tee /etc/systemd/system/minio.service > /dev/null <<EOF
[Unit]
Description=MinIO
Documentation=https://docs.min.io
Wants=network-online.target
After=network-online.target
AssertFileIsExecutable=/usr/local/bin/minio

[Service]
WorkingDirectory=/opt/minio
User=minio-user
Group=minio-user
EnvironmentFile=-/etc/default/minio
ExecStartPre=/bin/bash -c "if [ -z \"\${MINIO_VOLUMES}\" ]; then echo \"Variable MINIO_VOLUMES not set in /etc/default/minio\"; exit 1; fi"
ExecStart=/usr/local/bin/minio server \$MINIO_OPTS \$MINIO_VOLUMES
Restart=always
LimitNOFILE=65536
TasksMax=infinity
TimeoutStopSec=infinity
SendSIGKILL=no

[Install]
WantedBy=multi-user.target
EOF

# Конфигурация MinIO
sudo tee /etc/default/minio > /dev/null <<EOF
MINIO_VOLUMES="/opt/minio/data"
MINIO_OPTS="--console-address :9001"
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
EOF

sudo systemctl daemon-reload
sudo systemctl start minio
sudo systemctl enable minio
```

## 🔧 Настройка приложения

### 1. Клонирование репозитория
```bash
cd /opt
sudo git clone https://github.com/your-repo/aisha_v2.git
sudo chown -R $USER:$USER /opt/aisha_v2
cd /opt/aisha_v2
```

### 2. Виртуальное окружение
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Конфигурация окружения
```bash
cp .env.example .env
nano .env
```

### 4. Основные переменные окружения
```env
# ==================== ОСНОВНЫЕ НАСТРОЙКИ ====================

# База данных
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=aisha_v2
DATABASE_USER=aisha_user
DATABASE_PASSWORD=secure_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_AVATARS=aisha-v2-avatars
MINIO_BUCKET_TRANSCRIPTS=aisha-v2-transcripts

# ==================== TELEGRAM BOT ====================

TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# ==================== ВНЕШНИЕ API ====================

# OpenAI
OPENAI_API_KEY=sk-your_openai_api_key_here

# FAL AI
FAL_API_KEY=your_fal_api_key_here
FAL_WEBHOOK_URL=https://yourdomain.com:8443/api/v1/avatar/status_update

# ==================== РЕЖИМЫ РАБОТЫ ====================

# Продакшн режим
DEBUG=false
ENVIRONMENT=production

# FAL AI тестовый режим (установите false для продакшна)
FAL_TRAINING_TEST_MODE=false

# ==================== БЕЗОПАСНОСТЬ ====================

# JWT секрет
JWT_SECRET=your_jwt_secret_here

# Разрешенные хосты
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# ==================== ЛОГИРОВАНИЕ ====================

LOG_LEVEL=INFO
LOG_FILE=/var/log/aisha_v2/app.log
```

### 5. Применение миграций
```bash
source venv/bin/activate
alembic upgrade head
```

### 6. Создание buckets в MinIO
```bash
# Установка MinIO клиента
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

# Настройка алиаса
mc alias set local http://localhost:9000 minioadmin minioadmin123

# Создание buckets
mc mb local/aisha-v2-avatars
mc mb local/aisha-v2-transcripts

# Настройка политик доступа
mc policy set public local/aisha-v2-avatars
mc policy set public local/aisha-v2-transcripts
```

## 🔐 Настройка внешних сервисов

### 1. Telegram Bot Token

#### Создание бота
1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям для создания бота
4. Получите токен и добавьте в `.env`

#### Настройка webhook (опционально)
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://yourdomain.com:8443/webhook/telegram"}'
```

### 2. OpenAI API

#### Получение ключа
1. Зарегистрируйтесь на https://platform.openai.com
2. Создайте API ключ в разделе API Keys
3. Добавьте ключ в `.env` как `OPENAI_API_KEY`

#### Настройка лимитов
- Установите месячные лимиты расходов
- Настройте уведомления о превышении
- Мониторьте использование через dashboard

### 3. FAL AI

#### Получение ключа
1. Зарегистрируйтесь на https://fal.ai
2. Получите API ключ в настройках аккаунта
3. Добавьте ключ в `.env` как `FAL_API_KEY`

#### Настройка webhook
```bash
# Webhook URL для уведомлений о статусе обучения
FAL_WEBHOOK_URL=https://yourdomain.com:8443/api/v1/avatar/status_update
```

## 🌐 Настройка SSL и домена

### 1. Получение SSL сертификата
```bash
# Установка Certbot
sudo apt install -y certbot

# Получение сертификата
sudo certbot certonly --standalone -d yourdomain.com

# Копирование сертификатов для API сервера
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/aisha_v2/api_server/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/aisha_v2/api_server/ssl/
sudo chown $USER:$USER /opt/aisha_v2/api_server/ssl/*
```

### 2. Настройка автообновления сертификатов
```bash
# Добавление в crontab
sudo crontab -e

# Добавить строку:
0 12 * * * /usr/bin/certbot renew --quiet && systemctl restart aisha-api-server
```

## 🚀 Запуск сервисов

### 1. Создание systemd сервисов

#### Основной Telegram бот
```bash
sudo tee /etc/systemd/system/aisha-bot.service > /dev/null <<EOF
[Unit]
Description=Aisha v2 Telegram Bot
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/aisha_v2
Environment=PATH=/opt/aisha_v2/venv/bin
ExecStart=/opt/aisha_v2/venv/bin/python -m app.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### API сервер для webhook
```bash
sudo tee /etc/systemd/system/aisha-api-server.service > /dev/null <<EOF
[Unit]
Description=Aisha v2 API Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/aisha_v2/api_server
Environment=PATH=/opt/aisha_v2/venv/bin
ExecStart=/opt/aisha_v2/venv/bin/python run_api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 2. Запуск сервисов
```bash
sudo systemctl daemon-reload
sudo systemctl start aisha-bot
sudo systemctl start aisha-api-server
sudo systemctl enable aisha-bot
sudo systemctl enable aisha-api-server
```

### 3. Проверка статуса
```bash
sudo systemctl status aisha-bot
sudo systemctl status aisha-api-server
```

## 📊 Мониторинг и логирование

### 1. Настройка логирования
```bash
# Создание директории для логов
sudo mkdir -p /var/log/aisha_v2
sudo chown $USER:$USER /var/log/aisha_v2

# Настройка ротации логов
sudo tee /etc/logrotate.d/aisha_v2 > /dev/null <<EOF
/var/log/aisha_v2/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        systemctl reload aisha-bot
        systemctl reload aisha-api-server
    endscript
}
EOF
```

### 2. Health check endpoints
```bash
# Проверка основного бота
curl http://localhost:8000/health

# Проверка API сервера
curl https://localhost:8443/health

# Проверка webhook статуса
curl https://localhost:8443/api/v1/webhook/status
```

### 3. Мониторинг ресурсов
```bash
# Использование памяти и CPU
htop

# Логи сервисов
sudo journalctl -u aisha-bot -f
sudo journalctl -u aisha-api-server -f

# Логи приложения
tail -f /var/log/aisha_v2/app.log
```

## 🔧 Настройка Nginx (опционально)

### 1. Установка и конфигурация
```bash
sudo apt install -y nginx

sudo tee /etc/nginx/sites-available/aisha_v2 > /dev/null <<EOF
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # API сервер
    location /api/ {
        proxy_pass https://localhost:8443;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # MinIO консоль
    location /minio/ {
        proxy_pass http://localhost:9001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/aisha_v2 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🧪 Тестирование развертывания

### 1. Проверка компонентов
```bash
# База данных
psql -h localhost -U aisha_user -d aisha_v2 -c "SELECT version();"

# Redis
redis-cli ping

# MinIO
mc admin info local

# Сервисы
systemctl is-active aisha-bot
systemctl is-active aisha-api-server
```

### 2. Функциональное тестирование
```bash
# Отправка тестового сообщения боту
# Проверка создания аватара
# Тестирование webhook
curl -X POST https://yourdomain.com:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test_123",
    "status": "completed",
    "training_type": "portrait"
  }'
```

## 🚨 Решение проблем

### Частые проблемы и решения

#### Бот не отвечает
```bash
# Проверка статуса
sudo systemctl status aisha-bot

# Проверка логов
sudo journalctl -u aisha-bot -n 50

# Проверка токена
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

#### Ошибки базы данных
```bash
# Проверка подключения
psql -h localhost -U aisha_user -d aisha_v2

# Проверка миграций
cd /opt/aisha_v2
source venv/bin/activate
alembic current
alembic history
```

#### Проблемы с SSL
```bash
# Проверка сертификатов
sudo certbot certificates

# Тестирование SSL
openssl s_client -connect yourdomain.com:8443

# Обновление сертификатов
sudo certbot renew
```

#### Ошибки FAL AI
```bash
# Проверка API ключа
curl -H "Authorization: Key YOUR_FAL_API_KEY" https://fal.run/fal-ai/fast-sdxl

# Проверка webhook
curl -X POST https://yourdomain.com:8443/api/v1/avatar/status_update \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

## 📈 Оптимизация производительности

### 1. Настройка PostgreSQL
```sql
-- /etc/postgresql/15/main/postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### 2. Настройка Redis
```bash
# /etc/redis/redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 3. Мониторинг производительности
```bash
# Установка monitoring tools
sudo apt install -y htop iotop nethogs

# Мониторинг в реальном времени
htop
iotop
nethogs
```

## 🔄 Обновление системы

### 1. Обновление кода
```bash
cd /opt/aisha_v2
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart aisha-bot
sudo systemctl restart aisha-api-server
```

### 2. Резервное копирование
```bash
# База данных
pg_dump -h localhost -U aisha_user aisha_v2 > backup_$(date +%Y%m%d).sql

# MinIO данные
mc mirror local/aisha-v2-avatars /backup/minio/avatars/
mc mirror local/aisha-v2-transcripts /backup/minio/transcripts/

# Конфигурация
cp .env /backup/config/env_$(date +%Y%m%d)
```

---

**🎉 Развертывание завершено! Система готова к продакшн использованию.**

### 📞 Поддержка
- Логи: `/var/log/aisha_v2/`
- Статус сервисов: `systemctl status aisha-*`
- Мониторинг: Health check endpoints
- Документация: `/opt/aisha_v2/docs/` 