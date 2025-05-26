#!/bin/bash
#
# Скрипт автоматического развертывания Aisha Bot в продакшн (минимальная версия)
# Frontend: /opt/aisha-frontend, Backend: /opt/aisha-backend
# Пользователь: aisha:aisha, с nginx для webhook (рекомендуемо)
# Внешние сервисы: PostgreSQL, Redis, MinIO
# Ubuntu 24.04 LTS
#

set -e  # Выход при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация (обновлено для новой архитектуры)
BACKEND_DIR="/opt/aisha-backend"
FRONTEND_DIR="/opt/aisha-frontend" 
PROJECT_USER="aisha"
PYTHON_VERSION="3.11"
WEBHOOK_PORT="8443"
API_PORT="8000"
USE_NGINX="true"  # Использовать nginx (рекомендуемо)

# Логирование
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Проверка запуска от root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Скрипт должен запускаться от root (sudo)"
    fi
}

# Проверка системы (обновлено для 5000+ пользователей)
check_system() {
    log "Проверка системных требований для 5000+ пользователей..."
    
    # Проверка Ubuntu версии
    if ! grep -q "Ubuntu 24.04" /etc/os-release; then
        warn "Рекомендуется Ubuntu 24.04 LTS"
    fi
    
    # Проверка RAM (минимум 4GB, рекомендуемо 8GB)
    total_ram=$(free -g | awk '/^Mem:/{print $2}')
    if [ $total_ram -lt 4 ]; then
        error "Требуется минимум 4 GB RAM (обнаружено: ${total_ram}GB)"
    elif [ $total_ram -lt 8 ]; then
        warn "Рекомендуется 8 GB RAM для 5000+ пользователей (обнаружено: ${total_ram}GB)"
    else
        info "✅ RAM: ${total_ram}GB - достаточно"
    fi
    
    # Проверка CPU
    cpu_cores=$(nproc)
    if [ $cpu_cores -lt 2 ]; then
        error "Требуется минимум 2 CPU cores (обнаружено: ${cpu_cores})"
    elif [ $cpu_cores -lt 4 ]; then
        warn "Рекомендуется 4 CPU cores для 5000+ пользователей (обнаружено: ${cpu_cores})"
    else
        info "✅ CPU: ${cpu_cores} cores - достаточно"
    fi
    
    # Проверка свободного места (минимум 50GB, рекомендуемо 100GB)
    free_space=$(df / | awk 'NR==2{print $4/1024/1024}')
    if (( $(echo "$free_space < 50" | bc -l) )); then
        error "Требуется минимум 50 GB свободного места"
    elif (( $(echo "$free_space < 100" | bc -l) )); then
        warn "Рекомендуется 100 GB для 5000+ пользователей"
    else
        info "✅ Диск: достаточно места"
    fi
    
    log "Системные требования проверены"
}

# Обновление системы
update_system() {
    log "Обновление системы Ubuntu 24.04..."
    apt update && apt upgrade -y
    apt install -y software-properties-common curl wget git bc
}

# Установка зависимостей
install_dependencies() {
    log "Установка системных зависимостей..."
    
    # Python и инструменты разработки
    apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev
    apt install -y build-essential libssl-dev libffi-dev libpq-dev
    
    # Nginx (для webhook)
    if [ "$USE_NGINX" = "true" ]; then
        apt install -y nginx
        info "✅ Nginx установлен для webhook"
    fi
    
    # PostgreSQL client (для подключения к внешней БД)
    apt install -y postgresql-client-16
    
    # Redis client (для подключения к внешнему Redis)
    apt install -y redis-tools
    
    # Инструменты мониторинга
    apt install -y htop iotop netstat ss ufw logrotate
    
    # Инструменты бэкапа и диагностики
    apt install -y rsync cron telnet jq tree
    
    log "Зависимости установлены"
}

# Создание пользователя
create_user() {
    log "Создание пользователя ${PROJECT_USER}..."
    
    if ! id "${PROJECT_USER}" &>/dev/null; then
        useradd -r -m -s /bin/bash ${PROJECT_USER}
        usermod -a -G ${PROJECT_USER} ${PROJECT_USER}
        log "Пользователь ${PROJECT_USER} создан"
    else
        warn "Пользователь ${PROJECT_USER} уже существует"
    fi
}

