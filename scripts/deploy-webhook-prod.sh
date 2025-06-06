#!/bin/bash

# =============================================================================
# Скрипт развертывания Webhook API на продакшн сервер
# Целевой сервер: 192.168.0.10 (aibots.kz)
# =============================================================================

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Константы
PROD_SERVER="192.168.0.10"
PROD_USER="aisha"
INFRA_REGISTRY="192.168.0.4:5000"
PROJECT_NAME="aisha-webhook-api"
COMPOSE_FILE="docker-compose.webhook.prod.yml"

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

# Проверка окружения
check_environment() {
    log_info "🔍 Проверка окружения развертывания..."
    
    # Проверяем наличие необходимых файлов
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Файл $COMPOSE_FILE не найден!"
        exit 1
    fi
    
    if [[ ! -f "docker/Dockerfile.webhook" ]]; then
        log_error "Dockerfile для webhook API не найден!"
        exit 1
    fi
    
    if [[ ! -f "docker/nginx/nginx.conf" ]]; then
        log_error "Конфигурация nginx не найдена!"
        exit 1
    fi
    
    # Проверяем доступность продакшн сервера
    if ! ping -c 1 "$PROD_SERVER" &> /dev/null; then
        log_error "Продакшн сервер $PROD_SERVER недоступен!"
        exit 1
    fi
    
    log_success "Окружение проверено успешно"
}

# Сборка образов
build_images() {
    log_info "🔨 Сборка образов для webhook API..."
    
    # Сборка nginx образа
    log_info "📦 Сборка nginx reverse proxy..."
    docker build -t "${INFRA_REGISTRY}/aisha-nginx-webhook:latest" \
        -f docker/nginx/Dockerfile docker/nginx/
    
    # Сборка webhook API образа
    log_info "🚀 Сборка webhook API..."
    docker build -t "${INFRA_REGISTRY}/aisha-webhook-api:latest" \
        -f docker/Dockerfile.webhook \
        --target production .
    
    log_success "Образы собраны успешно"
}

# Отправка образов в registry
push_images() {
    log_info "📤 Отправка образов в registry..."
    
    docker push "${INFRA_REGISTRY}/aisha-nginx-webhook:latest"
    docker push "${INFRA_REGISTRY}/aisha-webhook-api:latest"
    
    log_success "Образы отправлены в registry"
}

# Подготовка продакшн сервера
prepare_production() {
    log_info "🛠️ Подготовка продакшн сервера..."
    
    # Создаем рабочую директорию
    ssh "$PROD_USER@$PROD_SERVER" "mkdir -p /opt/aisha-webhook"
    
    # Копируем необходимые файлы
    log_info "📋 Копирование конфигураций..."
    scp "$COMPOSE_FILE" "$PROD_USER@$PROD_SERVER:/opt/aisha-webhook/"
    scp -r ssl/ "$PROD_USER@$PROD_SERVER:/opt/aisha-webhook/" || log_warning "SSL сертификаты не скопированы"
    scp .env.example "$PROD_USER@$PROD_SERVER:/opt/aisha-webhook/.env.example"
    
    # Создаем .env файл если его нет
    ssh "$PROD_USER@$PROD_SERVER" << 'EOF'
cd /opt/aisha-webhook
if [[ ! -f .env ]]; then
    echo "🔧 Создание .env файла..."
    cp .env.example .env
    
    # Обновляем настройки для продакшн
    sed -i 's/DEBUG=true/DEBUG=false/' .env
    sed -i 's/SSL_ENABLED=false/SSL_ENABLED=false/' .env
    sed -i 's/API_PORT=8000/API_PORT=8001/' .env
    
    echo "⚠️  Пожалуйста, проверьте и обновите .env файл с актуальными значениями"
fi
EOF
    
    log_success "Продакшн сервер подготовлен"
}

