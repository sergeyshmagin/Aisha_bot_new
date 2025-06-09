#!/bin/bash

# ============================================================================
# Скрипт диагностики состояния продакшн сервисов Aisha Bot
# ============================================================================

set -e

# Конфигурация
PRODUCTION_SERVER="192.168.0.10"
SSH_USER="aisha"
DOMAIN="aibots.kz"

# Параметры командной строки
USE_SSH=true
DETAILED=false

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции логирования
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Показать справку
show_help() {
    cat << EOF
Использование: $0 [опции]

Скрипт диагностики состояния продакшн сервисов Aisha Bot

Опции:
  --local             Диагностика локально (без SSH)
  --detailed          Подробная диагностика с логами
  -h, --help          Показать эту справку

Примеры:
  $0                  # Диагностика на продакшн сервере
  $0 --detailed       # Подробная диагностика
  $0 --local          # Локальная диагностика

EOF
}

# Обработка параметров командной строки
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --local)
                USE_SSH=false
                shift
                ;;
            --detailed)
                DETAILED=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            --*)
                log_error "Неизвестный параметр: $1"
                log_info "Используйте '$0 --help' для справки"
                exit 1
                ;;
            *)
                log_error "Неожиданный аргумент: $1"
                log_info "Используйте '$0 --help' для справки"
                exit 1
                ;;
        esac
    done
}

# Выполнение команды на сервере
exec_cmd() {
    local cmd="$1"
    
    if [[ "$USE_SSH" == "true" ]]; then
        ssh -o StrictHostKeyChecking=no "$SSH_USER@$PRODUCTION_SERVER" "$cmd"
    else
        eval "$cmd"
    fi
}

# Проверка доступности сервера
check_server() {
    if [[ "$USE_SSH" == "false" ]]; then
        log_info "📍 Локальная диагностика"
        return 0
    fi
    
    log_step "🌐 Проверка доступности продакшн сервера..."
    
    if ping -c 1 -W 5 "$PRODUCTION_SERVER" >/dev/null 2>&1; then
        log_info "✅ Сервер $PRODUCTION_SERVER доступен"
    else
        log_error "❌ Сервер $PRODUCTION_SERVER недоступен"
        exit 1
    fi
    
    if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SSH_USER@$PRODUCTION_SERVER" "echo 'SSH OK'" >/dev/null 2>&1; then
        log_info "✅ SSH доступ работает"
    else
        log_error "❌ SSH доступ не работает"
        exit 1
    fi
}

# Проверка Docker
check_docker() {
    log_step "🐳 Проверка Docker..."
    
    if exec_cmd "command -v docker >/dev/null 2>&1"; then
        log_info "✅ Docker установлен"
    else
        log_error "❌ Docker не установлен"
        exit 1
    fi
    
    if exec_cmd "docker info >/dev/null 2>&1"; then
        log_info "✅ Docker служба запущена и доступна"
    else
        log_error "❌ Docker служба недоступна"
        # Не выходим, продолжаем диагностику
    fi
}

# Проверка Docker сетей
check_networks() {
    log_step "🌐 Проверка Docker сетей..."
    
    local networks=$(exec_cmd "docker network ls --filter name=aisha --format '{{.Name}}' 2>/dev/null || true")
    
    if echo "$networks" | grep -q "aisha_cluster"; then
        log_info "✅ Сеть aisha_cluster существует"
    else
        log_warn "⚠️ Сеть aisha_cluster не найдена"
    fi
    
    if echo "$networks" | grep -q "aisha_bot_cluster"; then
        log_info "✅ Сеть aisha_bot_cluster существует"
    else
        log_warn "⚠️ Сеть aisha_bot_cluster не найдена"
    fi
}

# Проверка контейнеров
check_containers() {
    log_step "📦 Проверка состояния контейнеров..."
    
    echo ""
    log_info "📊 Статус контейнеров:"
    exec_cmd "docker ps --filter 'name=aisha' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || echo 'Нет запущенных Aisha контейнеров'"
    
    echo ""
    local containers=$(exec_cmd "docker ps -a --filter 'name=aisha' --format '{{.Names}} {{.Status}}' 2>/dev/null || true")
    
    if [[ -z "$containers" ]]; then
        log_warn "⚠️ Контейнеры Aisha не найдены"
        return
    fi
    
    # Анализ статуса контейнеров
    echo "$containers" | while read -r name status; do
        if echo "$status" | grep -q "Up"; then
            log_info "✅ $name: Запущен"
        elif echo "$status" | grep -q "Restarting"; then
            log_error "❌ $name: Перезапускается (проблема)"
        elif echo "$status" | grep -q "Exited"; then
            log_error "❌ $name: Остановлен"
        else
            log_warn "⚠️ $name: $status"
        fi
    done
}