# Создание структуры каталогов
create_directories() {
    log "Создание структуры каталогов..."
    
    # Backend каталоги
    mkdir -p ${BACKEND_DIR}/{logs,ssl,scripts,data,backups}
    mkdir -p ${BACKEND_DIR}/logs/{bot,api}
    
    # Frontend каталоги (заготовка на будущее)
    mkdir -p ${FRONTEND_DIR}/{dist,assets,logs}
    
    # Системные каталоги
    mkdir -p /var/log/aisha
    mkdir -p /etc/aisha
    
    # Установка прав
    chown -R ${PROJECT_USER}:${PROJECT_USER} ${BACKEND_DIR}
    chown -R ${PROJECT_USER}:${PROJECT_USER} ${FRONTEND_DIR}
    chown -R ${PROJECT_USER}:${PROJECT_USER} /var/log/aisha
    
    chmod 750 ${BACKEND_DIR}
    chmod 750 ${FRONTEND_DIR}
    chmod 755 /var/log/aisha
    
    log "Структура каталогов создана"
}

# Создание конфигурации (обновлено)
create_config() {
    log "Создание конфигурации..."
    
    # Основной .env файл
    sudo -u ${PROJECT_USER} tee ${BACKEND_DIR}/.env << 'EOF'
# ===============================
# Aisha Bot Configuration
# ===============================

# Database (ВНЕШНИЙ СЕРВЕР - ЗАПОЛНИТЕ)
DATABASE_URL=postgresql+asyncpg://username:password@your-postgres-server:5432/aisha_bot_prod

# Redis (ВНЕШНИЙ СЕРВЕР - ЗАПОЛНИТЕ)
REDIS_URL=redis://your-redis-server:6379/0

# MinIO Storage (ВНЕШНИЙ СЕРВЕР - ЗАПОЛНИТЕ)
MINIO_ENDPOINT=your-minio-server:9000
MINIO_ACCESS_KEY=your-minio-access-key
MINIO_SECRET_KEY=your-minio-secret-key
MINIO_BUCKET_PREFIX=aisha-bot
MINIO_SECURE=true
MINIO_PRESIGNED_EXPIRES=3600

# MinIO Buckets
MINIO_BUCKETS={"avatars": "aisha-avatars", "transcripts": "aisha-transcripts", "generated": "aisha-generated"}

# Telegram Bot (ЗАПОЛНИТЕ)
TELEGRAM_TOKEN=
TELEGRAM_WEBHOOK_URL=https://aibots.kz:8443/webhook

# FAL AI (ЗАПОЛНИТЕ)
FAL_API_KEY=
FAL_WEBHOOK_URL=https://aibots.kz:8443/api/v1/avatar/status_update
FAL_WEBHOOK_SECRET=  # Необязательно - дополнительная безопасность
AVATAR_TEST_MODE=false

# Performance (оптимизировано для 5000+ пользователей)
MAX_WORKERS=4
BATCH_SIZE=50
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Storage (локальное дублирование)
STORAGE_PATH=/opt/aisha-backend/data
TEMP_PATH=/opt/aisha-backend/temp

# Logging
LOG_LEVEL=INFO
LOG_MAX_BYTES=50000000
LOG_BACKUP_COUNT=10

# Security (ЗАПОЛНИТЕ)
ADMIN_USER_IDS=

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Health Check
HEALTH_CHECK_INTERVAL=300
HEALTH_CHECK_TIMEOUT=30
EOF

    # API Server .env (если используется nginx)
    if [ "$USE_NGINX" = "true" ]; then
        sudo -u ${PROJECT_USER} mkdir -p ${BACKEND_DIR}/api_server
        sudo -u ${PROJECT_USER} tee ${BACKEND_DIR}/api_server/.env << 'EOF'
# ===============================
# API Server Configuration (за nginx)
# ===============================

# API Server (локальный, nginx делает SSL termination)
API_HOST=127.0.0.1
API_PORT=8000
SSL_ENABLED=false

# Database (ВНЕШНИЙ СЕРВЕР - ЗАПОЛНИТЕ)
DATABASE_URL=postgresql+asyncpg://username:password@your-postgres-server:5432/aisha_bot_prod

# Telegram (ЗАПОЛНИТЕ)
TELEGRAM_TOKEN=

# FAL AI (дополнительная безопасность)
FAL_WEBHOOK_SECRET=  # Необязательно

# Security
LOG_LEVEL=INFO
EOF
    else
        # Прямой SSL (без nginx)
        sudo -u ${PROJECT_USER} mkdir -p ${BACKEND_DIR}/api_server
        sudo -u ${PROJECT_USER} tee ${BACKEND_DIR}/api_server/.env << 'EOF'
# ===============================
# API Server Configuration (прямой SSL)
# ===============================

# API Server (прямой SSL)
API_HOST=0.0.0.0
API_PORT=8443
SSL_ENABLED=true
SSL_CERT_PATH=ssl/aibots_kz.crt
SSL_KEY_PATH=ssl/aibots.kz.key

# Database (ВНЕШНИЙ СЕРВЕР - ЗАПОЛНИТЕ)
DATABASE_URL=postgresql+asyncpg://username:password@your-postgres-server:5432/aisha_bot_prod

# Telegram (ЗАПОЛНИТЕ)
TELEGRAM_TOKEN=

# FAL AI (дополнительная безопасность)
FAL_WEBHOOK_SECRET=  # Необязательно

# Security
LOG_LEVEL=INFO
EOF
    fi
    
    # Права доступа
    chmod 600 ${BACKEND_DIR}/.env
    chmod 600 ${BACKEND_DIR}/api_server/.env
    
    log "Конфигурация создана"
}

