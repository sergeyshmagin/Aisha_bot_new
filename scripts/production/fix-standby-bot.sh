#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 ИСПРАВЛЕНИЕ STANDBY БОТА AISHA
# ═══════════════════════════════════════════════════════════════════════════════
# Временное решение: остановка standby бота для устранения polling конфликта
# Долгосрочное решение: реализация true standby режима
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

# Логирование
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "${CYAN}[===]${NC} $1"; }

# Проверка текущего статуса
check_current_status() {
    log_section "📊 ТЕКУЩИЙ СТАТУС БОТОВ"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "📦 Все бот-контейнеры:"
        docker ps --filter "name=aisha-bot" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        echo
        echo "📊 Статус polling ботов:"
        if docker ps -q --filter "name=aisha-bot-polling-1" | grep -q .; then
            echo "✅ Основной бот (polling-1): RUNNING"
        else
            echo "❌ Основной бот (polling-1): STOPPED"
        fi
        
        if docker ps -q --filter "name=aisha-bot-polling-2" | grep -q .; then
            echo "⚠️ Standby бот (polling-2): RUNNING (КОНФЛИКТ!)"
        else
            echo "✅ Standby бот (polling-2): STOPPED (норма)"
        fi
    '
}

# Остановка standby бота (временное решение)
stop_standby_bot() {
    log_section "🛑 ОСТАНОВКА STANDBY БОТА"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "🛑 Остановка standby бота для устранения конфликта..."
        
        if docker ps -q --filter "name=aisha-bot-polling-2" | grep -q .; then
            echo "Останавливаем aisha-bot-polling-2..."
            docker stop aisha-bot-polling-2
            echo "✅ Standby бот остановлен"
        else
            echo "ℹ️ Standby бот уже остановлен"
        fi
        
        echo
        echo "📊 Новый статус:"
        docker ps --filter "name=aisha-bot" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    '
}

# Проверка логов основного бота
check_main_bot_logs() {
    log_section "📝 ПРОВЕРКА ОСНОВНОГО БОТА"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "📝 Последние 10 строк логов основного бота:"
        docker logs aisha-bot-polling-1 --tail 10
        
        echo
        echo "🔍 Поиск конфликтов polling:"
        if docker logs aisha-bot-polling-1 2>&1 | grep -i "conflict\|409\|too many requests" | tail -5; then
            echo "⚠️ Найдены потенциальные конфликты polling"
        else
            echo "✅ Конфликтов polling не обнаружено"
        fi
    '
}

# Реализация true standby режима (планируемое)
plan_true_standby() {
    log_section "📋 ПЛАН РЕАЛИЗАЦИИ TRUE STANDBY"
    
    log_info "Для реализации правильного standby режима необходимо:"
    echo "1. 💓 Health Check система:"
    echo "   - Мониторинг состояния основного бота"
    echo "   - Проверка API Telegram на доступность"
    echo "   - Heartbeat между инстансами"
    echo ""
    echo "2. 🔄 Failover механизм:"
    echo "   - Автоматический запуск standby при падении основного"
    echo "   - Graceful shutdown основного перед запуском standby"
    echo "   - Синхронизация состояния через Redis"
    echo ""
    echo "3. 🎛️ Центр управления:"
    echo "   - API для переключения между инстансами"
    echo "   - Веб-интерфейс для мониторинга"
    echo "   - Алерты при проблемах"
    echo ""
    log_warn "Пока что используем временное решение (один активный бот)"
}

# Тестирование после исправления
test_bot_functionality() {
    log_section "🧪 ТЕСТИРОВАНИЕ ФУНКЦИОНАЛЬНОСТИ"
    
    log_info "Рекомендуемые тесты:"
    echo "1. 💬 Отправьте текстовое сообщение боту"
    echo "2. 🎤 Отправьте голосовое сообщение (тест транскрибации)"
    echo "3. 📝 Проверьте логи: ssh aisha@192.168.0.10 'docker logs aisha-bot-polling-1 --follow'"
    echo ""
    log_info "Ожидаемые результаты:"
    echo "✅ Нет ошибок конфликта polling"
    echo "✅ Транскрибация работает (после деплоя с ffmpeg)"
    echo "✅ Быстрый отклик бота"
}

# Мониторинг после исправления
monitor_after_fix() {
    log_section "📊 МОНИТОРИНГ ПОСЛЕ ИСПРАВЛЕНИЯ"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "📊 Статистика за последние 5 минут:"
        
        # Подсчет обработанных сообщений
        handled_count=$(docker logs aisha-bot-polling-1 --since 5m 2>&1 | grep -c "is handled" || echo 0)
        error_count=$(docker logs aisha-bot-polling-1 --since 5m 2>&1 | grep -c "ERROR" || echo 0)
        conflict_count=$(docker logs aisha-bot-polling-1 --since 5m 2>&1 | grep -i -c "conflict\|409" || echo 0)
        
        echo "   • Обработанные сообщения: $handled_count"
        echo "   • Ошибки: $error_count"
        echo "   • Конфликты polling: $conflict_count"
        
        if [[ $conflict_count -eq 0 ]]; then
            echo "✅ ОТЛИЧНО: Конфликтов polling нет"
        else
            echo "❌ ПРОБЛЕМА: Найдены конфликты polling ($conflict_count)"
        fi
        
        if [[ $handled_count -gt 0 ]]; then
            echo "✅ ХОРОШО: Бот обрабатывает сообщения"
        else
            echo "⚠️ ВНИМАНИЕ: Нет обработанных сообщений за 5 минут"
        fi
    '
}

# Основная функция
main() {
    local action="${1:-fix}"
    
    log_info "🔧 Исправление standby бота Aisha"
    log_info "📍 Сервер: ${PROD_USER}@${PROD_SERVER}"
    log_info "🕒 $(date)"
    echo
    
    case "$action" in
        "status"|"s")
            check_current_status
            ;;
        "stop")
            check_current_status
            echo
            stop_standby_bot
            echo
            check_main_bot_logs
            ;;
        "test"|"t")
            test_bot_functionality
            ;;
        "monitor"|"m")
            monitor_after_fix
            ;;
        "plan"|"p")
            plan_true_standby
            ;;
        "fix"|*)
            check_current_status
            echo
            stop_standby_bot
            echo
            check_main_bot_logs
            echo
            monitor_after_fix
            echo
            test_bot_functionality
            echo
            plan_true_standby
            ;;
    esac
    
    echo
    log_info "✅ Операция завершена"
}

# Справка
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Использование: $0 [действие]"
    echo
    echo "Действия:"
    echo "  fix           - Полное исправление (по умолчанию)"
    echo "  status, s     - Только проверка статуса"
    echo "  stop          - Только остановка standby бота"
    echo "  test, t       - Инструкции для тестирования"
    echo "  monitor, m    - Мониторинг после исправления"
    echo "  plan, p       - План реализации true standby"
    echo
    echo "Примеры:"
    echo "  $0            # Полное исправление"
    echo "  $0 status     # Проверка статуса"
    echo "  $0 stop       # Остановка standby"
    exit 0
fi

# Запуск
main "$@" 