# Проверка логов проблемных контейнеров
check_logs() {
    if [[ "$DETAILED" != "true" ]]; then
        return
    fi
    
    log_step "📋 Проверка логов проблемных контейнеров..."
    
    local problem_containers=$(exec_cmd "docker ps -a --filter 'name=aisha' --format '{{.Names}} {{.Status}}' | grep -E '(Restarting|Exited)' | cut -d' ' -f1" 2>/dev/null || true)
    
    if [[ -z "$problem_containers" ]]; then
        log_info "✅ Проблемных контейнеров не найдено"
        return
    fi
    
    echo "$problem_containers" | while read -r container; do
        if [[ -n "$container" ]]; then
            log_info "📋 Логи контейнера $container:"
            echo "----------------------------------------"
            exec_cmd "docker logs $container --tail 10 2>&1" || true
            echo "----------------------------------------"
            echo ""
        fi
    done
}

# Проверка доступности сервисов
check_services() {
    log_step "🌐 Проверка доступности сервисов..."
    
    # HTTP порт 80
    if exec_cmd "curl -f -s -m 5 http://localhost/ >/dev/null 2>&1"; then
        log_info "✅ HTTP (порт 80) доступен"
    else
        log_error "❌ HTTP (порт 80) недоступен"
    fi
    
    # HTTPS порт 8443
    if exec_cmd "curl -f -s -k -m 5 https://localhost:8443/ >/dev/null 2>&1"; then
        log_info "✅ HTTPS (порт 8443) доступен"
    else
        log_error "❌ HTTPS (порт 8443) недоступен"
    fi
    
    # Внешний доступ
    if ping -c 1 -W 3 "$PRODUCTION_SERVER" >/dev/null 2>&1; then
        if curl -f -s -m 5 "http://$DOMAIN/" >/dev/null 2>&1; then
            log_info "✅ Внешний HTTP доступ работает"
        else
            log_warn "⚠️ Внешний HTTP доступ недоступен"
        fi
        
        if curl -f -s -k -m 5 "https://$DOMAIN:8443/" >/dev/null 2>&1; then
            log_info "✅ Внешний HTTPS доступ работает"
        else
            log_warn "⚠️ Внешний HTTPS доступ недоступен"
        fi
    fi
}

# Проверка использования ресурсов
check_resources() {
    log_step "💻 Проверка использования ресурсов..."
    
    local stats=$(exec_cmd "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}' --filter 'name=aisha' 2>/dev/null || true")
    
    if [[ -n "$stats" ]]; then
        echo ""
        log_info "📊 Использование ресурсов:"
        echo "$stats"
    else
        log_warn "⚠️ Статистика ресурсов недоступна"
    fi
}

# Рекомендации по устранению проблем
show_recommendations() {
    log_step "💡 Рекомендации..."
    
    local has_problems=false
    
    # Проверяем, есть ли проблемные контейнеры
    local problem_containers=$(exec_cmd "docker ps -a --filter 'name=aisha' --format '{{.Names}} {{.Status}}' | grep -E '(Restarting|Exited)'" 2>/dev/null || true)
    
    if [[ -n "$problem_containers" ]]; then
        has_problems=true
        echo ""
        log_warn "🔧 Для устранения проблем:"
        log_info "   • Просмотр логов: docker logs <container_name>"
        log_info "   • Перезапуск сервисов: cd /opt/aisha-backend && docker-compose -f docker-compose.registry.yml restart"
        log_info "   • Полное пересоздание: cd /opt/aisha-backend && docker-compose -f docker-compose.registry.yml down && docker-compose -f docker-compose.registry.yml up -d"
    fi
    
    if [[ "$has_problems" == "false" ]]; then
        log_info "🎉 Все сервисы работают корректно!"
    fi
    
    echo ""
    log_info "📋 Полезные команды:"
    if [[ "$USE_SSH" == "true" ]]; then
        log_info "   • SSH подключение: ssh $SSH_USER@$PRODUCTION_SERVER"
        log_info "   • Мониторинг: ssh $SSH_USER@$PRODUCTION_SERVER 'docker ps'"
        log_info "   • Логи: ssh $SSH_USER@$PRODUCTION_SERVER 'docker logs <container>'"
    else
        log_info "   • Мониторинг: docker ps"
        log_info "   • Логи: docker logs <container>"
        log_info "   • Статистика: docker stats"
    fi
}

# Основная функция
main() {
    parse_args "$@"
    
    log_info "🔍 Диагностика состояния продакшн сервисов Aisha Bot"
    
    if [[ "$USE_SSH" == "true" ]]; then
        log_info "🎯 Сервер: $PRODUCTION_SERVER"
    else
        log_info "📍 Локальная диагностика"
    fi
    
    if [[ "$DETAILED" == "true" ]]; then
        log_info "🔬 Подробная диагностика включена"
    fi
    
    echo ""
    
    # Выполнение проверок
    check_server
    check_docker
    check_networks
    check_containers
    check_logs
    check_services
    check_resources
    show_recommendations
}

# Запуск
main "$@" 