# Конфигурация nginx (если используется)
setup_nginx() {
    if [ "$USE_NGINX" = "true" ]; then
        log "Настройка nginx для webhook..."
        
        cat > /etc/nginx/sites-available/aisha-webhook << 'EOF'
upstream aisha_api {
    server 127.0.0.1:8000;
}

# Rate limiting для защиты
limit_req_zone $binary_remote_addr zone=webhook:10m rate=10r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

server {
    listen 8443 ssl http2;
    server_name aibots.kz;
    
    # SSL сертификаты
    ssl_certificate /opt/aisha-backend/ssl/aibots_kz.crt;
    ssl_certificate_key /opt/aisha-backend/ssl/aibots.kz.key;
    
    # SSL конфигурация
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Webhook endpoint (ограниченный доступ)
    location /api/v1/avatar/status_update {
        limit_req zone=webhook burst=5 nodelay;
        
        # Только POST запросы
        if ($request_method != POST) {
            return 405;
        }
        
        proxy_pass http://aisha_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
        
        # Специальное логирование webhook
        access_log /var/log/aisha/webhook_access.log;
        error_log /var/log/aisha/webhook_error.log;
    }
    
    # Health check endpoint
    location /health {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://aisha_api;
    }
    
    # Status endpoint
    location /status {
        limit_req zone=api burst=5 nodelay;
        proxy_pass http://aisha_api;
    }
    
    # Блокировка всех остальных запросов
    location / {
        return 404;
    }
    
    # Основное логирование
    access_log /var/log/aisha/nginx_access.log;
    error_log /var/log/aisha/nginx_error.log;
}
EOF
        
        # Активация конфигурации
        ln -sf /etc/nginx/sites-available/aisha-webhook /etc/nginx/sites-enabled/
        rm -f /etc/nginx/sites-enabled/default
        
        # Проверка конфигурации (отложенная - после копирования SSL)
        # nginx -t
        
        log "Nginx сконфигурирован (проверка после копирования SSL)"
    else
        info "Nginx пропущен - используется прямой SSL"
    fi
}

