# 🚀 Продакшн развертывание Aisha Bot

## 📊 Системные требования для ~5000 пользователей

### 🖥️ Минимальные требования
- **CPU**: 4 cores (8 threads)
- **RAM**: 8 GB
- **SSD**: 100 GB
- **Network**: 1 Gbps

### 💪 Рекомендуемые требования
- **CPU**: 8 cores (16 threads) 
- **RAM**: 16 GB
- **SSD**: 200 GB (NVMe)
- **Network**: 1 Gbps+

### 🗄️ База данных PostgreSQL
- **RAM**: 4-6 GB для PostgreSQL
- **CPU**: 2-4 dedicated cores
- **Storage**: 50 GB SSD (с учетом роста)
- **Connections**: max_connections = 200

## 🏗️ Архитектура развертывания

```
┌─────────────────────────────────────────┐
│                Server                   │
├─────────────────────────────────────────┤
│  🤖 Telegram Bot (Port: Internal)      │
│  📡 API Server (Port: 8443 HTTPS)      │  
│  🗄️ PostgreSQL (Port: 5432)           │
│  🔄 Nginx Proxy (Port: 80/443)         │
│  📊 Monitoring (Optional)               │
└─────────────────────────────────────────┘
```

## 📁 Структура проекта в продакшн

```bash
/opt/aisha_bot/
├── app/                    # Основной бот
├── api_server/            # Webhook API  
├── storage/               # Пользовательские данные
├── logs/                  # Логи
├── backups/              # Резервные копии
├── .env                  # Продакшн конфиг
└── scripts/              # Служебные скрипты
```

## 🔧 Подготовка системы

### 1. Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y postgresql-16 postgresql-contrib
sudo apt install -y nginx certbot python3-certbot-nginx
sudo apt install -y htop iotop git curl wget
```

### 2. Создание пользователя
```bash
sudo useradd -m -s /bin/bash aisha
sudo usermod -aG sudo aisha
sudo mkdir -p /opt/aisha_bot
sudo chown -R aisha:aisha /opt/aisha_bot
```

### 3. Настройка PostgreSQL
```bash
sudo -u postgres createuser --createdb aisha
sudo -u postgres createdb aisha_bot_prod -O aisha
sudo -u postgres psql -c "ALTER USER aisha PASSWORD 'secure_password_here';"

# Настройка postgresql.conf
sudo nano /etc/postgresql/16/main/postgresql.conf
```

### PostgreSQL конфигурация для продакшн:
```ini
# postgresql.conf
max_connections = 200
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB
```

## 🚀 Установка приложения

### 1. Клонирование и настройка
```bash
sudo -u aisha bash
cd /opt/aisha_bot
git clone <your-repo> .
python3.11 -m venv venv
source venv/bin/activate

# Основной бот
pip install -r requirements.txt

# API сервер  
cd api_server
pip install -r requirements.txt
cd ..
```

### 2. Продакшн конфигурация
```bash
# Основной .env файл
cat > /opt/aisha_bot/.env << 'EOF'
# Database
DATABASE_URL=postgresql+asyncpg://aisha:secure_password_here@localhost/aisha_bot_prod

# Telegram
TELEGRAM_TOKEN=your_bot_token_here

# FAL AI
FAL_API_KEY=your_fal_api_key
FAL_WEBHOOK_URL=https://aibots.kz:8443/api/v1/avatar/status_update
AVATAR_TEST_MODE=false

# Storage
STORAGE_PATH=/opt/aisha_bot/storage

# Logs
LOG_LEVEL=INFO
LOG_MAX_BYTES=50000000
LOG_BACKUP_COUNT=10

# Redis (если используется)
REDIS_URL=redis://localhost:6379/0

# Security
ALLOWED_USERS=
ADMIN_USER_IDS=123456789

# Performance
MAX_WORKERS=4
BATCH_SIZE=100
EOF

# API Server .env
cat > /opt/aisha_bot/api_server/.env << 'EOF'
# API Server
API_HOST=0.0.0.0
API_PORT=8443
SSL_ENABLED=true
SSL_CERT_PATH=ssl/aibots_kz.crt
SSL_KEY_PATH=ssl/aibots.kz.key

