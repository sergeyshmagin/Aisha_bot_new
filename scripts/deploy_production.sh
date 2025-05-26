#!/bin/bash
#
# Скрипт автоматического развертывания Aisha Bot в продакшн
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
DB_NAME="aisha_bot_prod"
DB_USER="aisha"
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
    
    # Проверка RAM
    total_ram=$(free -g | awk '/^Mem:/{print $2}')
    if [ $total_ram -lt 8 ]; then
        warn "Рекомендуется минимум 8 GB RAM (обнаружено: ${total_ram}GB)"
    fi
    
    # Проверка свободного места
    free_space=$(df / | awk 'NR==2{print $4/1024/1024}')
    if (( $(echo "$free_space < 50" | bc -l) )); then
        warn "Рекомендуется минимум 50 GB свободного места"
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
    
    # PostgreSQL 16
    apt install -y postgresql-16 postgresql-contrib-16 postgresql-client-16
    
    # Nginx
    apt install -y nginx
    
    # Утилиты
    apt install -y htop iotop git curl wget unzip tree jq bc
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

# Настройка PostgreSQL
setup_postgresql() {
    log "Настройка PostgreSQL..."
    
    # Запуск PostgreSQL
    systemctl enable postgresql
    systemctl start postgresql
    
    # Создание пользователя и базы данных
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" || true
    sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;" || true
    
    # Генерация пароля
    DB_PASSWORD=$(openssl rand -base64 32)
    
    sudo -u postgres createuser --createdb $DB_USER
    sudo -u postgres createdb $DB_NAME -O $DB_USER
    sudo -u postgres psql -c "ALTER USER $DB_USER PASSWORD '$DB_PASSWORD';"
    
    # Сохранение пароля
    echo "$DB_PASSWORD" > /tmp/db_password.txt
    chown $PROJECT_USER:$PROJECT_USER /tmp/db_password.txt
    chmod 600 /tmp/db_password.txt
    
    # Настройка конфигурации PostgreSQL для продакшн
    PG_CONFIG="/etc/postgresql/16/main/postgresql.conf"
    cp $PG_CONFIG ${PG_CONFIG}.backup
    
    cat >> $PG_CONFIG << 'EOF'

# Aisha Bot Production Settings
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
EOF
    
    systemctl restart postgresql
    log "PostgreSQL настроен"
}

# Клонирование проекта
clone_project() {
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
    
    DB_PASSWORD=$(cat /tmp/db_password.txt)
    
    # Основной .env файл
    sudo -u $PROJECT_USER tee $PROJECT_DIR/.env << EOF
# Database
DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME

# Telegram (ЗАПОЛНИТЕ)
TELEGRAM_TOKEN=

# FAL AI (ЗАПОЛНИТЕ)
FAL_API_KEY=
FAL_WEBHOOK_URL=https://aibots.kz:8443/api/v1/avatar/status_update
AVATAR_TEST_MODE=false

# Storage
STORAGE_PATH=$PROJECT_DIR/storage

# Logs
LOG_LEVEL=INFO
LOG_MAX_BYTES=50000000
LOG_BACKUP_COUNT=10

# Security (ЗАПОЛНИТЕ)
ADMIN_USER_IDS=

# Performance
MAX_WORKERS=8
BATCH_SIZE=100
EOF

    # API Server .env
    sudo -u $PROJECT_USER tee $PROJECT_DIR/api_server/.env << EOF
# API Server
API_HOST=0.0.0.0
API_PORT=8443
SSL_ENABLED=true
SSL_CERT_PATH=ssl/aibots_kz.crt
SSL_KEY_PATH=ssl/aibots.kz.key

# Database
DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME

# Telegram (ЗАПОЛНИТЕ)
TELEGRAM_TOKEN=

# Security
LOG_LEVEL=INFO
ALLOWED_IPS=["185.199.108.0/22", "140.82.112.0/20"]
EOF

    # Права доступа
    chmod 600 $PROJECT_DIR/.env
    chmod 600 $PROJECT_DIR/api_server/.env
    
    rm /tmp/db_password.txt
    
    warn "⚠️ Не забудьте заполнить TELEGRAM_TOKEN и FAL_API_KEY в .env файлах!"
    
    log "Конфигурация создана"
}