# Создание systemd сервисов (обновлено)
create_services() {
    log "Создание systemd сервисов..."
    
    # Aisha Bot сервис
    tee /etc/systemd/system/aisha-bot.service << EOF
[Unit]
Description=Aisha Telegram Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${PROJECT_USER}
Group=${PROJECT_USER}
WorkingDirectory=${BACKEND_DIR}
Environment=PATH=${BACKEND_DIR}/.venv/bin
ExecStart=${BACKEND_DIR}/.venv/bin/python -m app.main
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10

# Ограничения ресурсов (для 5000+ пользователей)
MemoryLimit=3G
CPUQuota=200%

# Безопасность
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${BACKEND_DIR}/logs ${BACKEND_DIR}/data /var/log/aisha
ReadOnlyPaths=${BACKEND_DIR}

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aisha-bot

[Install]
WantedBy=multi-user.target
EOF

    # Aisha API сервис
    tee /etc/systemd/system/aisha-api.service << EOF
[Unit]
Description=Aisha API Server (Webhook)
After=network.target aisha-bot.service
Wants=aisha-bot.service

[Service]
Type=simple
User=${PROJECT_USER}
Group=${PROJECT_USER}
WorkingDirectory=${BACKEND_DIR}/api_server
Environment=PATH=${BACKEND_DIR}/.venv/bin
ExecStart=${BACKEND_DIR}/.venv/bin/python run_api_server.py
Restart=always
RestartSec=5

# Ограничения ресурсов (для API сервера)
MemoryLimit=1G
CPUQuota=50%

# Безопасность
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${BACKEND_DIR}/logs /var/log/aisha

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aisha-api

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable aisha-bot.service
    systemctl enable aisha-api.service
    
    if [ "$USE_NGINX" = "true" ]; then
        systemctl enable nginx
    fi
    
    log "Systemd сервисы созданы"
}

# Настройка мониторинга (обновлено)
setup_monitoring() {
    log "Настройка мониторинга..."
    
    # Health check скрипт
    tee ${BACKEND_DIR}/scripts/health_check.sh << 'EOF'
#!/bin/bash
# Health check для Aisha Bot

check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        echo "✅ $service: активен"
        return 0
    else
        echo "❌ $service: неактивен"
        systemctl restart $service
        return 1
    fi
}

check_port() {
    local port=$1
    local name=$2
    if ss -tuln | grep -q ":$port "; then
        echo "✅ $name (порт $port): доступен"
        return 0
    else
        echo "❌ $name (порт $port): недоступен"
        return 1
    fi
}

check_external_connection() {
    local service=$1
    local host=$2
    local port=$3
    
    if timeout 5 telnet $host $port >/dev/null 2>&1; then
        echo "✅ $service ($host:$port): подключение успешно"
        return 0
    else
        echo "❌ $service ($host:$port): подключение неудачно"
        return 1
    fi
}

echo "=== Health Check Aisha Bot ==="
echo "Время: $(date)"
echo

# Проверка сервисов
check_service aisha-bot
check_service aisha-api
if systemctl is-enabled nginx >/dev/null 2>&1; then
    check_service nginx
fi

echo

# Проверка портов
check_port 8443 "Webhook HTTPS"
check_port 8000 "API Server (internal)"

echo

# Проверка ресурсов
echo "=== Ресурсы системы ==="
echo "Место на диске:"
df -h /opt/aisha-backend | tail -1

echo
echo "Использование памяти:"
free -h

echo
echo "Нагрузка CPU:"
uptime