# Database
DATABASE_URL=postgresql+asyncpg://aisha:secure_password_here@localhost/aisha_bot_prod

# Telegram
TELEGRAM_TOKEN=your_bot_token_here

# Security
LOG_LEVEL=INFO
ALLOWED_IPS=["185.199.108.0/22", "140.82.112.0/20"]
EOF
```

## 🔄 Systemd Unit файлы

### 1. Основной Telegram бот
```bash
sudo tee /etc/systemd/system/aisha-bot.service << 'EOF'
[Unit]
Description=Aisha Telegram Bot
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=aisha
Group=aisha
WorkingDirectory=/opt/aisha_bot
Environment=PATH=/opt/aisha_bot/venv/bin
ExecStart=/opt/aisha_bot/venv/bin/python -m app.main
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aisha-bot

# Resource limits
LimitNOFILE=65536
MemoryMax=4G
CPUQuota=200%

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/aisha_bot/storage /opt/aisha_bot/logs
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
```

### 2. API Webhook сервер
```bash
sudo tee /etc/systemd/system/aisha-api.service << 'EOF'
[Unit]
Description=Aisha Bot FAL Webhook API Server
After=network.target postgresql.service aisha-bot.service
Wants=postgresql.service

[Service]
Type=simple
User=aisha
Group=aisha
WorkingDirectory=/opt/aisha_bot/api_server
Environment=PATH=/opt/aisha_bot/venv/bin
ExecStart=/opt/aisha_bot/venv/bin/python run_api_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aisha-api

# Resource limits
LimitNOFILE=4096
MemoryMax=2G
CPUQuota=100%

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/aisha_bot/api_server/logs
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
```

### 3. Активация сервисов
```bash
sudo systemctl daemon-reload
sudo systemctl enable aisha-bot.service
sudo systemctl enable aisha-api.service

# Запуск
sudo systemctl start aisha-bot
sudo systemctl start aisha-api

