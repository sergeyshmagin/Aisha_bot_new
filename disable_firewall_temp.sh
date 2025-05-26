#!/bin/bash

# Скрипт для временного отключения firewall
# Использование: sudo ./disable_firewall_temp.sh

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

log "Временное отключение firewall для диагностики..."

# Показать текущее состояние
log "Текущее состояние firewall:"
if command -v ufw &> /dev/null; then
    ufw status
elif command -v iptables &> /dev/null; then
    iptables -L -n
else
    log "Firewall не найден"
fi

echo
warn "⚠️  ВНИМАНИЕ: Отключение firewall снижает безопасность сервера!"
warn "⚠️  Используйте только для диагностики и на короткое время!"
echo

read -p "Продолжить отключение firewall? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Отключение firewall отменено"
    exit 0
fi

# Сохранение текущих правил ufw
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    log "Сохранение текущих правил ufw..."
    ufw status numbered > /tmp/ufw_rules_backup.txt
    log "Правила сохранены в /tmp/ufw_rules_backup.txt"
    
    log "Отключение ufw..."
    ufw --force disable
    log "✅ UFW отключен"
fi

# Сохранение текущих правил iptables
if command -v iptables &> /dev/null; then
    log "Сохранение текущих правил iptables..."
    iptables-save > /tmp/iptables_rules_backup.txt
    log "Правила iptables сохранены в /tmp/iptables_rules_backup.txt"
    
    # Опционально очистить iptables (осторожно!)
    read -p "Также очистить правила iptables? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Очистка правил iptables..."
        iptables -F
        iptables -X
        iptables -t nat -F
        iptables -t nat -X
        iptables -t mangle -F
        iptables -t mangle -X
        iptables -P INPUT ACCEPT
        iptables -P FORWARD ACCEPT
        iptables -P OUTPUT ACCEPT
        log "✅ Правила iptables очищены"
    fi
fi

log "🎉 Firewall временно отключен!"
echo
log "Теперь проверьте доступность API:"
echo "- Локально: curl http://localhost:8000/health"
echo "- Внешний: curl https://aibots.kz:8443/health"
echo
warn "ВАЖНО: Не забудьте включить firewall обратно после диагностики!"
log "Для включения используйте: sudo ./enable_firewall.sh"
echo
log "Файлы бэкапа правил:"
echo "- UFW: /tmp/ufw_rules_backup.txt"
echo "- iptables: /tmp/iptables_rules_backup.txt" 