# Проверка внешних подключений (если настроены)
if [ -f "/opt/aisha-backend/.env" ]; then
    source /opt/aisha-backend/.env
    
    echo
    echo "=== Внешние подключения ==="
    
    # Извлекаем хосты из URL
    if [[ $DATABASE_URL =~ @([^:]+):([0-9]+) ]]; then
        check_external_connection "PostgreSQL" ${BASH_REMATCH[1]} ${BASH_REMATCH[2]}
    fi
    
    if [[ $REDIS_URL =~ //([^:]+):([0-9]+) ]]; then
        REDIS_HOST=${BASH_REMATCH[1]}
        REDIS_PORT=${BASH_REMATCH[2]}
        check_external_connection "Redis" $REDIS_HOST $REDIS_PORT
    fi
    
    if [[ $MINIO_ENDPOINT =~ ([^:]+):([0-9]+) ]]; then
        MINIO_HOST=${BASH_REMATCH[1]}
        MINIO_PORT=${BASH_REMATCH[2]}
        check_external_connection "MinIO" $MINIO_HOST $MINIO_PORT
    fi
fi

echo "=== Конец проверки ==="
EOF

    # Backup скрипт (только конфигурация и логи)
    tee ${BACKEND_DIR}/scripts/backup.sh << 'EOF'
#!/bin/bash
# Backup скрипт для Aisha Bot

BACKUP_DIR="/opt/aisha-backend/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="aisha_backup_$DATE"

echo "$(date): Создание backup: $BACKUP_NAME"

# Создание архива конфигурации и логов
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='backups' \
    --exclude='temp' \
    /opt/aisha-backend/.env \
    /opt/aisha-backend/api_server/.env \
    /opt/aisha-backend/logs \
    /etc/systemd/system/aisha-*.service \
    /etc/nginx/sites-available/aisha-webhook 2>/dev/null

echo "$(date): Backup создан: $BACKUP_DIR/$BACKUP_NAME.tar.gz"

# Удаление старых backup'ов (старше 30 дней)
find $BACKUP_DIR -name "aisha_backup_*.tar.gz" -mtime +30 -delete

echo "$(date): Старые backup'ы очищены"
EOF

    chmod +x ${BACKEND_DIR}/scripts/*.sh
    chown -R ${PROJECT_USER}:${PROJECT_USER} ${BACKEND_DIR}/scripts/
    
    # Добавление в cron
    cat > /etc/cron.d/aisha-health << EOF
# Health check каждые 5 минут
*/5 * * * * ${PROJECT_USER} ${BACKEND_DIR}/scripts/health_check.sh >> /var/log/aisha/health_check.log 2>&1
EOF

    cat > /etc/cron.d/aisha-backup << EOF
# Ежедневный backup в 2:00
0 2 * * * ${PROJECT_USER} ${BACKEND_DIR}/scripts/backup.sh >> /var/log/aisha/backup.log 2>&1
EOF
    
    log "Мониторинг настроен"
}

# Настройка logrotate (обновлено)
setup_logrotate() {
    log "Настройка ротации логов..."
    
    tee /etc/logrotate.d/aisha << EOF
/var/log/aisha/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ${PROJECT_USER} ${PROJECT_USER}
    postrotate
        systemctl reload nginx 2>/dev/null || true
        systemctl restart aisha-bot 2>/dev/null || true
        systemctl restart aisha-api 2>/dev/null || true
    endscript
}

${BACKEND_DIR}/logs/*/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 ${PROJECT_USER} ${PROJECT_USER}
}
EOF

    log "Ротация логов настроена"
}

# Настройка firewall (обновлено)
setup_firewall() {
    log "Настройка UFW firewall..."
    
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # SSH доступ
    ufw allow ssh
    
    # Webhook порт (только HTTPS)
    ufw allow ${WEBHOOK_PORT}/tcp comment "Aisha Webhook HTTPS"
    
    # Внутренние порты (только localhost)
    ufw allow from 127.0.0.1 to any port ${API_PORT}
    
    # Включение firewall
    ufw --force enable
    
    log "Firewall настроен"
}

# Создание скрипта проверки подключений (обновлено)
create_connection_test() {
    log "Создание скрипта проверки подключений..."
    
    tee ${BACKEND_DIR}/scripts/test_connections.sh << 'EOF'
#!/bin/bash

echo "🔍 Проверка подключений к внешним сервисам..."

# Функция проверки подключения
test_connection() {
    local service=$1
    local host=$2
    local port=$3
    
    if timeout 5 telnet $host $port >/dev/null 2>&1; then
        echo "✅ $service ($host:$port) - подключение успешно"
        return 0
    else
        echo "❌ $service ($host:$port) - подключение неудачно"
        return 1
    fi
}

# Получаем настройки из .env
if [ -f "/opt/aisha-backend/.env" ]; then
    source /opt/aisha-backend/.env
    
    echo "📊 Тестирование внешних сервисов..."
    
    # Извлекаем хосты из URL
    if [[ $DATABASE_URL =~ @([^:]+):([0-9]+) ]]; then
        PG_HOST=${BASH_REMATCH[1]}
        PG_PORT=${BASH_REMATCH[2]}
        test_connection "PostgreSQL" $PG_HOST $PG_PORT
    fi
    
    if [[ $REDIS_URL =~ //([^:]+):([0-9]+) ]]; then
        REDIS_HOST=${BASH_REMATCH[1]}
        REDIS_PORT=${BASH_REMATCH[2]}
        test_connection "Redis" $REDIS_HOST $REDIS_PORT
    fi
    
    if [[ $MINIO_ENDPOINT =~ ([^:]+):([0-9]+) ]]; then
        MINIO_HOST=${BASH_REMATCH[1]}
        MINIO_PORT=${BASH_REMATCH[2]}
        test_connection "MinIO" $MINIO_HOST $MINIO_PORT
    fi
    
    echo
    echo "🔧 Команды для тестирования функциональности:"
    echo "   redis-cli -h \$REDIS_HOST ping"
    echo "   psql \$DATABASE_URL -c 'SELECT 1;'"
    echo "   curl -k https://\$MINIO_ENDPOINT/minio/health/live"
else
    echo "❌ Файл конфигурации .env не найден"
fi
EOF

    chmod +x ${BACKEND_DIR}/scripts/test_connections.sh
    chown ${PROJECT_USER}:${PROJECT_USER} ${BACKEND_DIR}/scripts/test_connections.sh
    
    log "Скрипт проверки подключений создан"
}

# Финальная проверка (обновлено)
final_check() {
    log "Выполнение финальной проверки..."
    
    # Проверка структуры каталогов
    if [ -d "${BACKEND_DIR}" ]; then
        info "✅ Backend каталог создан"
    else
        error "❌ Backend каталог не найден"
    fi
    
    if [ -d "${FRONTEND_DIR}" ]; then
        info "✅ Frontend каталог создан"
    else
        warn "❌ Frontend каталог не найден"
    fi
    
    # Проверка конфигурации
    if [ -f "${BACKEND_DIR}/.env" ]; then
        info "✅ Backend конфигурация создана"
    else
        error "❌ Backend конфигурация не найдена"
    fi
    
    if [ -f "${BACKEND_DIR}/api_server/.env" ]; then
        info "✅ API Server конфигурация создана"
    else
        error "❌ API Server конфигурация не найдена"
    fi
    
    # Проверка systemd сервисов
    if [ -f "/etc/systemd/system/aisha-bot.service" ]; then
        info "✅ Systemd сервис бота создан"
    else
        error "❌ Systemd сервис бота не найден"
    fi
    
    if [ -f "/etc/systemd/system/aisha-api.service" ]; then
        info "✅ Systemd сервис API создан"
    else
        error "❌ Systemd сервис API не найден"
    fi
    
    # Проверка nginx
    if [ "$USE_NGINX" = "true" ]; then
        if [ -f "/etc/nginx/sites-available/aisha-webhook" ]; then
            info "✅ Nginx конфигурация создана"
        else
            error "❌ Nginx конфигурация не найдена"
        fi
    fi
    
    log "Финальная проверка завершена"
}

# Главная функция
main() {
    log "🚀 Начинаем развертывание Aisha Bot (минимальная версия)..."
    log "📁 Frontend: ${FRONTEND_DIR}"
    log "📁 Backend: ${BACKEND_DIR}"
    log "👤 Пользователь: ${PROJECT_USER}"
    log "🌐 Nginx: $([ "$USE_NGINX" = "true" ] && echo "включен" || echo "отключен")"
    
    check_root
    check_system
    update_system
    install_dependencies
    create_user
    create_directories
    create_config
    setup_nginx
    create_services
    setup_monitoring
    setup_logrotate
    setup_firewall
    create_connection_test
    final_check
    
    log "🎉 Минимальное развертывание завершено!"
    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN} СЛЕДУЮЩИЕ ШАГИ ДЛЯ ЗАВЕРШЕНИЯ:${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    echo "1. 📁 Скопируйте код проекта:"
    echo "   sudo rsync -av --exclude='.git' --exclude='__pycache__' --exclude='temp' --exclude='*.log' --exclude='archive' --exclude='.venv' ./ ${BACKEND_DIR}/"
    echo "   sudo chown -R ${PROJECT_USER}:${PROJECT_USER} ${BACKEND_DIR}/"
    echo
    echo "2. 🔐 Скопируйте SSL сертификаты:"
    echo "   sudo cp ssl_certificate/* ${BACKEND_DIR}/ssl/"
    echo "   sudo chown ${PROJECT_USER}:${PROJECT_USER} ${BACKEND_DIR}/ssl/*"
    echo "   sudo chmod 600 ${BACKEND_DIR}/ssl/*.key"
    echo "   sudo chmod 644 ${BACKEND_DIR}/ssl/*.crt"
    echo
    echo "3. 📝 Заполните конфигурацию:"
    echo "   sudo nano ${BACKEND_DIR}/.env"
    echo "   sudo nano ${BACKEND_DIR}/api_server/.env"
    echo
    echo "4. 📦 Установите зависимости Python:"
    echo "   sudo -u ${PROJECT_USER} bash"
    echo "   cd ${BACKEND_DIR}"
    echo "   python${PYTHON_VERSION} -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    echo
    if [ "$USE_NGINX" = "true" ]; then
        echo "5. ✅ Проверьте nginx конфигурацию:"
        echo "   sudo nginx -t"
        echo
    fi
    echo "6. 🔍 Проверьте подключения к внешним сервисам:"
    echo "   sudo -u ${PROJECT_USER} ${BACKEND_DIR}/scripts/test_connections.sh"
    echo
    echo "7. 🗄️ Выполните миграции БД (если нужно):"
    echo "   cd ${BACKEND_DIR} && source .venv/bin/activate"
    echo "   alembic upgrade head"
    echo
    echo "8. 🚀 Запустите сервисы:"
    if [ "$USE_NGINX" = "true" ]; then
        echo "   sudo systemctl restart nginx"
    fi
    echo "   sudo systemctl start aisha-bot"
    echo "   sudo systemctl start aisha-api"
    echo
    echo "9. ✅ Проверьте статус:"
    echo "   sudo systemctl status aisha-bot aisha-api$([ "$USE_NGINX" = "true" ] && echo " nginx")"
    echo
    echo -e "${YELLOW}📊 МОНИТОРИНГ:${NC}"
    echo "   Health check: tail -f /var/log/aisha/health_check.log"
    echo "   Bot логи: sudo journalctl -fu aisha-bot"
    echo "   API логи: sudo journalctl -fu aisha-api"
    if [ "$USE_NGINX" = "true" ]; then
        echo "   Webhook логи: tail -f /var/log/aisha/webhook_access.log"
    fi
    echo "   Подключения: sudo -u ${PROJECT_USER} ${BACKEND_DIR}/scripts/test_connections.sh"
    echo
    echo -e "${BLUE}🌐 WEBHOOK URL:${NC}"
    echo "   https://aibots.kz:8443/api/v1/avatar/status_update"
    echo
    echo -e "${RED}⚠️  ОБЯЗАТЕЛЬНО НАСТРОЙТЕ:${NC}"
    echo "   - DATABASE_URL (ваш PostgreSQL сервер)"
    echo "   - REDIS_URL (ваш Redis сервер)"  
    echo "   - MINIO_* настройки (ваш MinIO сервер)"
    echo "   - TELEGRAM_TOKEN и FAL_API_KEY"
    echo
    echo -e "${BLUE}📝 НЕОБЯЗАТЕЛЬНЫЕ НАСТРОЙКИ:${NC}"
    echo "   - FAL_WEBHOOK_SECRET (дополнительная безопасность)"
    echo
    echo -e "${BLUE}💡 ВНЕШНИЕ ТРЕБОВАНИЯ:${NC}"
    echo "   PostgreSQL: database 'aisha_bot_prod' с пользователем"
    echo "   Redis: доступный экземпляр на порту 6379"
    echo "   MinIO: buckets 'aisha-avatars', 'aisha-transcripts', 'aisha-generated'"
}

# Запуск
main "$@" 