#!/bin/bash

# Скрипт для правильной настройки firewall после диагностики
# Использование: sudo ./enable_firewall_correct.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен запускаться с правами root (sudo)"
fi

log "Настройка firewall с правильными правилами..."

# Проверка наличия ufw
if ! command -v ufw &> /dev/null; then
    log "Установка ufw..."
    apt update
    apt install -y ufw
fi

# Показать текущее состояние
log "Текущее состояние firewall:"
ufw status

echo
log "Настраиваем firewall для работы API сервера на порту 8443"
echo

# Сброс правил для чистой настройки
warn "Сброс текущих правил firewall..."
ufw --force reset

# Базовые правила
log "Установка базовых правил..."
ufw default deny incoming
ufw default allow outgoing

# SSH (критически важно!)
log "Разрешение SSH (порт 22)..."
ufw allow 22/tcp
ufw limit 22/tcp  # Защита от брутфорса

# HTTP/HTTPS (для веб-сервера)
log "Разрешение HTTP/HTTPS..."
ufw allow 80/tcp
ufw allow 443/tcp

# API сервер - временно открываем для всех (для тестирования)
log "Разрешение доступа к API серверу (порт 8443) для всех..."
warn "ВНИМАНИЕ: Порт 8443 открыт для всех IP! Это временная мера для тестирования."
ufw allow 8443/tcp

# Локальный доступ
log "Разрешение локального доступа..."
ufw allow from 127.0.0.1 to any port 8000  # Внутренний API

# Блокировка прямого доступа к внутреннему API (8000) извне
log "Блокировка внешнего доступа к внутреннему API (порт 8000)..."
ufw deny 8000/tcp

# PostgreSQL - только локальный доступ
log "Блокировка внешнего доступа к PostgreSQL..."
ufw deny 5432/tcp

# Ping
log "Разрешение ping..."
ufw allow in on lo
ufw allow out on lo

# Активация firewall
log "Активация firewall..."
ufw --force enable

# Показать итоговые правила
log "Итоговые правила firewall:"
ufw status numbered

log "🎉 Firewall настроен и активирован!"
echo
log "Настроенные правила:"
echo "✅ SSH (порт 22) - разрешен с защитой от брутфорса"
echo "✅ HTTP (порт 80) - разрешен"
echo "✅ HTTPS (порт 443) - разрешен"
echo "⚠️  API сервер (порт 8443) - ВРЕМЕННО открыт для всех"
echo "🚫 Внутренний API (порт 8000) - заблокирован извне"
echo "🚫 PostgreSQL (порт 5432) - заблокирован извне"
echo
log "Проверьте доступность API:"
echo "curl https://aibots.kz:8443/health"
echo
warn "ВАЖНО: После проверки работы ограничьте доступ к порту 8443!"
log "Для ограничения доступа используйте:"
echo "sudo ufw delete allow 8443/tcp"
echo "sudo ufw allow from TRUSTED_IP to any port 8443" 