#!/bin/bash
#
# Скрипт автоматического развертывания Aisha Bot в продакшн (минимальная версия)
# Только Bot + API Server (PostgreSQL, Redis, MinIO - внешние)
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
PROJECT_DIR="/opt/aisha_bot"
PROJECT_USER="aisha"
PYTHON_VERSION="3.11"

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
        error "Этот скрипт должен запускаться от root"
    fi
}

# Проверка системы
check_system() {
    log "Проверка системных требований..."
    
    # Проверка Ubuntu версии
    if ! grep -q "Ubuntu 24.04" /etc/os-release; then
        warn "Рекомендуется Ubuntu 24.04 LTS"
    fi
    
    # Проверка RAM (снижены требования)
    total_ram=$(free -g | awk '/^Mem:/{print $2}')
    if [ $total_ram -lt 4 ]; then
        warn "Рекомендуется минимум 4 GB RAM для app сервера (обнаружено: ${total_ram}GB)"
    fi
    
    # Проверка свободного места (снижены требования)
    free_space=$(df / | awk 'NR==2{print $4/1024/1024}')
    if (( $(echo "$free_space < 20" | bc -l) )); then
        warn "Рекомендуется минимум 20 GB свободного места для app сервера"
    fi
    
    log "Системные требования проверены"
}

# Обновление системы
update_system() {
    log "Обновление системы..."
    apt update && apt upgrade -y
    apt install -y software-properties-common apt-transport-https ca-certificates curl gnupg lsb-release
}

# Установка зависимостей
install_dependencies() {
    log "Установка системных зависимостей..."
    
    # Python 3.11
    apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev python3-pip
    
    # PostgreSQL client (для подключения к внешней БД)
    apt install -y postgresql-client-16
    
    # Redis client (для подключения к внешнему Redis)
    apt install -y redis-tools
    
    # Nginx (опционально)
    apt install -y nginx
    
    # Утилиты
    apt install -y htop iotop git curl wget unzip tree jq bc telnet
    apt install -y certbot python3-certbot-nginx
    
    # Build tools
    apt install -y build-essential libpq-dev
    
    log "Зависимости установлены"
}

# Создание пользователя
create_user() {
    log "Создание пользователя ${PROJECT_USER}..."
    
    if id "$PROJECT_USER" &>/dev/null; then
        info "Пользователь ${PROJECT_USER} уже существует"
    else
        useradd -m -s /bin/bash $PROJECT_USER
        usermod -aG sudo $PROJECT_USER
        log "Пользователь ${PROJECT_USER} создан"
    fi
    
    # Создание директории проекта
    mkdir -p $PROJECT_DIR
    chown -R $PROJECT_USER:$PROJECT_USER $PROJECT_DIR
    
    # Создание дополнительных директорий
    sudo -u $PROJECT_USER mkdir -p $PROJECT_DIR/{storage,logs,backups,scripts}
}

# Настройка проекта
setup_project() {
    log "Настройка проекта..."
    
    # Переход к пользователю проекта
    sudo -u $PROJECT_USER bash << 'EOF'
cd /opt/aisha_bot

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка базовых зависимостей
pip install --upgrade pip setuptools wheel

EOF

    log "Проект подготовлен"
}

# Создание конфигурации
create_config() {
    log "Создание конфигурации..."
    
    # Основной .env файл
    sudo -u $PROJECT_USER tee $PROJECT_DIR/.env << 'EOF'
# Database (ВНЕШНИЙ СЕРВЕР - ЗАПОЛНИТЕ)
DATABASE_URL=postgresql+asyncpg://username:password@your-postgres-server:5432/aisha_bot_prod

# Redis (ВНЕШНИЙ СЕРВЕР - ЗАПОЛНИТЕ)
REDIS_URL=redis://your-redis-server:6379/0

# MinIO (ВНЕШНИЙ СЕРВЕР - ЗАПОЛНИТЕ)
MINIO_ENDPOINT=your-minio-server:9000
MINIO_ACCESS_KEY=your-minio-access-key
MINIO_SECRET_KEY=your-minio-secret-key
MINIO_BUCKET=aisha-bot-storage
MINIO_SECURE=true

# Telegram (ЗАПОЛНИТЕ)
TELEGRAM_TOKEN=

# FAL AI (ЗАПОЛНИТЕ)
FAL_API_KEY=
FAL_WEBHOOK_URL=https://aibots.kz:8443/api/v1/avatar/status_update
AVATAR_TEST_MODE=false

# Storage (локальное дублирование)
STORAGE_PATH=/opt/aisha_bot/storage

# Logs
LOG_LEVEL=INFO
LOG_MAX_BYTES=50000000
LOG_BACKUP_COUNT=10

# Security (ЗАПОЛНИТЕ)
ADMIN_USER_IDS=

# Performance (оптимизировано для app сервера)
MAX_WORKERS=4
BATCH_SIZE=50
DB_POOL_SIZE=15
DB_MAX_OVERFLOW=20
EOF

    # API Server .env
    sudo -u $PROJECT_USER tee $PROJECT_DIR/api_server/.env << 'EOF'
# API Server
API_HOST=0.0.0.0
API_PORT=8443
SSL_ENABLED=true
SSL_CERT_PATH=ssl/aibots_kz.crt
SSL_KEY_PATH=ssl/aibots.kz.key

# Database (ВНЕШНИЙ СЕРВЕР - ЗАПОЛНИТЕ)
DATABASE_URL=postgresql+asyncpg://username:password@your-postgres-server:5432/aisha_bot_prod

# Telegram (ЗАПОЛНИТЕ)
TELEGRAM_TOKEN=

# Security
LOG_LEVEL=INFO
ALLOWED_IPS=["185.199.108.0/22", "140.82.112.0/20"]
EOF

    # Права доступа
    chmod 600 $PROJECT_DIR/.env
    chmod 600 $PROJECT_DIR/api_server/.env
    
    warn "⚠️ ОБЯЗАТЕЛЬНО заполните:"
    warn "   - DATABASE_URL (ваш PostgreSQL сервер)"
    warn "   - REDIS_URL (ваш Redis сервер)"
    warn "   - MINIO_* настройки (ваш MinIO сервер)"
    warn "   - TELEGRAM_TOKEN и FAL_API_KEY"
    
    log "Конфигурация создана"
}

