#!/bin/bash

# ============================================================================
# Скрипт полного деплоя webhook сервисов на продакшн сервер
# 
# Использование:
#   ./scripts/deploy/webhook-complete.sh
#
# Что делает:
# 1. Собирает и пушит образы webhook-api и nginx-webhook 
# 2. Создаёт сеть для webhook кластера
# 3. Запускает webhook сервисы через docker-compose
# ============================================================================

set -e  # Остановка при любой ошибке

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Логирование
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
WEBHOOK_IMAGE="${REGISTRY}/webhook-api:latest"
NGINX_IMAGE="${REGISTRY}/nginx-webhook:latest"
COMPOSE_FILE="docker-compose.webhook.prod.yml"
NETWORK_NAME="aisha_webhook_cluster"

# Проверка что мы в корне проекта
if [ ! -f "docker-compose.webhook.prod.yml" ]; then
    log_error "docker-compose.webhook.prod.yml не найден. Запустите скрипт из корня проекта."
    exit 1
fi

# Проверка что prod.env существует
if [ ! -f "prod.env" ]; then
    log_error "prod.env файл не найден. Создайте его со всеми необходимыми переменными."
    exit 1
fi

log_info "🚀 Начинаю деплой webhook сервисов..."

# ============================================================================
# 1. Сборка и пуш образов
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
# 2. Создание сети
# ============================================================================

log_info "🌐 Создаю Docker сеть для webhook кластера..."
if ! docker network ls | grep -q ${NETWORK_NAME}; then
    docker network create ${NETWORK_NAME}
    log_success "Сеть ${NETWORK_NAME} создана"
else
    log_warning "Сеть ${NETWORK_NAME} уже существует"
fi

# ============================================================================
# 3. Остановка старых контейнеров (если есть)
# ============================================================================

log_info "🛑 Останавливаю старые webhook контейнеры..."
docker-compose -f ${COMPOSE_FILE} --env-file prod.env down || true
log_success "Старые контейнеры остановлены"

# ============================================================================
# 4. Запуск новых контейнеров
# ============================================================================

log_info "🔄 Подтягиваю свежие образы..."
docker-compose -f ${COMPOSE_FILE} --env-file prod.env pull

log_info "🚀 Запускаю webhook сервисы..."
docker-compose -f ${COMPOSE_FILE} --env-file prod.env up -d

# ============================================================================
# 5. Проверка состояния
# ============================================================================

log_info "⏳ Ожидаю запуска сервисов (30 секунд)..."
sleep 30

log_info "🔍 Проверяю состояние контейнеров..."
docker-compose -f ${COMPOSE_FILE} --env-file prod.env ps

# Проверка webhook API endpoints
log_info "🔍 Проверяю webhook API endpoints..."

# Проверка через nginx load balancer
if curl -f -s http://localhost/health > /dev/null; then
    log_success "✅ Nginx load balancer работает"
else
    log_error "❌ Nginx load balancer недоступен"
fi

# Проверка прямых подключений к API
if curl -f -s http://localhost:8001/health > /dev/null; then
    log_success "✅ Webhook API #1 работает (порт 8001)"
else
    log_error "❌ Webhook API #1 недоступен (порт 8001)"
fi

if curl -f -s http://localhost:8002/health > /dev/null; then
    log_success "✅ Webhook API #2 работает (порт 8002)"
else
    log_error "❌ Webhook API #2 недоступен (порт 8002)"
fi

# ============================================================================
# 6. Финальная информация
# ============================================================================

log_success "🎉 Деплой webhook сервисов завершён!"
echo ""
log_info "📋 Сводка развёрнутых сервисов:"
echo "   • Nginx Load Balancer: http://localhost (порты 80, 443)"
echo "   • Webhook API #1: http://localhost:8001"
echo "   • Webhook API #2: http://localhost:8002"
echo "   • FAL AI Webhook URL: https://aibots.kz:8443/api/v1/avatar/status_update"
echo ""
log_info "📝 Полезные команды:"
echo "   • Просмотр логов: docker-compose -f ${COMPOSE_FILE} --env-file prod.env logs -f"
echo "   • Перезапуск: docker-compose -f ${COMPOSE_FILE} --env-file prod.env restart"
echo "   • Остановка: docker-compose -f ${COMPOSE_FILE} --env-file prod.env down"
echo "   • Обновление: ./scripts/deploy/webhook-complete.sh"
echo ""
log_success "✨ Готово! Webhook сервисы развёрнуты и готовы к работе." 