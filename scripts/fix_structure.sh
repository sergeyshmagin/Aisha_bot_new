#!/bin/bash
#
# Скрипт исправления структуры файлов Aisha Bot на продакшене
# ЗАПУСКАТЬ ТОЛЬКО ОТ ROOT!
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

log "🔄 Начинаем исправление структуры файлов..."

# 1. Остановка сервисов
log "Остановка сервисов..."
systemctl stop aisha-backend 2>/dev/null || true
systemctl stop aisha-frontend 2>/dev/null || true

# 2. Создание временного каталога
log "Создание временной структуры..."
mkdir -p /tmp/aisha_migration
cd /tmp/aisha_migration

# 3. Копирование основного проекта из aisha-frontend
log "Копирование основного проекта..."
cp -r /opt/aisha-frontend/* ./
rm -rf run_api_server.py 2>/dev/null || true  # API server файл не нужен в основном проекте

# 4. Создание правильного API server каталога
log "Создание API server структуры..."
mkdir -p api_server
cp /opt/aisha-backend/run_api_server.py api_server/
cp /opt/aisha-backend/app api_server/ -r 2>/dev/null || true

# Создание .env для API server если его нет
if [ ! -f "api_server/.env" ]; then
    log "Создание API server .env..."
    cat > api_server/.env << 'EOF'
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
fi

# 5. Очистка старых каталогов
log "Очистка старых каталогов..."
rm -rf /opt/aisha-backend/*
rm -rf /opt/aisha-frontend/*

# 6. Размещение файлов в правильных местах
log "Размещение файлов в правильной структуре..."

# Backend = основной проект + API server
cp -r /tmp/aisha_migration/* /opt/aisha-backend/

# Frontend = пустой каталог (заготовка)
mkdir -p /opt/aisha-frontend/{dist,assets,logs}
echo "# Frontend заготовка - будущий веб-интерфейс" > /opt/aisha-frontend/README.md

# 7. Установка прав
log "Установка прав доступа..."
chown -R ${PROJECT_USER}:${PROJECT_USER} /opt/aisha-backend/
chown -R ${PROJECT_USER}:${PROJECT_USER} /opt/aisha-frontend/
chmod 750 /opt/aisha-backend
chmod 750 /opt/aisha-frontend

# 8. Создание правильных systemd сервисов
log "Создание правильных systemd сервисов..."

# Удаление старых сервисов
systemctl disable aisha-backend 2>/dev/null || true
systemctl disable aisha-frontend 2>/dev/null || true
rm -f /etc/systemd/system/aisha-backend.service
rm -f /etc/systemd/system/aisha-frontend.service

# Создание новых сервисов
cat > /etc/systemd/system/aisha-bot.service << EOF
[Unit]
Description=Aisha Telegram Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${PROJECT_USER}
Group=${PROJECT_USER}
WorkingDirectory=/opt/aisha-backend
Environment=PATH=/opt/aisha-backend/.venv/bin
ExecStart=/opt/aisha-backend/.venv/bin/python -m app.main
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
ReadWritePaths=/opt/aisha-backend/logs /opt/aisha-backend/data /var/log/aisha
ReadOnlyPaths=/opt/aisha-backend

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aisha-bot

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/aisha-api.service << EOF
[Unit]
Description=Aisha API Server (Webhook)
After=network.target aisha-bot.service
Wants=aisha-bot.service

[Service]
Type=simple
User=${PROJECT_USER}
Group=${PROJECT_USER}
WorkingDirectory=/opt/aisha-backend/api_server
Environment=PATH=/opt/aisha-backend/.venv/bin
ExecStart=/opt/aisha-backend/.venv/bin/python run_api_server.py
Restart=always
RestartSec=5

# Ограничения ресурсов
MemoryLimit=1G
CPUQuota=50%

# Безопасность
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/aisha-backend/logs /var/log/aisha

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aisha-api

[Install]
WantedBy=multi-user.target
EOF

# 9. Обновление systemd
systemctl daemon-reload
systemctl enable aisha-bot
systemctl enable aisha-api

# 10. Очистка временных файлов
log "Очистка временных файлов..."
rm -rf /tmp/aisha_migration

log "✅ Структура файлов исправлена!"
echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} НОВАЯ СТРУКТУРА:${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo "📁 /opt/aisha-backend/          - Основной проект + API server"
echo "   ├── app/                     - Telegram бот"
echo "   ├── api_server/              - Webhook API"
echo "   ├── alembic/                 - Миграции БД"
echo "   ├── tests/                   - Тесты"
echo "   ├── scripts/                 - Скрипты"
echo "   └── ssl/                     - SSL сертификаты"
echo
echo "📁 /opt/aisha-frontend/         - Заготовка для веб-интерфейса"
echo
echo "🔧 Systemd сервисы:"
echo "   ✅ aisha-bot.service         - Telegram бот"
echo "   ✅ aisha-api.service         - API сервер"
echo
echo -e "${YELLOW}СЛЕДУЮЩИЕ ШАГИ:${NC}"
echo "1. Проверьте конфигурацию: sudo nano /opt/aisha-backend/.env"
echo "2. Проверьте API config: sudo nano /opt/aisha-backend/api_server/.env"  
echo "3. Запустите сервисы: sudo systemctl start aisha-bot aisha-api"
echo "4. Проверьте статус: sudo systemctl status aisha-bot aisha-api" 