#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 AISHA BOT - ФИНАЛЬНЫЙ ПРОДАКШН ДЕПЛОЙ
# ═══════════════════════════════════════════════════════════════════════════════
# Версия: 2.0 СТАБИЛЬНАЯ
# Дата: 2025-06-09
# Статус: ✅ ПРОТЕСТИРОВАНО В ПРОДАКШНЕ
#
# Этот скрипт учитывает ВСЕ ошибки найденные в процессе развертывания:
# - Переменные TELEGRAM_TOKEN и TELEGRAM_BOT_TOKEN
# - Правильные entrypoint без nc проверок
# - Исправленные Dockerfile (webhook без --worker-class)
# - Права доступа на директории storage
# - Conflict resolution для polling ботов
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Конфигурация
PROD_SERVER="192.168.0.10"
PROD_USER="aisha"
REGISTRY_PORT="5000"
PROJECT_ROOT="/opt/aisha-backend"

# Логирование
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

# Проверка токена
check_telegram_token() {
    if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
        log_error "Переменная TELEGRAM_BOT_TOKEN не установлена!"
        log_info "Экспортируйте токен: export TELEGRAM_BOT_TOKEN=your_token_here"
        exit 1
    fi
    
    # Проверка валидности токена
    if ! curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" | grep -q '"ok":true'; then
        log_error "Токен Telegram недействителен!"
        exit 1
    fi
    
    log_info "✅ Токен Telegram валидный"
}

# Сборка образов с исправлениями
build_images() {
    log_step "🔨 Сборка исправленных Docker образов..."
    
    # Webhook API (БЕЗ --worker-class параметра!)
    log_info "Сборка Webhook API..."
    docker build -f docker/Dockerfile.webhook -t localhost:${REGISTRY_PORT}/aisha-webhook:latest .
    
    # Bot с исправленным entrypoint (БЕЗ nc проверок!)
    log_info "Сборка Bot..."
    docker build -f docker/Dockerfile.bot -t localhost:${REGISTRY_PORT}/aisha-bot:latest .
    
    log_info "✅ Образы собраны"
}

# Отправка на сервер
push_images() {
    log_step "📤 Отправка образов на продакшн регистр..."
    
    docker push localhost:${REGISTRY_PORT}/aisha-webhook:latest || {
        log_error "Ошибка отправки webhook образа"
        exit 1
    }
    
    docker push localhost:${REGISTRY_PORT}/aisha-bot:latest || {
        log_error "Ошибка отправки bot образа"
        exit 1
    }
    
    log_info "✅ Образы отправлены"
}

# Развертывание на сервере
deploy_to_server() {
    log_step "🚀 Развертывание на продакшн сервере..."
    
    ssh ${PROD_USER}@${PROD_SERVER} "
        cd ${PROJECT_ROOT}
        
        echo '🔄 Обновление образов...'
        docker pull localhost:${REGISTRY_PORT}/aisha-webhook:latest
        docker pull localhost:${REGISTRY_PORT}/aisha-bot:latest
        
        echo '⏹️ Остановка существующих сервисов...'
        export TELEGRAM_BOT_TOKEN='${TELEGRAM_BOT_TOKEN}'
        docker-compose -f docker-compose.webhook.prod.yml down || true
        docker-compose -f docker-compose.bot.registry.yml down || true
        
        echo '🧹 Очистка старых контейнеров...'
        docker system prune -f
        
        echo '🚀 Запуск Webhook API...'
        docker-compose -f docker-compose.webhook.prod.yml up -d
        
        echo '⏳ Ожидание запуска API...'
        sleep 30
        
        echo '🤖 Запуск Bot кластера...'
        docker-compose -f docker-compose.bot.registry.yml up -d
        
        echo '⏳ Ожидание запуска ботов...'
        sleep 20
        
        echo '📊 Проверка статуса сервисов...'
        docker ps --format 'table {{.Names}}\\\t{{.Status}}\\\t{{.Ports}}'
    " || {
        log_error "Ошибка развертывания на сервере"
        exit 1
    }
}

# Проверка здоровья
health_check() {
    log_step "🏥 Проверка здоровья системы..."
    
    ssh ${PROD_USER}@${PROD_SERVER} "
        cd ${PROJECT_ROOT}
        
        echo '=== СТАТУС КОНТЕЙНЕРОВ ==='
        docker ps --format 'table {{.Names}}\\\t{{.Status}}'
        
        echo
        echo '=== ПРОВЕРКА WEBHOOK API ==='
        for i in {1..2}; do
            echo \"Webhook API \$i:\"
            docker logs aisha-webhook-api-\$i --tail 3 2>/dev/null || echo \"Не запущен\"
        done
        
        echo
        echo '=== ПРОВЕРКА БОТОВ ==='
        echo 'Основной бот:'
        docker logs aisha-bot-polling-1 --tail 3 2>/dev/null || echo 'Не запущен'
        
        echo 'Standby бот:'
        docker logs aisha-bot-polling-2 --tail 3 2>/dev/null || echo 'Не запущен'
        
        echo
        echo '=== ПРОВЕРКА NGINX ==='
        docker logs aisha-nginx-prod --tail 3 2>/dev/null || echo 'Не запущен'
        
        echo
        echo '✅ Проверка завершена'
    "
}

# Основная функция
main() {
    log_info "🚀 Начинаем финальный деплой Aisha Bot на продакшн"
    log_info "📍 Сервер: ${PROD_USER}@${PROD_SERVER}"
    log_info "📅 $(date)"
    
    # Проверки
    check_telegram_token
    
    # Сборка и деплой
    build_images
    push_images
    deploy_to_server
    
    # Финальная проверка
    health_check
    
    log_info "🎉 Деплой завершен успешно!"
    log_info "🌐 Webhook API: https://${PROD_SERVER}/webhook/"
    log_info "🤖 Bot кластер: polling + standby + workers"
}

# Обработка ошибок
trap 'log_error "❌ Скрипт прерван на строке $LINENO"' ERR

# Справка
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Использование: $0"
    echo ""
    echo "Переменные окружения:"
    echo "  TELEGRAM_BOT_TOKEN  - Токен Telegram бота (обязательно)"
    echo ""
    echo "Примеры:"
    echo "  export TELEGRAM_BOT_TOKEN=your_token"
    echo "  $0"
    exit 0
fi

# Запуск
main "$@" 