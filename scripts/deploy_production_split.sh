#!/bin/bash
#
# Скрипт развертывания Aisha Bot с разделением frontend/backend
# Frontend: /opt/aisha-frontend, Backend: /opt/aisha-backend
# Пользователь: aisha:aisha, с nginx для webhook
# Ubuntu 24.04 LTS
#

set -e  # Выход при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
BACKEND_DIR="/opt/aisha-backend"
FRONTEND_DIR="/opt/aisha-frontend"
PROJECT_USER="aisha"
PYTHON_VERSION="3.11"
WEBHOOK_PORT="8443"
API_PORT="8000"
BOT_PORT="8001"

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
        error "Скрипт должен запускаться от имени root (sudo)"
    fi
}

# Обновление системы
update_system() {
    log "Обновление системы Ubuntu 24.04..."
    apt update && apt upgrade -y
    apt install -y software-properties-common curl wget git
}

# Установка зависимостей
install_dependencies() {
    log "Установка основных зависимостей..."
    
    # Python и инструменты разработки
    apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev
    apt install -y build-essential libssl-dev libffi-dev
    
    # Nginx
    apt install -y nginx
    
    # Инструменты мониторинга
    apt install -y htop iostat netstat ss ufw logrotate
    
    # Инструменты бэкапа
    apt install -y rsync cron
    
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
    mkdir -p ${BACKEND_DIR}/logs/{bot,api,nginx}
    
    # Frontend каталоги (если потребуется)
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

# Копирование SSL сертификатов
setup_ssl() {
    log "Настройка SSL сертификатов..."
    
    if [[ -d "ssl_certificate" ]]; then
        cp ssl_certificate/* ${BACKEND_DIR}/ssl/
        chown ${PROJECT_USER}:${PROJECT_USER} ${BACKEND_DIR}/ssl/*
        chmod 600 ${BACKEND_DIR}/ssl/*.key
        chmod 644 ${BACKEND_DIR}/ssl/*.crt
        chmod 644 ${BACKEND_DIR}/ssl/*.ca-bundle
        log "SSL сертификаты скопированы"
    else
        warn "Каталог ssl_certificate не найден. SSL нужно настроить вручную."
    fi
}

# Копирование проекта
deploy_backend() {
    log "Развертывание backend приложения..."
    
    # Копирование файлов (исключая ненужные)
    rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
          --exclude='temp' --exclude='.pytest_cache' --exclude='*.log' \
          --exclude='archive' --exclude='.venv' \
          ./ ${BACKEND_DIR}/
    
    # Удаление временных файлов если попали
    find ${BACKEND_DIR} -name "*.pyc" -delete
    find ${BACKEND_DIR} -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Установка прав
    chown -R ${PROJECT_USER}:${PROJECT_USER} ${BACKEND_DIR}
    chmod +x ${BACKEND_DIR}/scripts/*.sh
    
    log "Backend приложение развернуто"
}

# Создание виртуального окружения
setup_virtualenv() {
    log "Создание виртуального окружения Python..."
    
    sudo -u ${PROJECT_USER} python${PYTHON_VERSION} -m venv ${BACKEND_DIR}/.venv
    
    # Обновление pip и установка зависимостей
    sudo -u ${PROJECT_USER} ${BACKEND_DIR}/.venv/bin/pip install --upgrade pip
    sudo -u ${PROJECT_USER} ${BACKEND_DIR}/.venv/bin/pip install -r ${BACKEND_DIR}/requirements.txt
    
    log "Виртуальное окружение создано и зависимости установлены"
}

# Конфигурация nginx
setup_nginx() {
    log "Настройка nginx для webhook..."
    
    cat > /etc/nginx/sites-available/aisha-webhook << 'EOF'
upstream aisha_api {
    server 127.0.0.1:8000;
}

# Rate limiting
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
    
    # Webhook endpoint (ограниченный)
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
        
        # Логирование webhook запросов
        access_log /var/log/aisha/webhook_access.log;
        error_log /var/log/aisha/webhook_error.log;
    }
    
    # Health check endpoint
    location /health {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://aisha_api;
    }
    
    # Status endpoint (ограниченный)
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
    
    # Проверка конфигурации
    nginx -t
    
    log "Nginx сконфигурирован"
}

# Создание systemd сервисов
create_systemd_services() {
    log "Создание systemd сервисов..."
    
    # Aisha Bot сервис
    cat > /etc/systemd/system/aisha-bot.service << EOF
[Unit]
Description=Aisha Telegram Bot
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

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

# Ограничения ресурсов
MemoryLimit=2G
CPUQuota=200%

# Безопасность
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${BACKEND_DIR}/logs /var/log/aisha
ReadOnlyPaths=${BACKEND_DIR}

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aisha-bot

[Install]
WantedBy=multi-user.target
EOF

    # Aisha API сервис
    cat > /etc/systemd/system/aisha-api.service << EOF
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

# Ограничения ресурсов
MemoryLimit=1G
CPUQuota=100%

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
    
    # Перезагрузка systemd
    systemctl daemon-reload
    
    log "Systemd сервисы созданы"
}

# Настройка firewall
setup_firewall() {
    log "Настройка UFW firewall..."
    
    # Сброс правил
    ufw --force reset
    
    # Базовые правила
    ufw default deny incoming
    ufw default allow outgoing
    
    # SSH доступ
    ufw allow ssh
    
    # Webhook порт (только HTTPS)
    ufw allow ${WEBHOOK_PORT}/tcp comment "Aisha Webhook HTTPS"
    
    # Внутренние порты (только localhost)
    ufw allow from 127.0.0.1 to any port ${API_PORT}
    ufw allow from 127.0.0.1 to any port ${BOT_PORT}
    
    # Включение firewall
    ufw --force enable
    
    log "Firewall настроен"
}

# Настройка логирования
setup_logging() {
    log "Настройка логирования..."
    
    # Конфигурация logrotate
    cat > /etc/logrotate.d/aisha << EOF
/var/log/aisha/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ${PROJECT_USER} ${PROJECT_USER}
    postrotate
        systemctl reload nginx
        systemctl restart aisha-bot
        systemctl restart aisha-api
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
    
    log "Логирование настроено"
}

# Создание скриптов мониторинга
create_monitoring() {
    log "Создание скриптов мониторинга..."
    
    # Health check скрипт
    cat > ${BACKEND_DIR}/scripts/health_check.sh << 'EOF'
#!/bin/bash
# Health check для Aisha Bot

check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        echo "✅ $service: активен"
        return 0
    else
        echo "❌ $service: неактивен"
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

echo "=== Health Check Aisha Bot ==="
echo "Время: $(date)"
echo

# Проверка сервисов
check_service aisha-bot
check_service aisha-api
check_service nginx

echo

# Проверка портов
check_port 8443 "Webhook HTTPS"
check_port 8000 "API Server"

echo

# Проверка места на диске
echo "=== Место на диске ==="
df -h /opt/aisha-backend | tail -1

echo

# Проверка памяти
echo "=== Использование памяти ==="
free -h

echo "=== Конец проверки ==="
EOF

    chmod +x ${BACKEND_DIR}/scripts/health_check.sh
    chown ${PROJECT_USER}:${PROJECT_USER} ${BACKEND_DIR}/scripts/health_check.sh
    
    # Добавление в cron
    cat > /etc/cron.d/aisha-health << EOF
# Health check каждые 5 минут
*/5 * * * * ${PROJECT_USER} ${BACKEND_DIR}/scripts/health_check.sh >> ${BACKEND_DIR}/logs/health_check.log 2>&1
EOF
    
    log "Мониторинг настроен"
}

# Создание backup скрипта
create_backup() {
    log "Создание backup скрипта..."
    
    cat > ${BACKEND_DIR}/scripts/backup.sh << 'EOF'
#!/bin/bash
# Backup скрипт для Aisha Bot

BACKUP_DIR="/opt/aisha-backend/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="aisha_backup_$DATE"

echo "Создание backup: $BACKUP_NAME"

# Создание архива конфигурации
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='backups' \
    /opt/aisha-backend \
    /etc/systemd/system/aisha-*.service \
    /etc/nginx/sites-available/aisha-webhook

echo "Backup создан: $BACKUP_DIR/$BACKUP_NAME.tar.gz"

# Удаление старых backup'ов (старше 30 дней)
find $BACKUP_DIR -name "aisha_backup_*.tar.gz" -mtime +30 -delete

echo "Старые backup'ы очищены"
EOF

    chmod +x ${BACKEND_DIR}/scripts/backup.sh
    chown ${PROJECT_USER}:${PROJECT_USER} ${BACKEND_DIR}/scripts/backup.sh
    
    # Ежедневный backup в 2:00
    cat > /etc/cron.d/aisha-backup << EOF
# Ежедневный backup в 2:00
0 2 * * * ${PROJECT_USER} ${BACKEND_DIR}/scripts/backup.sh >> ${BACKEND_DIR}/logs/backup.log 2>&1
EOF
    
    log "Backup настроен"
}

# Запуск сервисов
start_services() {
    log "Запуск сервисов..."
    
    # Nginx
    systemctl enable nginx
    systemctl restart nginx
    
    # Aisha сервисы
    systemctl enable aisha-bot
    systemctl enable aisha-api
    
    systemctl start aisha-bot
    sleep 3
    systemctl start aisha-api
    
    log "Сервисы запущены"
}

# Проверка развертывания
verify_deployment() {
    log "Проверка развертывания..."
    
    # Проверка сервисов
    for service in nginx aisha-bot aisha-api; do
        if systemctl is-active --quiet $service; then
            info "✅ $service: запущен"
        else
            warn "❌ $service: не запущен"
        fi
    done
    
    # Проверка портов
    sleep 5
    for port in 8443 8000; do
        if ss -tuln | grep -q ":$port "; then
            info "✅ Порт $port: открыт"
        else
            warn "❌ Порт $port: закрыт"
        fi
    done
    
    log "Проверка завершена"
}

# Основная функция
main() {
    log "🚀 Начало развертывания Aisha Bot (Frontend/Backend архитектура)"
    
    check_root
    update_system
    install_dependencies
    create_user
    create_directories
    setup_ssl
    deploy_backend
    setup_virtualenv
    setup_nginx
    create_systemd_services
    setup_firewall
    setup_logging
    create_monitoring
    create_backup
    start_services
    verify_deployment
    
    log "🎉 Развертывание завершено успешно!"
    echo
    info "📊 Статус сервисов:"
    systemctl status aisha-bot aisha-api nginx --no-pager -l
    echo
    info "🔗 Webhook URL: https://aibots.kz:8443/api/v1/avatar/status_update"
    info "📁 Backend: ${BACKEND_DIR}"
    info "📁 Frontend: ${FRONTEND_DIR}"
    info "👤 Пользователь: ${PROJECT_USER}"
    echo
    warn "⚠️  Не забудьте:"
    warn "   1. Настроить .env файл с токенами и ключами"
    warn "   2. Проверить подключение к внешним сервисам (PostgreSQL, Redis, MinIO)"
    warn "   3. Протестировать webhook от FAL AI"
}

# Запуск
main "$@" 