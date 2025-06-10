#!/bin/bash

# 🚀 Деплой Aisha Bot с использованием Docker Registry
# Использует HTTP registry на 192.168.0.4:5000

set -euo pipefail

# Конфигурация
REGISTRY_HOST="192.168.0.4"
REGISTRY_PORT="5000"
REGISTRY_URL="${REGISTRY_HOST}:${REGISTRY_PORT}"
PROJECT_NAME="aisha"
PRODUCTION_HOST="192.168.0.10"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >&2
}

check_prerequisites() {
    log "🔍 Проверка предварительных условий..."
    
    # Проверка Docker Registry
    if ! curl -f "http://${REGISTRY_URL}/v2/" &>/dev/null; then
        log_error "❌ Docker Registry недоступен: http://${REGISTRY_URL}"
        exit 1
    fi
    log "✅ Docker Registry доступен"
    
    # Проверка подключения к продакшн
    if ! ssh -o ConnectTimeout=5 aisha@${PRODUCTION_HOST} 'echo "OK"' &>/dev/null; then
        log_error "❌ Продакшн сервер недоступен: ${PRODUCTION_HOST}"
        exit 1
    fi
    log "✅ Продакшн сервер доступен"
    
    # Проверка insecure registry настройки
    if ! docker info 2>/dev/null | grep -q "Insecure Registries:" || ! docker info 2>/dev/null | grep -A 10 "Insecure Registries:" | grep -q "${REGISTRY_URL}"; then
        log_error "❌ Insecure registry не настроен. Запустите: scripts/docker-registry/setup-insecure-registry.sh"
        exit 1
    fi
    log "✅ Insecure registry настроен"
}

build_and_push_image() {
    local service=$1
    local version=${2:-latest}
    local image_name="${REGISTRY_URL}/${PROJECT_NAME}/${service}:${version}"
    
    log "🔨 Сборка образа $service..."
    
    case $service in
        "bot")
            docker build -f docker/Dockerfile.bot -t "$image_name" .
            ;;
        "webhook")
            docker build -f docker/Dockerfile.webhook -t "$image_name" .
            ;;
        *)
            log_error "❌ Неизвестный сервис: $service"
            return 1
            ;;
    esac
    
    log "📤 Push образа в registry..."
    docker push "$image_name"
    
    log "✅ Образ $service готов: $image_name"
    echo "$image_name"
}

deploy_to_production() {
    local images=("$@")
    
    log "🚀 Развертывание на продакшн сервере..."
    
    # Передача скриптов на продакшн
    scp scripts/production/fix-environment.sh aisha@${PRODUCTION_HOST}:/tmp/
    scp scripts/production/safe-cleanup.sh aisha@${PRODUCTION_HOST}:/tmp/
    
    # Выполнение развертывания
    ssh aisha@${PRODUCTION_HOST} << EOF
        set -euo pipefail
        cd /opt/aisha-backend
        
        echo "🔧 Исправление окружения..."
        chmod +x /tmp/fix-environment.sh
        /tmp/fix-environment.sh
        
        echo "🐳 Pull новых образов..."
        for image in ${images[@]}; do
            docker pull \$image
        done
        
        echo "🔄 Обновление docker-compose..."
        # Обновляем image теги в docker-compose файлах
        # (здесь можно добавить sed команды для автоматического обновления)
        
        echo "📦 Перезапуск сервисов..."
        docker-compose -f docker-compose.bot.registry.yml down
        docker-compose -f docker-compose.bot.registry.yml up -d
        
        echo "⏰ Ожидание запуска..."
        sleep 30
        
        echo "📊 Проверка статуса..."
        docker-compose -f docker-compose.bot.registry.yml ps
EOF
    
    log "✅ Развертывание завершено"
}

run_health_checks() {
    log "🏥 Проверка здоровья сервисов..."
    
    ssh aisha@${PRODUCTION_HOST} << 'EOF'
        cd /opt/aisha-backend
        
        echo "=== Статус контейнеров ==="
        docker-compose -f docker-compose.bot.registry.yml ps
        
        echo -e "\n=== Проверка логов ==="
        for container in $(docker-compose -f docker-compose.bot.registry.yml ps -q); do
            container_name=$(docker inspect --format '{{.Name}}' $container | sed 's/^.//')
            echo "--- Логи $container_name (последние 5 строк) ---"
            docker logs $container --tail 5 2>&1 | head -5
        done
        
        echo -e "\n=== Внешние зависимости ==="
        nc -z 192.168.0.4 5432 && echo "✅ PostgreSQL" || echo "❌ PostgreSQL"
        nc -z 192.168.0.3 6379 && echo "✅ Redis" || echo "❌ Redis"
        nc -z 192.168.0.4 5000 && echo "✅ Docker Registry" || echo "❌ Docker Registry"
EOF
}

show_deployment_info() {
    log "📋 Информация о развертывании:"
    
    echo "🌐 Registry: http://${REGISTRY_URL}"
    echo "🖥️  Registry UI: http://${REGISTRY_HOST}:8080"
    echo "🏭 Продакшн: ${PRODUCTION_HOST}"
    echo ""
    echo "📊 Управление:"
    echo "  • Логи: ssh aisha@${PRODUCTION_HOST} 'cd /opt/aisha-backend && docker-compose -f docker-compose.bot.registry.yml logs -f'"
    echo "  • Статус: ssh aisha@${PRODUCTION_HOST} 'cd /opt/aisha-backend && docker-compose -f docker-compose.bot.registry.yml ps'"
    echo "  • Перезапуск: ssh aisha@${PRODUCTION_HOST} 'cd /opt/aisha-backend && docker-compose -f docker-compose.bot.registry.yml restart'"
}

main() {
    local services=("${@:-bot}")  # По умолчанию деплоим только bot
    local version=$(date +%Y%m%d_%H%M%S)
    
    log "🚀 Запуск деплоя Aisha Bot"
    log "📦 Сервисы: ${services[*]}"
    log "🏷️  Версия: $version"
    
    # Предварительные проверки
    check_prerequisites
    
    # Сборка и push образов
    local built_images=()
    for service in "${services[@]}"; do
        image=$(build_and_push_image "$service" "$version")
        built_images+=("$image")
    done
    
    # Развертывание
    deploy_to_production "${built_images[@]}"
    
    # Проверка здоровья
    run_health_checks
    
    # Информация
    show_deployment_info
    
    log "🎉 Деплой завершен успешно!"
}

# Запуск скрипта
main "$@" 