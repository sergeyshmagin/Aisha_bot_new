#!/bin/bash

# 🔧 Исправление проблем окружения на продакшн
# Этот скрипт проверяет и исправляет критические проблемы

set -euo pipefail

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >&2
}

log_warning() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >&2
}

check_telegram_token() {
    log "🔍 Проверка Telegram Bot Token..."
    
    if [[ -f ".env" ]]; then
        if grep -q "TELEGRAM_BOT_TOKEN=" .env && grep "TELEGRAM_BOT_TOKEN=" .env | grep -v "^$" | grep -v "TELEGRAM_BOT_TOKEN=$"; then
            log "✅ Telegram токен найден в .env"
            return 0
        else
            log_error "❌ Telegram токен отсутствует или пустой в .env"
            return 1
        fi
    else
        log_error "❌ Файл .env не найден"
        return 1
    fi
}

fix_telegram_token() {
    log_warning "🔧 Для исправления токена необходимо:"
    echo "1. Получить токен от @BotFather в Telegram"
    echo "2. Добавить строку в .env файл:"
    echo "   TELEGRAM_BOT_TOKEN=your_bot_token_here"
    echo "3. Перезапустить контейнеры"
    echo ""
    echo "Хотите добавить токен сейчас? [y/N]"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Введите токен Telegram бота:"
        read -r token
        if [[ -n "$token" ]]; then
            # Удаляем старые строки с токеном
            sed -i '/^TELEGRAM_BOT_TOKEN=/d' .env 2>/dev/null || true
            # Добавляем новый токен
            echo "TELEGRAM_BOT_TOKEN=$token" >> .env
            log "✅ Токен добавлен в .env"
        else
            log_error "❌ Токен не может быть пустым"
        fi
    fi
}

ensure_docker_networks() {
    log "🔧 Проверка Docker сетей..."
    
    # Список необходимых сетей
    networks=("aisha_cluster" "aisha_bot_cluster")
    
    for network in "${networks[@]}"; do
        if ! docker network ls | grep -q "$network"; then
            log "🔗 Создание сети $network..."
            if [[ "$network" == "aisha_bot_cluster" ]]; then
                docker network create --subnet=172.26.0.0/16 "$network"
            else
                docker network create "$network"
            fi
            log "✅ Сеть $network создана"
        else
            log "✅ Сеть $network уже существует"
        fi
    done
}

check_required_services() {
    log "🔍 Проверка внешних сервисов..."
    
    # Проверка PostgreSQL
    if nc -z 192.168.0.4 5432 2>/dev/null; then
        log "✅ PostgreSQL доступен (192.168.0.4:5432)"
    else
        log_error "❌ PostgreSQL недоступен (192.168.0.4:5432)"
    fi
    
    # Проверка Redis
    if nc -z 192.168.0.3 6379 2>/dev/null; then
        log "✅ Redis доступен (192.168.0.3:6379)"
    else
        log_error "❌ Redis недоступен (192.168.0.3:6379)"
    fi
    
    # Проверка Docker Registry
    if nc -z 192.168.0.4 5000 2>/dev/null; then
        log "✅ Docker Registry доступен (192.168.0.4:5000)"
    else
        log_error "❌ Docker Registry недоступен (192.168.0.4:5000)"
    fi
}

restart_services() {
    log "🔄 Перезапуск сервисов..."
    
    # Останавливаем контейнеры
    docker-compose -f docker-compose.bot.registry.yml down || true
    
    # Запускаем заново
    docker-compose -f docker-compose.bot.registry.yml up -d
    
    log "✅ Сервисы перезапущены"
}

show_status() {
    log "📊 Статус системы:"
    
    echo "=== Docker контейнеры ==="
    docker-compose -f docker-compose.bot.registry.yml ps
    
    echo -e "\n=== Docker сети ==="
    docker network ls | grep aisha || echo "Сети не найдены"
    
    echo -e "\n=== Переменные окружения ==="
    if check_telegram_token; then
        echo "✅ TELEGRAM_BOT_TOKEN: настроен"
    else
        echo "❌ TELEGRAM_BOT_TOKEN: отсутствует"
    fi
    
    echo -e "\n=== Внешние сервисы ==="
    check_required_services
}

main() {
    log "🚀 Запуск диагностики и исправления окружения"
    
    # Проверяем, что мы в правильной директории
    if [[ ! -f "docker-compose.bot.registry.yml" ]]; then
        log_error "❌ Запустите скрипт из корня проекта"
        exit 1
    fi
    
    # Создаем необходимые сети
    ensure_docker_networks
    
    # Проверяем токен
    if ! check_telegram_token; then
        fix_telegram_token
    fi
    
    # Проверяем внешние сервисы
    check_required_services
    
    # Показываем статус
    show_status
    
    # Предлагаем перезапуск
    echo ""
    echo "Хотите перезапустить сервисы? [y/N]"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        restart_services
        sleep 10
        show_status
    fi
    
    log "✅ Диагностика завершена"
}

# Запуск скрипта
main "$@" 