# Создание systemd сервисов
create_services() {
    log "Создание systemd сервисов..."
    
    # Основной бот
    tee /etc/systemd/system/aisha-bot.service << EOF
[Unit]
Description=Aisha Telegram Bot
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=$PROJECT_USER
Group=$PROJECT_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python -m app.main
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
ReadWritePaths=$PROJECT_DIR/storage $PROJECT_DIR/logs
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # API сервер
    tee /etc/systemd/system/aisha-api.service << EOF
[Unit]
Description=Aisha Bot FAL Webhook API Server
After=network.target postgresql.service aisha-bot.service
Wants=postgresql.service

[Service]
Type=simple
User=$PROJECT_USER
Group=$PROJECT_USER
WorkingDirectory=$PROJECT_DIR/api_server
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python run_api_server.py
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
    
    # Health check скрипт
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

# Проверка endpoint (если SSL настроен)
curl -f https://aibots.kz:8443/health >/dev/null 2>&1 || {
    echo "$(date): API health check failed" >> /var/log/aisha-health.log
}

# Проверка места на диске
DISK_USAGE=$(df $PROJECT_DIR | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "$(date): Disk usage is ${DISK_USAGE}%" >> /var/log/aisha-health.log
fi
EOF

    # Backup скрипт
    tee $PROJECT_DIR/scripts/backup.sh << EOF
#!/bin/bash

BACKUP_DIR="$PROJECT_DIR/backups"
DATE=\$(date +"%Y%m%d_%H%M%S")

mkdir -p \$BACKUP_DIR

# Database backup
pg_dump -h localhost -U $DB_USER $DB_NAME | gzip > \$BACKUP_DIR/db_\$DATE.sql.gz

# Application data backup
tar czf \$BACKUP_DIR/storage_\$DATE.tar.gz $PROJECT_DIR/storage/

# Keep only last 7 days
find \$BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "\$(date): Backup completed - \$DATE" >> /var/log/aisha-backup.log
EOF

    chmod +x $PROJECT_DIR/scripts/*.sh
    chown -R $PROJECT_USER:$PROJECT_USER $PROJECT_DIR/scripts/
    
    # Добавление в crontab
    sudo -u $PROJECT_USER bash << 'EOF'
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/aisha_bot/scripts/health_check.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/aisha_bot/scripts/backup.sh") | crontab -
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
    
    # PostgreSQL (только локально)
    ufw deny 5432/tcp
    
    ufw --force enable
    
    log "Firewall настроен"
}

# Финальная проверка
final_check() {
    log "Выполнение финальной проверки..."
    
    # Проверка PostgreSQL
    if systemctl is-active postgresql >/dev/null; then
        info "✅ PostgreSQL работает"
    else
        error "❌ PostgreSQL не работает"
    fi
    
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
    
    log "Финальная проверка завершена"
}

# Главная функция
main() {
    log "🚀 Начинаем развертывание Aisha Bot в продакшн..."
    
    check_root
    check_system
    update_system
    install_dependencies
    create_user
    setup_postgresql
    clone_project
    create_config
    create_services
    setup_monitoring
    setup_logrotate
    setup_firewall
    final_check
    
    log "🎉 Базовое развертывание завершено!"
    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN} Следующие шаги для завершения:${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    echo "1. 📝 Заполните конфигурацию:"
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
    echo "5. 🗄️ Выполните миграции базы данных:"
    echo "   alembic upgrade head"
    echo
    echo "6. 🚀 Запустите сервисы:"
    echo "   sudo systemctl start aisha-bot"
    echo "   sudo systemctl start aisha-api"
    echo
    echo "7. ✅ Проверьте статус:"
    echo "   sudo systemctl status aisha-bot"
    echo "   sudo systemctl status aisha-api"
    echo
    echo -e "${YELLOW}📊 Мониторинг:${NC}"
    echo "   Логи: sudo journalctl -fu aisha-bot"
    echo "   Health: tail -f /var/log/aisha-health.log"
    echo "   Backup: tail -f /var/log/aisha-backup.log"
    echo
}

# Запуск
main "$@" 