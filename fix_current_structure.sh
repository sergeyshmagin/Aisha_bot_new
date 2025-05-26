#!/bin/bash
#
# Скрипт адаптации ТЕКУЩЕЙ структуры Aisha Bot
# Исправляет systemd сервисы под существующие пути
# ЗАПУСКАТЬ ОТ ROOT!
#

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_USER="aisha"

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

# Проверка root
if [[ $EUID -ne 0 ]]; then
    error "Скрипт должен запускаться от root!"
fi

log "🔧 Адаптируем текущую структуру для корректной работы..."

# 1. Остановка сервисов
log "Остановка текущих сервисов..."
systemctl stop aisha-backend 2>/dev/null || true
systemctl stop aisha-frontend 2>/dev/null || true

# 2. Создание правильных systemd сервисов под текущую структуру
log "Создание адаптированных systemd сервисов..."

# Telegram Bot сервис (в aisha-frontend!)
cat > /etc/systemd/system/aisha-bot.service << EOF
[Unit]
Description=Aisha Telegram Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${PROJECT_USER}
Group=${PROJECT_USER}
WorkingDirectory=/opt/aisha-frontend
Environment=PATH=/opt/aisha-frontend/.venv/bin
ExecStart=/opt/aisha-frontend/.venv/bin/python -m app.main
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10

# Ограничения ресурсов
MemoryLimit=3G
CPUQuota=200%

# Безопасность
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/aisha-frontend/logs /opt/aisha-frontend/data /var/log/aisha
ReadOnlyPaths=/opt/aisha-frontend

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aisha-bot

[Install]
WantedBy=multi-user.target
EOF

# API Server сервис (в aisha-backend!)
cat > /etc/systemd/system/aisha-api.service << EOF
[Unit]
Description=Aisha API Server (Webhook)
After=network.target aisha-bot.service
Wants=aisha-bot.service

[Service]
Type=simple
User=${PROJECT_USER}
Group=${PROJECT_USER}
WorkingDirectory=/opt/aisha-backend
Environment=PATH=/opt/aisha-frontend/.venv/bin
ExecStart=/opt/aisha-frontend/.venv/bin/python /opt/aisha-backend/run_api_server.py
Restart=always
RestartSec=5

# Ограничения ресурсов
MemoryLimit=1G
CPUQuota=50%

# Безопасность
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/aisha-frontend/logs /var/log/aisha

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aisha-api

[Install]
WantedBy=multi-user.target
EOF

# 3. Создание конфигурации API server если её нет
if [ ! -f "/opt/aisha-backend/.env" ]; then
    log "Создание конфигурации API server..."
    cat > /opt/aisha-backend/.env << 'EOF'
# API Server Configuration (за nginx)
API_HOST=127.0.0.1
API_PORT=8000
SSL_ENABLED=false

# Database (ВНЕШНИЙ СЕРВЕР - ЗАПОЛНИТЕ)
DATABASE_URL=postgresql+asyncpg://username:password@your-postgres-server:5432/aisha_bot_prod

# Telegram (ЗАПОЛНИТЕ)
TELEGRAM_TOKEN=

# FAL AI (дополнительная безопасность)
FAL_WEBHOOK_SECRET=

# Security
LOG_LEVEL=INFO
EOF
    chown ${PROJECT_USER}:${PROJECT_USER} /opt/aisha-backend/.env
    chmod 600 /opt/aisha-backend/.env
fi

# 4. Создание символических ссылок для удобства
log "Создание символических ссылок..."
ln -sf /opt/aisha-frontend/.env /opt/aisha-backend/main.env 2>/dev/null || true
ln -sf /opt/aisha-frontend/ssl /opt/aisha-backend/ssl 2>/dev/null || true

# 5. Удаление старых сервисов и создание новых
systemctl disable aisha-backend 2>/dev/null || true
systemctl disable aisha-frontend 2>/dev/null || true

systemctl daemon-reload
systemctl enable aisha-bot
systemctl enable aisha-api

# 6. Создание скрипта мониторинга под текущую структуру
log "Создание адаптированного мониторинга..."
mkdir -p /opt/aisha-frontend/scripts 2>/dev/null || true

cat > /opt/aisha-frontend/scripts/health_check_current.sh << 'EOF'
#!/bin/bash
# Health check для текущей структуры

echo "=== Health Check Aisha Bot (current structure) ==="
echo "Время: $(date)"
echo

# Проверка сервисов
if systemctl is-active --quiet aisha-bot; then
    echo "✅ Telegram Bot (aisha-bot): активен"
else
    echo "❌ Telegram Bot (aisha-bot): неактивен"
    systemctl restart aisha-bot
fi

if systemctl is-active --quiet aisha-api; then
    echo "✅ API Server (aisha-api): активен"
else
    echo "❌ API Server (aisha-api): неактивен"
    systemctl restart aisha-api
fi

echo
echo "=== Структура файлов ==="
echo "📁 Main project: /opt/aisha-frontend/"
echo "📁 API server: /opt/aisha-backend/"
echo "🔧 Services: aisha-bot.service, aisha-api.service"
EOF

chmod +x /opt/aisha-frontend/scripts/health_check_current.sh
chown ${PROJECT_USER}:${PROJECT_USER} /opt/aisha-frontend/scripts/health_check_current.sh

log "✅ Текущая структура адаптирована!"
echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} АДАПТИРОВАННАЯ СТРУКТУРА:${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo "📁 /opt/aisha-frontend/         - Основной проект (НЕОЖИДАННО!)"
echo "   ├── app/                     - Telegram бот"
echo "   ├── alembic/                 - Миграции БД"
echo "   ├── tests/                   - Тесты"
echo "   ├── scripts/                 - Скрипты"
echo "   └── ssl/                     - SSL сертификаты"
echo
echo "📁 /opt/aisha-backend/          - Только API server"
echo "   ├── run_api_server.py        - Запуск API"
echo "   ├── app/                     - API routes"
echo "   └── .env                     - API конфигурация"
echo
echo "🔧 Systemd сервисы:"
echo "   ✅ aisha-bot.service         - Telegram бот (/opt/aisha-frontend/)"
echo "   ✅ aisha-api.service         - API сервер (/opt/aisha-backend/)"
echo
echo -e "${YELLOW}⚠️  ВАЖНЫЕ ОСОБЕННОСТИ:${NC}"
echo "1. Основной проект в /opt/aisha-frontend/ (путаница в названии)"
echo "2. API server использует .venv из основного проекта"
echo "3. SSL сертификаты в /opt/aisha-frontend/ssl/"
echo "4. Конфигурация бота: /opt/aisha-frontend/.env"
echo "5. Конфигурация API: /opt/aisha-backend/.env"
echo
echo -e "${RED}🚨 РИСКИ ТАКОЙ СТРУКТУРЫ:${NC}"
echo "- Путаница для новых разработчиков"
echo "- Несоответствие документации"
echo "- Проблемы с автоматическими скриптами"
echo "- Сложность в поддержке и обновлениях"
echo
echo -e "${YELLOW}СЛЕДУЮЩИЕ ШАГИ:${NC}"
echo "1. Проверьте конфигурацию: sudo nano /opt/aisha-frontend/.env"
echo "2. Проверьте API config: sudo nano /opt/aisha-backend/.env"  
echo "3. Запустите сервисы: sudo systemctl start aisha-bot aisha-api"
echo "4. Проверьте статус: sudo systemctl status aisha-bot aisha-api"
echo "5. Мониторинг: /opt/aisha-frontend/scripts/health_check_current.sh" 