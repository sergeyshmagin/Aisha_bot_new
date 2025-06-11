#!/bin/bash

# 📊 Скрипт быстрого просмотра логов Aisha Bot
# Версия: 2.0 (2025-06-11)

set -euo pipefail

# 📋 Конфигурация
readonly PROD_SERVER="192.168.0.10"
readonly PROD_USER="aisha"

# 🎨 Цвета
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 📊 Статус контейнеров
show_status() {
    log_info "📊 Статус всех контейнеров:"
    ssh "${PROD_USER}@${PROD_SERVER}" "
        docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | 
        grep -E '(aisha|webhook)' || echo 'Контейнеры не найдены'
    "
}

# 📋 Логи бота
show_bot_logs() {
    local lines=${1:-20}
    log_info "📋 Логи бота (последние ${lines} строк):"
    ssh "${PROD_USER}@${PROD_SERVER}" "
        docker logs aisha-bot-primary --tail ${lines} 2>/dev/null || 
        echo 'Контейнер aisha-bot-primary не найден'
    "
}

# 🌐 Логи API
show_api_logs() {
    local lines=${1:-10}
    log_info "🌐 Логи Webhook API (последние ${lines} строк):"
    ssh "${PROD_USER}@${PROD_SERVER}" "
        docker logs webhook-api-1 --tail ${lines} 2>/dev/null ||
        echo 'Контейнер webhook-api-1 не найден'
    "
}

# 🔍 Проверка здоровья
health_check() {
    log_info "🔍 Проверка здоровья системы:"
    ssh "${PROD_USER}@${PROD_SERVER}" "
        echo '=== Redis (192.168.0.3:6379) ==='
        timeout 5 redis-cli -h 192.168.0.3 -p 6379 -a 'wd7QuwAbG0wtyoOOw3Sm' ping 2>/dev/null || echo 'Redis недоступен'
        
        echo '=== PostgreSQL (192.168.0.4:5432) ==='
        timeout 5 pg_isready -h 192.168.0.4 -p 5432 2>/dev/null || echo 'PostgreSQL проверка недоступна'
        
        echo '=== MinIO (192.168.0.4:9000) ==='
        timeout 5 curl -s http://192.168.0.4:9000/minio/health/live > /dev/null && echo 'MinIO доступен' || echo 'MinIO недоступен'
    "
}

# 📋 Справка
show_help() {
    cat << EOF
📊 Скрипт быстрого мониторинга Aisha Bot

Использование: $0 [КОМАНДА] [ОПЦИИ]

КОМАНДЫ:
  status          Показать статус контейнеров (по умолчанию)
  bot [N]         Показать логи бота (N строк, по умолчанию 20)
  api [N]         Показать логи API (N строк, по умолчанию 10)  
  health          Проверить здоровье внешних сервисов
  all [N]         Показать всё (статус + логи + здоровье)
  watch           Мониторинг в реальном времени (ctrl+c для выхода)
  help            Показать эту справку

Примеры:
  $0                    # Статус контейнеров
  $0 bot 50             # Последние 50 строк логов бота
  $0 all 30             # Полная проверка с 30 строками логов
  $0 watch              # Мониторинг в реальном времени

Сервер: ${PROD_USER}@${PROD_SERVER}
EOF
}

# 👁️ Мониторинг в реальном времени
watch_logs() {
    log_info "👁️ Мониторинг в реальном времени (Ctrl+C для выхода)..."
    ssh "${PROD_USER}@${PROD_SERVER}" "
        docker logs -f aisha-bot-primary 2>/dev/null || 
        echo 'Не удалось подключиться к логам'
    "
}

# 🎯 Главная функция
main() {
    local cmd=${1:-"status"}
    local lines=${2:-20}
    
    case $cmd in
        status)
            show_status
            ;;
        bot)
            show_bot_logs "$lines"
            ;;
        api)
            show_api_logs "$lines"
            ;;
        health)
            health_check
            ;;
        all)
            show_status
            echo
            show_bot_logs "$lines"
            echo
            show_api_logs "$lines"
            echo
            health_check
            ;;
        watch)
            watch_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_info "❓ Неизвестная команда: $cmd"
            show_help
            exit 1
            ;;
    esac
}

# Запуск
main "$@" 