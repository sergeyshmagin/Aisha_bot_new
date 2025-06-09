#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# 📊 AISHA BOT - МОНИТОРИНГ ПРОДАКШН СИСТЕМЫ
# ═══════════════════════════════════════════════════════════════════════════════
# Версия: 2.0
# Дата: 2025-06-09
# Статус: ✅ ГОТОВ К ИСПОЛЬЗОВАНИЮ
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Конфигурация
PROD_SERVER="192.168.0.10"
PROD_USER="aisha"
PROJECT_ROOT="/opt/aisha-backend"

# Логирование
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "${CYAN}[===]${NC} $1"; }

# Проверка статуса контейнеров
check_containers() {
    log_section "📦 СТАТУС КОНТЕЙНЕРОВ"
    
    ssh ${PROD_USER}@${PROD_SERVER} "
        echo '🐳 Docker контейнеры:'
        docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E '(aisha|nginx)' || echo 'Нет запущенных контейнеров'
        
        echo
        echo '💾 Использование ресурсов:'
        docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' | head -10
    "
}

# Проверка логов сервисов
check_logs() {
    log_section "📝 ЛОГИ СЕРВИСОВ"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "🤖 Основной бот (последние 5 строк):"
        docker logs aisha-bot-polling-1 --tail 5 2>/dev/null || echo "Не запущен"
        
        echo
        echo "⏸️ Standby бот (последние 3 строки):"
        docker logs aisha-bot-polling-2 --tail 3 2>/dev/null || echo "Не запущен"
        
        echo  
        echo "🌐 Webhook API 1 (последние 3 строки):"
        docker logs aisha-webhook-api-1 --tail 3 2>/dev/null || echo "Не запущен"
        
        echo
        echo "🌐 Webhook API 2 (последние 3 строки):"
        docker logs aisha-webhook-api-2 --tail 3 2>/dev/null || echo "Не запущен"
        
        echo
        echo "🔄 Nginx (последние 3 строки):"
        docker logs aisha-nginx-prod --tail 3 2>/dev/null || echo "Не запущен"
    '
}

# Проверка health check'ов
check_health() {
    log_section "🏥 ПРОВЕРКА ЗДОРОВЬЯ"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "💚 Healthy контейнеры:"
        docker ps --filter "health=healthy" --format "table {{.Names}}\t{{.Status}}" || echo "Нет healthy контейнеров"
        
        echo
        echo "❤️ Unhealthy контейнеры:"
        docker ps --filter "health=unhealthy" --format "table {{.Names}}\t{{.Status}}" || echo "Нет unhealthy контейнеров"
    '
}

# Проверка системных ресурсов
check_system() {
    log_section "🖥️ СИСТЕМНЫЕ РЕСУРСЫ"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "💾 Память:"
        free -h | head -2
        
        echo
        echo "💽 Диск:"
        df -h | grep -E "(/$|/opt)" || df -h | head -2
        
        echo
        echo "🔥 CPU Load:"
        uptime
        
        echo
        echo "🔗 Сеть:"
        ss -tuln | grep -E ":80|:443|:5000|:6379|:5432" || echo "Основные порты не прослушиваются"
    '
}

# Проверка Telegram API
check_telegram() {
    log_section "📱 TELEGRAM API"
    
    if [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]]; then
        log_info "Проверка токена бота..."
        
        response=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" || echo '{"ok":false}')
        
        if echo "$response" | grep -q '"ok":true'; then
            username=$(echo "$response" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
            log_info "✅ Бот активен: @${username}"
        else
            log_error "❌ Проблема с токеном бота"
        fi
    else
        log_warn "⚠️ TELEGRAM_BOT_TOKEN не установлен"
    fi
}

# Проверка БД соединений
check_database() {
    log_section "🗄️ БАЗА ДАННЫХ"
    
    ssh ${PROD_USER}@${PROD_SERVER} "
        cd ${PROJECT_ROOT}
        
        echo '🐘 PostgreSQL:'
        docker exec postgres-prod psql -U aisha -d aisha_db -c 'SELECT version();' 2>/dev/null | head -3 || echo 'PostgreSQL недоступен'
        
        echo
        echo '🟥 Redis:'
        docker exec redis-prod redis-cli ping 2>/dev/null || echo 'Redis недоступен'
    " || log_warn "База данных недоступна для проверки"
}

# Сводка по кластеру
cluster_summary() {
    log_section "📋 СВОДКА ПО КЛАСТЕРУ"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        total=$(docker ps | grep -c aisha || echo 0)
        healthy=$(docker ps --filter "health=healthy" | grep -c aisha || echo 0)
        running=$(docker ps --filter "status=running" | grep -c aisha || echo 0)
        
        echo "📊 Статистика кластера:"
        echo "   • Всего контейнеров Aisha: $total"
        echo "   • Запущенных: $running"
        echo "   • Здоровых: $healthy"
        
        if [[ $running -gt 0 && $healthy -gt 0 ]]; then
            echo "✅ Кластер работает нормально"
        elif [[ $running -gt 0 ]]; then
            echo "⚠️ Кластер работает с проблемами"
        else
            echo "❌ Кластер не работает"
        fi
    '
}

# Основная функция
main() {
    local mode="${1:-full}"
    
    log_info "📊 Мониторинг Aisha Bot Production"
    log_info "📍 Сервер: ${PROD_USER}@${PROD_SERVER}"
    log_info "🕒 $(date)"
    echo
    
    case "$mode" in
        "containers"|"c")
            check_containers
            ;;
        "logs"|"l")
            check_logs
            ;;
        "health"|"h")
            check_health
            ;;
        "system"|"s")
            check_system
            ;;
        "telegram"|"t")
            check_telegram
            ;;
        "database"|"db")
            check_database
            ;;
        "summary"|"sum")
            cluster_summary
            ;;
        "quick"|"q")
            check_containers
            cluster_summary
            ;;
        "full"|*)
            check_containers
            echo
            check_health
            echo
            check_logs
            echo
            check_system
            echo
            check_telegram
            echo
            check_database
            echo
            cluster_summary
            ;;
    esac
    
    echo
    log_info "✅ Мониторинг завершен"
}

# Справка
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Использование: $0 [режим]"
    echo
    echo "Режимы мониторинга:"
    echo "  full, f     - Полная проверка (по умолчанию)"
    echo "  quick, q    - Быстрая проверка (контейнеры + сводка)"
    echo "  containers, c - Только статус контейнеров"
    echo "  logs, l     - Только логи сервисов"
    echo "  health, h   - Только health check"
    echo "  system, s   - Только системные ресурсы"
    echo "  telegram, t - Только проверка Telegram API"
    echo "  database, db - Только проверка БД"
    echo "  summary, sum - Только сводка по кластеру"
    echo
    echo "Примеры:"
    echo "  $0              # Полная проверка"
    echo "  $0 quick        # Быстрая проверка"
    echo "  $0 logs         # Только логи"
    echo
    echo "Переменные окружения:"
    echo "  TELEGRAM_BOT_TOKEN - для проверки Telegram API"
    exit 0
fi

# Запуск
main "$@" 