# Создание systemd сервисов
create_services() {
    log "Создание systemd сервисов..."
    
    # Основной бот
    tee /etc/systemd/system/aisha-bot.service << EOF
[Unit]
Description=Aisha Telegram Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$PROJECT_USER
Group=$PROJECT_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python -m app.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aisha-bot

# Resource limits (снижены для app сервера)
LimitNOFILE=32768
MemoryMax=3G
CPUQuota=200%

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR/storage $PROJECT_DIR/logs
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # API сервер
    tee /etc/systemd/system/aisha-api.service << EOF
[Unit]
Description=Aisha Bot FAL Webhook API Server
After=network.target network-online.target aisha-bot.service
Wants=network-online.target

[Service]
Type=simple
User=$PROJECT_USER
Group=$PROJECT_USER
WorkingDirectory=$PROJECT_DIR/api_server
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python run_api_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aisha-api

# Resource limits (для API сервера)
LimitNOFILE=4096
MemoryMax=1G
CPUQuota=50%

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR/api_server/logs
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable aisha-bot.service
    systemctl enable aisha-api.service
    
    log "Systemd сервисы созданы"
}

# Настройка мониторинга
setup_monitoring() {
    log "Настройка мониторинга..."
    
    # Health check скрипт (адаптированный для внешних сервисов)
    tee $PROJECT_DIR/scripts/health_check.sh << 'EOF'
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

# Проверка API endpoint
curl -f https://aibots.kz:8443/health >/dev/null 2>&1 || {
    echo "$(date): API health check failed" >> /var/log/aisha-health.log
}

