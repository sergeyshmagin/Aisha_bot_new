#!/bin/bash

# ============================================================================
# 🚀 WEBHOOK API COMPLETE DEPLOYMENT SCRIPT
# ============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Начинаем полное развертывание Webhook API...${NC}"

# Конфигурация
REGISTRY_SERVER="192.168.0.4:5000"
PROD_SERVER="192.168.0.10"
WEBHOOK_IMAGE="webhook-api"
NGINX_IMAGE="nginx-webhook"

# Переходим в корень проекта
cd "$(dirname "$0")/../.."

# ============================================================================
# 🔧 Функции
# ============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 не найден!"
        exit 1
    fi
}

# ============================================================================
# 🔍 Проверки
# ============================================================================

log_info "Проверка зависимостей..."
check_command docker
check_command docker-compose

# ============================================================================
# 🏗️ ЭТАП 1: Сборка образов
# ============================================================================

log_info "ЭТАП 1: Сборка образов..."

# Сборка webhook API
log_info "Сборка webhook-api..."
docker build -f docker/Dockerfile.webhook -t $WEBHOOK_IMAGE:latest .

# Сборка nginx
log_info "Сборка nginx..."
docker build -f docker/nginx/Dockerfile -t $NGINX_IMAGE:latest docker/nginx/

# ============================================================================
# 🏷️ ЭТАП 2: Тегирование для registry
# ============================================================================

log_info "ЭТАП 2: Тегирование образов..."

docker tag $WEBHOOK_IMAGE:latest $REGISTRY_SERVER/$WEBHOOK_IMAGE:latest
docker tag $NGINX_IMAGE:latest $REGISTRY_SERVER/$NGINX_IMAGE:latest

# ============================================================================
# 📤 ЭТАП 3: Отправка в registry
# ============================================================================

log_info "ЭТАП 3: Отправка образов в registry..."

# Проверка доступности registry
if ! curl -s http://$REGISTRY_SERVER/v2/ > /dev/null; then
    log_error "Registry $REGISTRY_SERVER недоступен!"
    log_warn "Сначала запустите: ./scripts/deploy/fix-registry.sh"
    exit 1
fi

log_info "Registry доступен, отправляем образы..."
docker push $REGISTRY_SERVER/$WEBHOOK_IMAGE:latest
docker push $REGISTRY_SERVER/$NGINX_IMAGE:latest

# ============================================================================
# 🚀 ЭТАП 4: Развертывание на продакшн
# ============================================================================

log_info "ЭТАП 4: Развертывание на продакшн сервере..."

# Копирование файлов развертывания
log_info "Копирование файлов развертывания..."
scp docker-compose.webhook.prod.yml aisha@$PROD_SERVER:~/
scp prod.env aisha@$PROD_SERVER:~/
scp -r ssl_certificate/ aisha@$PROD_SERVER:~/

# Развертывание на продакшн сервере
log_info "Запуск развертывания на продакшн сервере..."
ssh aisha@$PROD_SERVER << 'EOF'
    # Настройка insecure registry
    if ! grep -q "192.168.0.4:5000" /etc/docker/daemon.json 2>/dev/null; then
        echo '{"insecure-registries": ["192.168.0.4:5000"]}' | sudo tee /etc/docker/daemon.json
        sudo systemctl restart docker
        sleep 5
    fi
    
    # Остановка старых контейнеров
    sudo docker-compose -f docker-compose.webhook.prod.yml down || true
    
    # Загрузка новых образов
    sudo docker pull 192.168.0.4:5000/webhook-api:latest
    sudo docker pull 192.168.0.4:5000/nginx-webhook:latest
    
    # Запуск новых контейнеров
    sudo docker-compose -f docker-compose.webhook.prod.yml up -d
    
    # Проверка статуса
    sleep 10
    sudo docker-compose -f docker-compose.webhook.prod.yml ps
EOF

# ============================================================================
# ✅ ЭТАП 5: Проверка развертывания
# ============================================================================

log_info "ЭТАП 5: Проверка развертывания..."

# Проверка health endpoints
log_info "Проверка health endpoints..."

# Проверка через внешний API
if curl -k -s https://aibots.kz:8443/health | grep -q "ok"; then
    log_info "✅ Webhook API доступен через https://aibots.kz:8443"
else
    log_warn "⚠️ Webhook API может быть недоступен извне"
fi

# Проверка через внутренний IP
if curl -k -s https://$PROD_SERVER:8443/health | grep -q "ok"; then
    log_info "✅ Webhook API доступен через https://$PROD_SERVER:8443"
else
    log_warn "⚠️ Webhook API может быть недоступен через внутренний IP"
fi

# ============================================================================
# 📋 Финальная информация
# ============================================================================

echo -e "${GREEN}🎉 Развертывание завершено!${NC}"
echo ""
echo "📊 Конечные точки:"
echo "  • Health Check: https://aibots.kz:8443/health"
echo "  • Webhook API:   https://aibots.kz:8443/webhook/fal"
echo "  • Внутренний IP: https://$PROD_SERVER:8443"
echo ""
echo "🔧 Команды для управления:"
echo "  • Статус:      ssh aisha@$PROD_SERVER 'sudo docker-compose -f docker-compose.webhook.prod.yml ps'"
echo "  • Логи:        ssh aisha@$PROD_SERVER 'sudo docker-compose -f docker-compose.webhook.prod.yml logs -f'"
echo "  • Перезапуск:  ssh aisha@$PROD_SERVER 'sudo docker-compose -f docker-compose.webhook.prod.yml restart'"
echo "  • Остановка:   ssh aisha@$PROD_SERVER 'sudo docker-compose -f docker-compose.webhook.prod.yml down'"
echo ""
echo "🎯 Следующие шаги:"
echo "  1. Настройте FAL AI webhook URL: https://aibots.kz:8443/webhook/fal"
echo "  2. Проверьте логи на отсутствие ошибок"
echo "  3. Протестируйте обработку webhook'ов"

log_info "Готово! 🚀" 