# Проверка статуса
sudo systemctl status aisha-bot
sudo systemctl status aisha-api
```

## 🔧 Настройка Nginx (опционально)

### Конфигурация для домена
```bash
sudo tee /etc/nginx/sites-available/aisha-bot << 'EOF'
server {
    listen 80;
    server_name aibots.kz www.aibots.kz;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aibots.kz www.aibots.kz;

    # SSL Configuration
    ssl_certificate /opt/aisha_bot/api_server/ssl/aibots_kz.crt;
    ssl_certificate_key /opt/aisha_bot/api_server/ssl/aibots.kz.key;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # API Server proxy (webhook)
    location /api/ {
        proxy_pass https://127.0.0.1:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Webhook specific
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
    }

    # Health check
    location /health {
        proxy_pass https://127.0.0.1:8443/health;
        access_log off;
    }

    # Default response
    location / {
        return 200 'Aisha Bot API Running';
        add_header Content-Type text/plain;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/aisha-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 📊 Мониторинг и логирование

### 1. Настройка logrotate
```bash
sudo tee /etc/logrotate.d/aisha-bot << 'EOF'
/opt/aisha_bot/logs/*.log
/opt/aisha_bot/api_server/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 644 aisha aisha
    postrotate
        systemctl reload aisha-bot
        systemctl reload aisha-api
    endscript
}
EOF
```

### 2. Мониторинг скрипт
```bash
sudo tee /opt/aisha_bot/scripts/health_check.sh << 'EOF'
#!/bin/bash

# Проверка статуса сервисов
systemctl is-active aisha-bot >/dev/null 2>&1 || {
    echo "$(date): aisha-bot service is down" >> /var/log/aisha-health.log
    systemctl restart aisha-bot
}

systemctl is-active aisha-api >/dev/null 2>&1 || {
    echo "$(date): aisha-api service is down" >> /var/log/aisha-health.log  
    systemctl restart aisha-api
}

# Проверка endpoint
curl -f https://aibots.kz:8443/health >/dev/null 2>&1 || {
    echo "$(date): API health check failed" >> /var/log/aisha-health.log
}

# Проверка места на диске
DISK_USAGE=$(df /opt/aisha_bot | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "$(date): Disk usage is ${DISK_USAGE}%" >> /var/log/aisha-health.log
fi
EOF

chmod +x /opt/aisha_bot/scripts/health_check.sh

# Добавляем в crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/aisha_bot/scripts/health_check.sh") | crontab -
```

## 🔐 Безопасность

### 1. Firewall настройка
```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH
sudo ufw allow 22/tcp

# HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# API Server (только для FAL AI)
sudo ufw allow from 185.199.108.0/22 to any port 8443
sudo ufw allow from 140.82.112.0/20 to any port 8443

# PostgreSQL (только локально)
sudo ufw deny 5432/tcp
```

### 2. SSL сертификаты
```bash
# Копируем сертификаты
sudo cp /path/to/ssl/* /opt/aisha_bot/api_server/ssl/
sudo chown -R aisha:aisha /opt/aisha_bot/api_server/ssl/
sudo chmod 600 /opt/aisha_bot/api_server/ssl/*.key
sudo chmod 644 /opt/aisha_bot/api_server/ssl/*.crt
```

## 💾 Резервное копирование

### 1. Скрипт бэкапа
```bash
sudo tee /opt/aisha_bot/scripts/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/aisha_bot/backups"
DATE=$(date +"%Y%m%d_%H%M%S")

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U aisha aisha_bot_prod | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Application data backup
tar czf $BACKUP_DIR/storage_$DATE.tar.gz /opt/aisha_bot/storage/

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "$(date): Backup completed - $DATE" >> /var/log/aisha-backup.log
EOF

chmod +x /opt/aisha_bot/scripts/backup.sh

# Ежедневный бэкап в 2:00
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/aisha_bot/scripts/backup.sh") | crontab -
```

## 📈 Производительность и масштабирование

### 1. Оптимизация для нагрузки
```python
# В app/core/config.py добавить
TELEGRAM_WORKERS = 8  # Для обработки сообщений
DB_POOL_SIZE = 20     # Размер пула соединений
DB_MAX_OVERFLOW = 30  # Максимальные дополнительные соединения
REQUEST_TIMEOUT = 30  # Таймаут запросов к FAL AI
BATCH_PROCESSING_SIZE = 50  # Размер батча для массовых операций
```

### 2. Мониторинг ресурсов
```bash
# CPU и Memory мониторинг
echo "*/2 * * * * iostat 1 1 | tail -n +4 >> /var/log/aisha-perf.log" | crontab -

# Process monitoring
echo "*/5 * * * * ps aux | grep -E '(aisha|python)' >> /var/log/aisha-processes.log" | crontab -
```

## 🚀 Чек-лист развертывания

### ✅ Предварительные проверки
- [ ] Системные требования соблюдены
- [ ] PostgreSQL настроен и работает  
- [ ] SSL сертификаты скопированы и корректны
- [ ] Переменные окружения настроены
- [ ] Права доступа настроены

### ✅ Развертывание
- [ ] Приложение установлено
- [ ] Зависимости установлены
- [ ] Миграции базы данных выполнены
- [ ] Unit файлы созданы и активированы
- [ ] Сервисы запущены

### ✅ Тестирование
- [ ] Telegram бот отвечает на команды
- [ ] API Server доступен (health check)
- [ ] Webhook принимает запросы
- [ ] SSL работает корректно
- [ ] Логи пишутся

### ✅ Мониторинг
- [ ] Health check скрипт настроен
- [ ] Резервное копирование настроено
- [ ] Логи ротируются
- [ ] Firewall настроен

## 📞 Поддержка и отладка

### Полезные команды
```bash
# Логи сервисов
sudo journalctl -fu aisha-bot
sudo journalctl -fu aisha-api

# Логи приложения
tail -f /opt/aisha_bot/logs/bot.log
tail -f /opt/aisha_bot/api_server/logs/webhook.log

# Проверка портов
sudo netstat -tlnp | grep -E "(8443|5432)"

# Проверка ресурсов
htop
iotop
df -h
```

### Типичные проблемы
1. **SSL ошибки** - Проверить права на файлы сертификатов
2. **База данных недоступна** - Проверить подключение и пароли
3. **Высокая нагрузка** - Увеличить worker'ы и память
4. **Переполнение диска** - Настроить ротацию логов 