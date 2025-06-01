#!/bin/bash

# 🚀 Скрипт развертывания Aisha Bot v2 (только приложения)

set -e

# Конфигурация
DEPLOY_DIR="/opt/aisha-v2"
BACKUP_DIR="/opt/backups/aisha-v2"
SERVICE_NAME="aisha-bot"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

check_external_services() {
    log "🔍 Проверка внешних сервисов..."
    
    if ! ./docker/scripts/health-check.sh; then
        log_error "Внешние сервисы недоступны. Остановка развертывания."
        exit 1
    fi
    
    log_success "Все внешние сервисы доступны"
}

backup_current() {
    if [ -d "$DEPLOY_DIR" ]; then
        log "📦 Создание бэкапа текущей версии..."
        
        mkdir -p "$BACKUP_DIR"
        
        local backup_name="aisha-v2-$(date +%Y%m%d-%H%M%S).tar.gz"
        
        if tar -czf "$BACKUP_DIR/$backup_name" -C "$DEPLOY_DIR" .; then
            log_success "Бэкап создан: $backup_name"
            
            # Удаление старых бэкапов (оставляем последние 5)
            cd "$BACKUP_DIR"
            ls -t aisha-v2-*.tar.gz | tail -n +6 | xargs -r rm
            log "🧹 Старые бэкапы очищены"
        else
            log_warning "Не удалось создать бэкап, продолжаем..."
        fi
    fi
}

validate_environment() {
    log "🔍 Проверка конфигурации..."
    
    local env_file=".env.docker.prod"
    if [ "$ENVIRONMENT" = "development" ]; then
        env_file=".env.docker.dev"
        COMPOSE_FILE="docker-compose.yml"
    fi
    
    if [ ! -f "$DEPLOY_DIR/$env_file" ]; then
        log_error "Файл $env_file не найден в $DEPLOY_DIR"
        exit 1
    fi
    
    if [ ! -f "$DEPLOY_DIR/$COMPOSE_FILE" ]; then
        log_error "Файл $COMPOSE_FILE не найден в $DEPLOY_DIR"
        exit 1
    fi
    
    log_success "Конфигурация валидна"
}

deploy_application() {
    log "🚀 Развертывание приложений..."
    
    cd "$DEPLOY_DIR"
    
    # Остановка существующих контейнеров
    if docker-compose -f "$COMPOSE_FILE" ps -q 2>/dev/null | grep -q .; then
        log "🛑 Остановка существующих контейнеров..."
        docker-compose -f "$COMPOSE_FILE" down
    fi
    
    # Очистка старых образов
    log "🧹 Очистка неиспользуемых образов..."
    docker image prune -f
    
    # Сборка новых образов
    log "🔨 Сборка Docker образов..."
    if ! docker-compose -f "$COMPOSE_FILE" build --no-cache; then
        log_error "Ошибка сборки образов"
        exit 1
    fi
    
    # Запуск сервисов
    log "🚀 Запуск приложений..."
    if ! docker-compose -f "$COMPOSE_FILE" up -d; then
        log_error "Ошибка запуска приложений"
        exit 1
    fi
    
    # Ожидание готовности сервисов
    log "⏳ Ожидание готовности приложений (60 секунд)..."
    sleep 60
    
    # Проверка состояния контейнеров
    local failed_containers=$(docker-compose -f "$COMPOSE_FILE" ps --filter "status=exited" --format "table {{.Name}}")
    
    if [ -n "$failed_containers" ] && [ "$failed_containers" != "NAME" ]; then
        log_error "Некоторые контейнеры не запустились:"
        echo "$failed_containers"
        log "📋 Логи неудачных контейнеров:"
        docker-compose -f "$COMPOSE_FILE" logs --tail=50
        exit 1
    fi
    
    log_success "Все приложения запущены успешно"
}