# Проверка места на диске
DISK_USAGE=$(df /opt/aisha_bot | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "$(date): Disk usage is ${DISK_USAGE}%" >> /var/log/aisha-health.log
fi

# Проверка внешних подключений (опционально)
# Раскомментируйте после настройки конфигурации
# timeout 5 telnet your-postgres-server 5432 >/dev/null 2>&1 || {
#     echo "$(date): PostgreSQL server unreachable" >> /var/log/aisha-health.log
# }
# 
# timeout 5 telnet your-redis-server 6379 >/dev/null 2>&1 || {
#     echo "$(date): Redis server unreachable" >> /var/log/aisha-health.log
# }
EOF

    # Backup скрипт (только логи и конфиг)
    tee $PROJECT_DIR/scripts/backup.sh << EOF
#!/bin/bash

BACKUP_DIR="$PROJECT_DIR/backups"
DATE=\$(date +"%Y%m%d_%H%M%S")

mkdir -p \$BACKUP_DIR

# Backup configuration
tar czf \$BACKUP_DIR/config_\$DATE.tar.gz $PROJECT_DIR/.env $PROJECT_DIR/api_server/.env

# Backup logs
tar czf \$BACKUP_DIR/logs_\$DATE.tar.gz $PROJECT_DIR/logs/ $PROJECT_DIR/api_server/logs/

# Backup local storage
if [ -d "$PROJECT_DIR/storage" ] && [ "\$(ls -A $PROJECT_DIR/storage)" ]; then
    tar czf \$BACKUP_DIR/storage_\$DATE.tar.gz $PROJECT_DIR/storage/
fi

# Keep only last 7 days
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "\$(date): Local backup completed - \$DATE" >> /var/log/aisha-backup.log
EOF

    chmod +x $PROJECT_DIR/scripts/*.sh
    chown -R $PROJECT_USER:$PROJECT_USER $PROJECT_DIR/scripts/
    
    # Добавление в crontab
    sudo -u $PROJECT_USER bash << 'EOF'
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/aisha_bot/scripts/health_check.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/aisha_bot/scripts/backup.sh") | crontab -
EOF

    log "Мониторинг настроен"
}

# Настройка logrotate
setup_logrotate() {
    log "Настройка ротации логов..."
    
    tee /etc/logrotate.d/aisha-bot << EOF
$PROJECT_DIR/logs/*.log
$PROJECT_DIR/api_server/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 644 $PROJECT_USER $PROJECT_USER
    postrotate
        systemctl reload aisha-bot 2>/dev/null || true
        systemctl reload aisha-api 2>/dev/null || true
    endscript
}
EOF

    log "Ротация логов настроена"
}

# Настройка firewall
setup_firewall() {
    log "Настройка firewall..."
    
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # SSH
    ufw allow 22/tcp
    
    # HTTP/HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # API Server (только для FAL AI)
    ufw allow from 185.199.108.0/22 to any port 8443
    ufw allow from 140.82.112.0/20 to any port 8443
    
    ufw --force enable
    
    info "Firewall настроен для исходящих подключений к внешним сервисам"
    warn "Убедитесь что ваши PostgreSQL/Redis/MinIO серверы доступны"
    
    log "Firewall настроен"
}

# Создание скрипта проверки внешних подключений
create_connection_test() {
    log "Создание скрипта проверки подключений..."
    
    tee $PROJECT_DIR/scripts/test_connections.sh << 'EOF'
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
source /opt/aisha_bot/.env

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

echo ""
echo "📋 Для проверки функциональности после настройки конфигурации:"
echo "   redis-cli -h \$REDIS_HOST ping"
echo "   psql \$DATABASE_URL -c 'SELECT 1;'"
echo "   curl http://\$MINIO_ENDPOINT/minio/health/live"
EOF

    chmod +x $PROJECT_DIR/scripts/test_connections.sh
    chown $PROJECT_USER:$PROJECT_USER $PROJECT_DIR/scripts/test_connections.sh
    
    log "Скрипт проверки подключений создан"
}

# Финальная проверка
final_check() {
    log "Выполнение финальной проверки..."
    
    # Проверка структуры проекта
    if [ -d "$PROJECT_DIR/venv" ]; then
        info "✅ Виртуальное окружение создано"
    else
        error "❌ Виртуальное окружение не найдено"
    fi
    
    # Проверка конфигурации
    if [ -f "$PROJECT_DIR/.env" ]; then
        info "✅ Основная конфигурация создана"
    else
        error "❌ Основная конфигурация не найдена"
    fi
    
    if [ -f "$PROJECT_DIR/api_server/.env" ]; then
        info "✅ Конфигурация API сервера создана"
    else
        error "❌ Конфигурация API сервера не найдена"
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
    
    log "Финальная проверка завершена"
}

# Главная функция
main() {
    log "🚀 Начинаем развертывание Aisha Bot (только App сервер)..."
    
    check_root
    check_system
    update_system
    install_dependencies
    create_user
    setup_project
    create_config
    create_services
    setup_monitoring
    setup_logrotate
    setup_firewall
    create_connection_test
    final_check
    
    log "🎉 Развертывание App сервера завершено!"
    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN} Следующие шаги для завершения:${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    echo "1. 📝 Заполните конфигурацию внешних сервисов:"
    echo "   sudo nano $PROJECT_DIR/.env"
    echo "   sudo nano $PROJECT_DIR/api_server/.env"
    echo
    echo "2. 📁 Скопируйте код проекта в $PROJECT_DIR"
    echo
    echo "3. 🔐 Скопируйте SSL сертификаты:"
    echo "   sudo cp ssl_certificates/* $PROJECT_DIR/api_server/ssl/"
    echo "   sudo chown -R $PROJECT_USER:$PROJECT_USER $PROJECT_DIR/api_server/ssl/"
    echo "   sudo chmod 600 $PROJECT_DIR/api_server/ssl/*.key"
    echo
    echo "4. 📦 Установите зависимости проекта:"
    echo "   sudo -u $PROJECT_USER bash"
    echo "   cd $PROJECT_DIR && source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    echo "   cd api_server && pip install -r requirements.txt"
    echo
    echo "5. 🔍 Проверьте подключения к внешним сервисам:"
    echo "   sudo -u $PROJECT_USER $PROJECT_DIR/scripts/test_connections.sh"
    echo
    echo "6. 🗄️ Выполните миграции (если нужно):"
    echo "   alembic upgrade head"
    echo
    echo "7. 🚀 Запустите сервисы:"
    echo "   sudo systemctl start aisha-bot"
    echo "   sudo systemctl start aisha-api"
    echo
    echo "8. ✅ Проверьте статус:"
    echo "   sudo systemctl status aisha-bot"
    echo "   sudo systemctl status aisha-api"
    echo
    echo -e "${YELLOW}📊 Мониторинг:${NC}"
    echo "   Логи: sudo journalctl -fu aisha-bot"
    echo "   Health: tail -f /var/log/aisha-health.log"
    echo "   Connections: sudo -u $PROJECT_USER $PROJECT_DIR/scripts/test_connections.sh"
    echo
    echo -e "${BLUE}💡 Требования к внешним сервисам:${NC}"
    echo "   PostgreSQL: database 'aisha_bot_prod' с пользователем"
    echo "   Redis: доступный экземпляр"
    echo "   MinIO: bucket 'aisha-bot-storage' с настроенными правами"
}

# Запуск
main "$@" 