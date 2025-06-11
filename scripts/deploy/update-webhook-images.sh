#!/bin/bash

# ============================================================================
# Скрипт быстрого обновления образов webhook сервисов
# 
# Использование:
#   ./scripts/deploy/update-webhook-images.sh
#
# Что делает:
# 1. Собирает новые образы webhook-api и nginx-webhook 
# 2. Пушит их в реестр
# 3. Перезапускает контейнеры с новыми образами
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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Переменные
REGISTRY="192.168.0.4:5000"
WEBHOOK_IMAGE="${REGISTRY}/webhook-api:latest"
NGINX_IMAGE="${REGISTRY}/nginx-webhook:latest"
COMPOSE_FILE="docker-compose.webhook.prod.yml"

# Проверка файлов
if [ ! -f "docker-compose.webhook.prod.yml" ]; then
    log_error "docker-compose.webhook.prod.yml не найден"
    exit 1
fi

if [ ! -f "prod.env" ]; then
    log_error "prod.env файл не найден"
    exit 1
fi

log_info "🔄 Обновляю webhook образы..."

# Сборка новых образов
log_info "📦 Собираю новый webhook-api образ..."
docker build -f docker/Dockerfile.webhook -t ${WEBHOOK_IMAGE} .

log_info "📦 Собираю новый nginx-webhook образ..."
docker build -f docker/nginx/Dockerfile -t ${NGINX_IMAGE} docker/nginx/

# Пуш в реестр
log_info "⬆️ Пушу обновлённые образы..."
docker push ${WEBHOOK_IMAGE}
docker push ${NGINX_IMAGE}

# Обновление контейнеров
log_info "🔄 Подтягиваю свежие образы и перезапускаю сервисы..."
docker-compose -f ${COMPOSE_FILE} --env-file prod.env pull
docker-compose -f ${COMPOSE_FILE} --env-file prod.env up -d --force-recreate

# Ожидание и проверка
log_info "⏳ Ожидаю перезапуска (15 секунд)..."
sleep 15

log_info "🔍 Проверяю состояние сервисов..."
docker-compose -f ${COMPOSE_FILE} --env-file prod.env ps

log_success "✅ Образы обновлены и сервисы перезапущены"
echo ""
log_info "🔍 Проверьте что сервисы работают:"
echo "   • curl -f http://localhost/health"
echo "   • curl -f http://localhost:8001/health"
echo "   • curl -f http://localhost:8002/health" 