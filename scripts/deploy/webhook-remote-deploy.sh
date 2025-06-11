#!/bin/bash

# ============================================================================
# Скрипт развёртывания webhook сервисов на продакшн сервере 192.168.0.10
# 
# Использование:
#   ./scripts/deploy/webhook-remote-deploy.sh
#
# Что делает:
# 1. Собирает и пушит образы в реестр 192.168.0.4:5000
# 2. Копирует файлы на продакшн сервер 192.168.0.10
# 3. Настраивает доступ к реестру на продакшн сервере
# 4. Запускает webhook сервисы на продакшн сервере
# ============================================================================

set -e

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Переменные
REGISTRY="192.168.0.4:5000"
PROD_SERVER="192.168.0.10"
PROD_USER="aisha"
WEBHOOK_IMAGE="${REGISTRY}/webhook-api:latest"
NGINX_IMAGE="${REGISTRY}/nginx-webhook:latest"

# Проверка файлов
if [ ! -f "docker-compose.webhook.prod.yml" ]; then
    log_error "docker-compose.webhook.prod.yml не найден"
    exit 1
fi

if [ ! -f "prod.env" ]; then
    log_error "prod.env файл не найден"
    exit 1
fi

log_info "🚀 Начинаю развёртывание webhook сервисов на продакшн сервере ${PROD_SERVER}..."

# ============================================================================
# 1. Сборка и пуш образов в реестр
# ============================================================================

log_info "📦 Собираю webhook-api образ..."
docker build -f docker/Dockerfile.webhook -t ${WEBHOOK_IMAGE} .
log_success "Webhook API образ собран"

log_info "📦 Собираю nginx-webhook образ..."
docker build -f docker/nginx/Dockerfile -t ${NGINX_IMAGE} docker/nginx/
log_success "Nginx образ собран"

log_info "⬆️ Пушу образы в реестр ${REGISTRY}..."
docker push ${WEBHOOK_IMAGE}
docker push ${NGINX_IMAGE}
log_success "Образы запушены в реестр"

# ============================================================================
# 2. Копирование файлов на продакшн сервер
# ============================================================================

log_info "📂 Копирую файлы на продакшн сервер ${PROD_SERVER}..."

# Создаём директорию для деплоя
ssh ${PROD_USER}@${PROD_SERVER} "mkdir -p ~/aisha-webhook-deploy"

# Копируем необходимые файлы
scp docker-compose.webhook.prod.yml ${PROD_USER}@${PROD_SERVER}:~/aisha-webhook-deploy/
scp prod.env ${PROD_USER}@${PROD_SERVER}:~/aisha-webhook-deploy/

# Копируем SSL сертификаты если есть
if [ -d "ssl_certificate" ]; then
    scp -r ssl_certificate/ ${PROD_USER}@${PROD_SERVER}:~/aisha-webhook-deploy/
    log_info "SSL сертификаты скопированы"
fi

log_success "Файлы скопированы на продакшн сервер"

# ============================================================================
# 3. Развёртывание на продакшн сервере
# ============================================================================

log_info "🚀 Запускаю развёртывание на продакшн сервере..."

ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
    # Переходим в директорию деплоя
    cd ~/aisha-webhook-deploy
    
    # Настройка insecure registry для доступа к 192.168.0.4:5000
    if ! sudo test -f /etc/docker/daemon.json || ! sudo grep -q "192.168.0.4:5000" /etc/docker/daemon.json 2>/dev/null; then
        echo 'Настраиваю доступ к Docker реестру...'
        echo '{"insecure-registries": ["192.168.0.4:5000"]}' | sudo tee /etc/docker/daemon.json
        sudo systemctl restart docker
        sleep 10
        echo 'Docker перезапущен'
    fi
    
    # Создание сети webhook кластера
    if ! docker network ls | grep -q aisha_webhook_cluster; then
        docker network create aisha_webhook_cluster
        echo 'Сеть aisha_webhook_cluster создана'
    fi
    
    # Остановка старых контейнеров
    echo 'Останавливаю старые контейнеры...'
    docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env down || true
    
    # Загрузка свежих образов
    echo 'Загружаю свежие образы...'
    docker pull 192.168.0.4:5000/webhook-api:latest
    docker pull 192.168.0.4:5000/nginx-webhook:latest
    
    # Запуск новых контейнеров
    echo 'Запускаю webhook сервисы...'
    docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env up -d
    
    # Ожидание запуска
    echo 'Ожидаю запуска сервисов (30 секунд)...'
    sleep 30
    
    # Проверка статуса
    echo 'Проверяю статус контейнеров:'
    docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env ps
EOF

# ============================================================================
# 4. Проверка развёртывания
# ============================================================================

log_info "🔍 Проверяю развёртывание на продакшн сервере..."

# Проверка health endpoints
log_info "Проверяю health endpoints..."

# Через nginx load balancer
if ssh ${PROD_USER}@${PROD_SERVER} "curl -f -s http://localhost/health" > /dev/null; then
    log_success "✅ Nginx load balancer работает"
else
    log_error "❌ Nginx load balancer недоступен"
fi

# Прямые подключения к API
if ssh ${PROD_USER}@${PROD_SERVER} "curl -f -s http://localhost:8001/health" > /dev/null; then
    log_success "✅ Webhook API #1 работает (порт 8001)"
else
    log_error "❌ Webhook API #1 недоступен (порт 8001)"
fi

if ssh ${PROD_USER}@${PROD_SERVER} "curl -f -s http://localhost:8002/health" > /dev/null; then
    log_success "✅ Webhook API #2 работает (порт 8002)"
else
    log_error "❌ Webhook API #2 недоступен (порт 8002)"
fi

# Внешняя проверка через aibots.kz
log_info "Проверяю внешний доступ через aibots.kz..."
if curl -k -f -s https://aibots.kz:8443/health > /dev/null 2>&1; then
    log_success "✅ Webhook API доступен через https://aibots.kz:8443"
else
    log_warning "⚠️ Webhook API может быть недоступен через https://aibots.kz:8443"
fi

# ============================================================================
# 5. Финальная информация
# ============================================================================

log_success "🎉 Развёртывание webhook сервисов завершено!"
echo ""
log_info "📋 Развёрнутые сервисы на ${PROD_SERVER}:"
echo "   • Nginx Load Balancer: http://${PROD_SERVER} (порты 80, 443)"
echo "   • Webhook API #1: http://${PROD_SERVER}:8001"
echo "   • Webhook API #2: http://${PROD_SERVER}:8002"
echo "   • Внешний доступ: https://aibots.kz:8443"
echo ""
log_info "🔗 FAL AI Webhook URL:"
echo "   https://aibots.kz:8443/api/v1/avatar/status_update"
echo ""
log_info "📝 Управление сервисами на продакшн сервере:"
echo "   ssh ${PROD_USER}@${PROD_SERVER}"
echo "   cd ~/aisha-webhook-deploy"
echo "   docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env logs -f"
echo "   docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env restart"
echo "   docker-compose -f docker-compose.webhook.prod.yml --env-file prod.env down"
echo ""
log_success "✨ Готово! Webhook сервисы развёрнуты на продакшн сервере и готовы к работе." 