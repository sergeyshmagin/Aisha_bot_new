#!/bin/bash

# ============================================================================
# Скрипт запуска DEV окружения Aisha Bot
# Использует отдельный dev токен телеграм бота
# ============================================================================

set -e

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

# Проверка виртуального окружения
check_venv() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_warn "⚠️  Виртуальное окружение не активировано"
        log_info "Попытка активации..."
        if [[ -f "venv/bin/activate" ]]; then
            source venv/bin/activate
            log_info "✅ Виртуальное окружение активировано"
        else
            log_error "❌ Виртуальное окружение не найдено"
            exit 1
        fi
    else
        log_info "✅ Виртуальное окружение активно: $VIRTUAL_ENV"
    fi
}

# Проверка Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "❌ Docker не установлен"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "❌ Docker Compose не установлен"
        exit 1
    fi
    
    log_info "✅ Docker и Docker Compose доступны"
}

# Проверка доступности внешних сервисов
check_external_services() {
    log_info "🔍 Проверка доступности внешних сервисов..."
    
    # PostgreSQL
    if nc -z 192.168.0.4 5432 2>/dev/null; then
        log_info "✅ PostgreSQL (192.168.0.4:5432) доступен"
    else
        log_warn "⚠️  PostgreSQL недоступен"
    fi
    
    # Redis
    if nc -z 192.168.0.3 6379 2>/dev/null; then
        log_info "✅ Redis (192.168.0.3:6379) доступен"
    else
        log_warn "⚠️  Redis недоступен"
    fi
    
    # MinIO
    if nc -z 192.168.0.4 9000 2>/dev/null; then
        log_info "✅ MinIO (192.168.0.4:9000) доступен"
    else
        log_warn "⚠️  MinIO недоступен"
    fi
}

# Проверка dev токена
check_dev_token() {
    local dev_token="7891892225:AAHzdW0QdtQ3mpN_3aPT1eFOX-z_TWpUDJw"
    
    log_info "🤖 Проверка dev токена телеграм бота..."
    
    local response=$(curl -s "https://api.telegram.org/bot${dev_token}/getMe" 2>/dev/null || echo '{"ok":false}')
    
    if echo "$response" | grep -q '"ok":true'; then
        local username=$(echo "$response" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
        log_info "✅ Dev бот активен: @${username}"
    else
        log_warn "⚠️  Проблема с dev токеном бота"
    fi
}

# Запуск dev окружения
start_dev() {
    log_info "🚀 Запуск dev окружения..."
    
    # Остановка продакшн контейнеров на всякий случай
    docker-compose -f docker-compose.bot.simple.yml down 2>/dev/null || true
    
    # Создание .env файла если не существует
    if [[ ! -f ".env.dev" ]]; then
        log_info "📝 Создание .env.dev из шаблона..."
        cp env.dev.template .env.dev
        log_warn "⚠️  Обновите API ключи в .env.dev"
    fi
    
    # Запуск dev контейнеров
    log_info "🐳 Запуск Docker контейнеров..."
    docker-compose -f docker-compose.dev.yml up -d --build
    
    # Ожидание запуска
    log_info "⏳ Ожидание запуска сервисов..."
    sleep 10
    
    # Проверка статуса
    log_info "📊 Статус контейнеров:"
    docker-compose -f docker-compose.dev.yml ps
    
    log_info ""
    log_info "🎉 DEV окружение запущено!"
    log_info "📱 Dev токен: 7891892225:AAH...UDJw"
    log_info "📋 Просмотр логов: docker-compose -f docker-compose.dev.yml logs -f"
    log_info "🛑 Остановка: docker-compose -f docker-compose.dev.yml down"
}

# Просмотр логов
show_logs() {
    log_info "📋 Логи dev окружения:"
    docker-compose -f docker-compose.dev.yml logs -f
}

# Остановка dev окружения
stop_dev() {
    log_info "🛑 Остановка dev окружения..."
    docker-compose -f docker-compose.dev.yml down
    log_info "✅ Dev окружение остановлено"
}

# Главная функция
main() {
    case "${1:-start}" in
        "start")
            log_info "🔧 Запуск DEV окружения Aisha Bot"
            check_venv
            check_docker
            check_external_services
            check_dev_token
            start_dev
            ;;
        "logs")
            show_logs
            ;;
        "stop")
            stop_dev
            ;;
        "restart")
            stop_dev
            sleep 2
            main start
            ;;
        "status")
            log_info "📊 Статус dev окружения:"
            docker-compose -f docker-compose.dev.yml ps
            ;;
        *)
            log_info "Использование: $0 {start|stop|restart|logs|status}"
            log_info ""
            log_info "Команды:"
            log_info "  start   - Запуск dev окружения (по умолчанию)"
            log_info "  stop    - Остановка dev окружения"
            log_info "  restart - Перезапуск dev окружения"
            log_info "  logs    - Просмотр логов"
            log_info "  status  - Статус контейнеров"
            exit 1
            ;;
    esac
}

main "$@" 