# Развертывание контейнеров
deploy_containers() {
    log_info "🚀 Развертывание webhook API на продакшн..."
    
    ssh "$PROD_USER@$PROD_SERVER" << EOF
cd /opt/aisha-webhook

# Останавливаем старые контейнеры
echo "🛑 Остановка старых контейнеров..."
docker-compose -f $COMPOSE_FILE down --remove-orphans || true

# Загружаем новые образы
echo "📥 Загрузка образов..."
docker pull ${INFRA_REGISTRY}/aisha-nginx-webhook:latest
docker pull ${INFRA_REGISTRY}/aisha-webhook-api:latest

# Обновляем docker-compose файл для использования образов из registry
sed -i 's|build:|# build:|g' $COMPOSE_FILE
sed -i 's|context:|# context:|g' $COMPOSE_FILE
sed -i 's|dockerfile:|# dockerfile:|g' $COMPOSE_FILE
sed -i 's|target:|# target:|g' $COMPOSE_FILE

# Добавляем image директивы
sed -i '/webhook-api-1:/a\\    image: ${INFRA_REGISTRY}/aisha-webhook-api:latest' $COMPOSE_FILE
sed -i '/webhook-api-2:/a\\    image: ${INFRA_REGISTRY}/aisha-webhook-api:latest' $COMPOSE_FILE
sed -i '/nginx:/a\\    image: ${INFRA_REGISTRY}/aisha-nginx-webhook:latest' $COMPOSE_FILE

# Запускаем новые контейнеры
echo "🚀 Запуск контейнеров..."
docker-compose -f $COMPOSE_FILE up -d

# Проверяем статус
echo "📊 Проверка статуса..."
sleep 10
docker-compose -f $COMPOSE_FILE ps
EOF
    
    log_success "Контейнеры развернуты"
}

# Проверка развертывания
verify_deployment() {
    log_info "✅ Проверка развертывания..."
    
    # Проверяем доступность webhook endpoint
    log_info "🔗 Проверка webhook endpoint..."
    sleep 15  # Ждем полного запуска
    
    if curl -f -s "https://aibots.kz:8443/health" > /dev/null; then
        log_success "✅ Webhook API доступен по HTTPS"
    else
        log_warning "⚠️  HTTPS endpoint недоступен, проверяем HTTP..."
        if curl -f -s "http://$PROD_SERVER/health" > /dev/null; then
            log_success "✅ Webhook API доступен по HTTP"
        else
            log_error "❌ Webhook API недоступен!"
            return 1
        fi
    fi
    
    # Проверяем логи
    log_info "📋 Проверка логов..."
    ssh "$PROD_USER@$PROD_SERVER" << 'EOF'
cd /opt/aisha-webhook
echo "=== Логи webhook-api-1 ==="
docker-compose -f docker-compose.webhook.prod.yml logs --tail=10 webhook-api-1
echo "=== Логи nginx ==="
docker-compose -f docker-compose.webhook.prod.yml logs --tail=10 nginx
EOF
    
    log_success "Развертывание проверено"
}

# Настройка мониторинга
setup_monitoring() {
    log_info "📊 Настройка мониторинга..."
    
    ssh "$PROD_USER@$PROD_SERVER" << 'EOF'
# Создаем systemd сервис для мониторинга
sudo tee /etc/systemd/system/aisha-webhook-monitor.service > /dev/null << 'SERVICE'
[Unit]
Description=Aisha Webhook API Monitor
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/bin/docker-compose -f /opt/aisha-webhook/docker-compose.webhook.prod.yml ps
ExecStartPost=/usr/bin/curl -f http://localhost:8443/health
User=aisha
WorkingDirectory=/opt/aisha-webhook

[Install]
WantedBy=multi-user.target
SERVICE

# Создаем cron задачу для health check
(crontab -l 2>/dev/null; echo "*/5 * * * * curl -f http://localhost:8443/health > /dev/null || echo 'Webhook API down' | logger") | crontab -

sudo systemctl daemon-reload
EOF
    
    log_success "Мониторинг настроен"
}

# Главная функция
main() {
    echo "========================================"
    echo "🚀 Развертывание Aisha Webhook API"
    echo "📍 Целевой сервер: $PROD_SERVER"
    echo "========================================"
    
    check_environment
    build_images
    push_images
    prepare_production
    deploy_containers
    verify_deployment
    setup_monitoring
    
    echo "========================================"
    log_success "✅ Развертывание завершено успешно!"
    echo "🔗 Webhook URL: https://aibots.kz:8443/api/v1/avatar/status_update"
    echo "📊 Мониторинг: http://aibots.kz:9090"
    echo "📋 Логи: ssh $PROD_USER@$PROD_SERVER 'cd /opt/aisha-webhook && docker-compose logs -f'"
    echo "========================================"
}

# Обработка аргументов
case "${1:-}" in
    "build")
        build_images
        ;;
    "push")
        push_images
        ;;
    "deploy")
        deploy_containers
        ;;
    "verify")
        verify_deployment
        ;;
    "monitor")
        setup_monitoring
        ;;
    "full"|"")
        main
        ;;
    *)
        echo "Использование: $0 [build|push|deploy|verify|monitor|full]"
        echo "  build   - Только сборка образов"
        echo "  push    - Только отправка в registry"
        echo "  deploy  - Только развертывание"
        echo "  verify  - Только проверка"
        echo "  monitor - Только настройка мониторинга"
        echo "  full    - Полное развертывание (по умолчанию)"
        exit 1
        ;;
esac 