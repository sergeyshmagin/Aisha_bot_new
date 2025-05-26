#!/bin/bash

# Скрипт настройки firewall для Aisha Bot API сервера
# Использование: sudo ./setup_firewall.sh

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

# Проверка наличия ufw
if ! command -v ufw &> /dev/null; then
    log "Установка ufw..."
    apt update
    apt install -y ufw
fi

log "Настройка firewall для Aisha Bot API сервера..."

# Показать текущие правила
log "Текущие правила firewall:"
ufw status

read -p "Продолжить настройку firewall? Это изменит существующие правила. (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Настройка firewall отменена"
    exit 0
fi

# Сброс правил (осторожно!)
warn "Сброс существующих правил firewall..."
ufw --force reset

# Настройка базовых правил
log "Настройка базовых правил..."
ufw default deny incoming
ufw default allow outgoing

# SSH (важно!)
log "Разрешение SSH (порт 22)..."
ufw allow 22/tcp
ufw limit 22/tcp  # Защита от брутфорса

# HTTP/HTTPS (если нужен веб-сервер)
log "Разрешение HTTP/HTTPS..."
ufw allow 80/tcp
ufw allow 443/tcp

# API Server на порту 8443 (только для FAL AI)
log "Настройка доступа к API серверу (порт 8443)..."

# IP адреса FAL AI (по документации)
FAL_AI_IPS=(
    "185.199.108.0/22"
    "140.82.112.0/20"
)

for ip in "${FAL_AI_IPS[@]}"; do
    log "Разрешение доступа с $ip к порту 8443..."
    ufw allow from $ip to any port 8443
done

# Разрешение локального доступа к API серверу (для тестирования)
log "Разрешение локального доступа к API серверу..."
ufw allow from 127.0.0.1 to any port 8443
ufw allow from 127.0.0.1 to any port 8000  # Внутренний порт API

# Блокировка прямого доступа к внутреннему порту API (8000) извне
log "Блокировка внешнего доступа к порту 8000..."
ufw deny 8000/tcp

# PostgreSQL - только локальный доступ
log "Блокировка внешнего доступа к PostgreSQL..."
ufw deny 5432/tcp

# Разрешение ping (ICMP)
log "Разрешение ping (ICMP)..."
ufw allow in on lo
ufw allow out on lo

# Активация firewall
log "Активация firewall..."
ufw --force enable

# Показать итоговые правила
log "Итоговые правила firewall:"
ufw status numbered

log "🎉 Firewall настроен!"
echo
log "Настроенные правила:"
echo "✅ SSH (порт 22) - разрешен с ограничением брутфорса"
echo "✅ HTTP (порт 80) - разрешен"
echo "✅ HTTPS (порт 443) - разрешен"
echo "✅ API сервер (порт 8443) - разрешен только для FAL AI"
echo "🚫 Внутренний API (порт 8000) - заблокирован извне"
echo "🚫 PostgreSQL (порт 5432) - заблокирован извне"
echo
log "Тестирование доступа:"
echo "- Локально: curl http://localhost:8000/health"
echo "- Внешний (должен работать): curl https://aibots.kz:8443/health"
echo
warn "ВАЖНО: Убедитесь, что SSH работает, прежде чем отключаться от сервера!" 