run_health_checks() {
    log "🏥 Проверка здоровья приложений..."
    
    local health_ok=true
    
    # Проверка API эндпоинта
    for i in {1..10}; do
        if curl -f -s "http://localhost:8443/health" >/dev/null 2>&1; then
            log_success "API сервер отвечает"
            break
        else
            if [ $i -eq 10 ]; then
                log_error "API сервер не отвечает после 10 попыток"
                health_ok=false
            else
                log "🔄 Попытка $i/10: API сервер не готов, ждем..."
                sleep 5
            fi
        fi
    done
    
    # Проверка Nginx (только в production)
    if [ "$COMPOSE_FILE" = "docker-compose.prod.yml" ]; then
        if curl -f -s "http://localhost/health" >/dev/null 2>&1; then
            log_success "Nginx работает"
        else
            log_error "Nginx не отвечает"
            health_ok=false
        fi
    fi
    
    if [ "$health_ok" = false ]; then
        log_error "Проверки здоровья не прошли"
        log "📋 Логи приложений:"
        docker-compose -f "$COMPOSE_FILE" logs --tail=50
        exit 1
    fi
    
    log_success "Все проверки здоровья прошли"
}

setup_systemd() {
    if [ "$COMPOSE_FILE" = "docker-compose.prod.yml" ]; then
        log "⚙️ Настройка systemd сервиса..."
        
        sudo tee /etc/systemd/system/aisha-bot.service > /dev/null <<EOF
[Unit]
Description=Aisha Bot v2 Production
Documentation=https://github.com/your-org/aisha-bot-v2
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
WorkingDirectory=$DEPLOY_DIR
Environment=COMPOSE_PROJECT_NAME=aisha-v2-prod
ExecStartPre=/usr/bin/docker-compose -f $COMPOSE_FILE down
ExecStart=/usr/bin/docker-compose -f $COMPOSE_FILE up -d
ExecStop=/usr/bin/docker-compose -f $COMPOSE_FILE down
ExecReload=/usr/bin/docker-compose -f $COMPOSE_FILE restart
TimeoutStartSec=300
TimeoutStopSec=60
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        sudo systemctl daemon-reload
        sudo systemctl enable aisha-bot
        
        log_success "Systemd сервис настроен и включен"
    else
        log "⏭️ Systemd сервис настраивается только для production"
    fi
}

show_status() {
    log "📊 Статус развертывания:"
    echo ""
    echo "🐳 Статус контейнеров:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    echo "📈 Использование ресурсов:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
    echo ""
    echo "🔗 Доступные эндпоинты:"
    echo "  - API: http://localhost:8443/health"
    if [ "$COMPOSE_FILE" = "docker-compose.prod.yml" ]; then
        echo "  - Nginx: http://localhost/health"
    fi
    echo ""
    echo "📝 Полезные команды:"
    echo "  - Логи: docker-compose -f $COMPOSE_FILE logs -f"
    if [ "$COMPOSE_FILE" = "docker-compose.prod.yml" ]; then
        echo "  - Статус: sudo systemctl status aisha-bot"
        echo "  - Перезапуск: sudo systemctl restart aisha-bot"
    fi
    echo "  - Проверка БД: ./docker/scripts/health-check.sh"
}

# Основная логика
main() {
    log "🏁 Начинаем развертывание Aisha Bot v2 на $(hostname)..."
    
    # Проверка прав
    if [ "$EUID" -eq 0 ]; then
        log_error "Не запускайте скрипт от root. Используйте sudo только для системных операций."
        exit 1
    fi
    
    # Проверка Docker
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker не установлен"
        exit 1
    fi
    
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "Docker Compose не установлен"
        exit 1
    fi
    
    # Создание директории развертывания
    sudo mkdir -p "$DEPLOY_DIR"
    sudo chown $USER:$USER "$DEPLOY_DIR"
    
    # Основные этапы
    check_external_services
    backup_current
    validate_environment
    deploy_application
    run_health_checks
    setup_systemd
    show_status
    
    log_success "🎉 Развертывание завершено успешно!"
}

# Обработка аргументов
case "${1:-}" in
    "health")
        check_external_services
        run_health_checks
        ;;
    "status")
        show_status
        ;;
    "dev")
        export ENVIRONMENT="development"
        export COMPOSE_FILE="docker-compose.yml"
        main "$@"
        ;;
    *)
        main "$@"
        ;;
esac 