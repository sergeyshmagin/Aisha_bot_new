#!/bin/bash

# Скрипт для управления nginx контейнером в продакшене

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Переходим в корень проекта
cd "$(dirname "$0")/../.."

# Проверяем, что мы в правильной директории
if [[ ! -f "docker-compose.prod.yml" ]]; then
    log_error "Скрипт должен запускаться из корня проекта aisha-backend"
    exit 1
fi

CONTAINER_NAME="aisha-nginx-prod"
COMPOSE_FILE="docker-compose.prod.yml"

# Функция для показа статуса
show_status() {
    log_info "Статус nginx контейнера:"
    docker-compose -f $COMPOSE_FILE ps nginx || true
    
    echo -e "\nИнформация о контейнере:"
    docker inspect $CONTAINER_NAME --format='
Статус: {{.State.Status}}
Запущен: {{.State.StartedAt}}
Restart Count: {{.RestartCount}}
Memory: {{.HostConfig.Memory}}
CPUs: {{.HostConfig.CpuQuota}}' 2>/dev/null || log_warning "Контейнер не найден"
}

# Функция для показа логов
show_logs() {
    local lines=${1:-50}
    log_info "Показываем последние $lines строк логов nginx:"
    docker-compose -f $COMPOSE_FILE logs --tail=$lines nginx
}

# Функция для перезапуска
restart_nginx() {
    log_info "Перезапускаем nginx контейнер..."
    docker-compose -f $COMPOSE_FILE restart nginx
    sleep 5
    show_status
    health_check
}

# Функция для остановки
stop_nginx() {
    log_info "Останавливаем nginx контейнер..."
    docker-compose -f $COMPOSE_FILE stop nginx
    log_success "nginx остановлен"
}

# Функция для запуска
start_nginx() {
    log_info "Запускаем nginx контейнер..."
    docker-compose -f $COMPOSE_FILE up -d nginx
    sleep 5
    show_status
    health_check
}

# Функция для пересборки
rebuild_nginx() {
    log_info "Пересобираем и перезапускаем nginx контейнер..."
    docker-compose -f $COMPOSE_FILE stop nginx
    docker-compose -f $COMPOSE_FILE build --no-cache nginx
    docker-compose -f $COMPOSE_FILE up -d nginx
    sleep 5
    show_status
    health_check
}

# Функция для проверки здоровья
health_check() {
    log_info "Выполняем health check..."
    
    # Проверка HTTP
    if curl -s http://localhost/health > /dev/null; then
        log_success "HTTP health check: OK"
    else
        log_error "HTTP health check: FAILED"
    fi
    
    # Проверка HTTPS
    if curl -sk https://localhost:8443/health > /dev/null; then
        log_success "HTTPS health check: OK"
    else
        log_warning "HTTPS health check: FAILED"
    fi
    
    # Проверка webhook endpoint
    if curl -sk -X POST -H "Content-Type: application/json" -d '{}' https://localhost:8443/api/v1/avatar/status_update > /dev/null 2>&1; then
        log_success "Webhook endpoint: Доступен"
    else
        log_warning "Webhook endpoint: Возможны проблемы"
    fi
}

# Функция для показа метрик
show_metrics() {
    log_info "Метрики nginx контейнера:"
    docker stats $CONTAINER_NAME --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" 2>/dev/null || log_warning "Контейнер не запущен"
}

# Функция для показа конфигурации
show_config() {
    log_info "Текущая конфигурация nginx:"
    docker exec $CONTAINER_NAME nginx -T 2>/dev/null || log_error "Не удалось получить конфигурацию"
}

# Функция для проверки ошибок
check_errors() {
    log_info "Проверяем ошибки в логах nginx:"
    docker-compose -f $COMPOSE_FILE logs nginx 2>&1 | grep -i error || log_success "Ошибок не найдено"
}

# Функция для ротации логов
rotate_logs() {
    log_info "Выполняем ротацию логов nginx..."
    docker exec $CONTAINER_NAME nginx -s reopen 2>/dev/null && log_success "Логи ротированы" || log_error "Ошибка ротации логов"
}

# Функция для backup конфигурации
backup_config() {
    local backup_dir="backups/nginx-$(date +%Y%m%d_%H%M%S)"
    log_info "Создаем backup конфигурации в $backup_dir..."
    mkdir -p $backup_dir
    cp -r docker/nginx/* $backup_dir/
    log_success "Backup создан в $backup_dir"
}

# Функция показа помощи
show_help() {
    echo "Использование: $0 [команда]"
    echo ""
    echo "Доступные команды:"
    echo "  status      - Показать статус контейнера"
    echo "  start       - Запустить nginx"
    echo "  stop        - Остановить nginx"
    echo "  restart     - Перезапустить nginx"
    echo "  rebuild     - Пересобрать и перезапустить nginx"
    echo "  logs [n]    - Показать последние n строк логов (по умолчанию 50)"
    echo "  health      - Проверить здоровье сервиса"
    echo "  metrics     - Показать метрики контейнера"
    echo "  config      - Показать текущую конфигурацию nginx"
    echo "  errors      - Проверить ошибки в логах"
    echo "  rotate      - Ротировать логи"
    echo "  backup      - Создать backup конфигурации"
    echo "  help        - Показать эту справку"
}

# Обработка аргументов командной строки
case "${1:-help}" in
    "status")
        show_status
        ;;
    "start")
        start_nginx
        ;;
    "stop")
        stop_nginx
        ;;
    "restart")
        restart_nginx
        ;;
    "rebuild")
        rebuild_nginx
        ;;
    "logs")
        show_logs "${2:-50}"
        ;;
    "health")
        health_check
        ;;
    "metrics")
        show_metrics
        ;;
    "config")
        show_config
        ;;
    "errors")
        check_errors
        ;;
    "rotate")
        rotate_logs
        ;;
    "backup")
        backup_config
        ;;
    "help")
        show_help
        ;;
    *)
        log_error "Неизвестная команда: $1"
        show_help
        exit 1
        ;;
esac 