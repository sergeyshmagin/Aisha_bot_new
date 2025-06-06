#!/bin/bash

# ============================================================================
# 📦 QUICK DOCKER REGISTRY SETUP
# ============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

REGISTRY_SERVER="192.168.0.4"

echo -e "${GREEN}📦 Быстрая настройка Docker Registry...${NC}"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# 🏗️ Настройка Registry сервера
# ============================================================================

log_info "Настройка Registry на $REGISTRY_SERVER..."

ssh aisha@$REGISTRY_SERVER << 'EOF'
    # Создание директории
    mkdir -p ~/docker-registry
    
    # Остановка старых контейнеров
    sudo docker stop registry-server 2>/dev/null || true
    sudo docker rm registry-server 2>/dev/null || true
    
    # Запуск Registry
    sudo docker run -d \
        --name registry-server \
        --restart=always \
        -p 5000:5000 \
        -v ~/docker-registry:/var/lib/registry \
        registry:2
    
    # Проверка
    sleep 3
    if sudo docker ps | grep -q registry-server; then
        echo "✅ Registry запущен успешно"
    else
        echo "❌ Ошибка запуска Registry"
        exit 1
    fi
EOF

# ============================================================================
# 🔧 Настройка клиентов
# ============================================================================

log_info "Настройка insecure registry на клиентах..."

# Продакшн сервер
ssh aisha@192.168.0.10 << 'EOF'
    sudo mkdir -p /etc/docker
    echo '{"insecure-registries": ["192.168.0.4:5000"]}' | sudo tee /etc/docker/daemon.json
    sudo systemctl restart docker
    sleep 3
    echo "✅ Продакшн сервер настроен"
EOF

# ============================================================================
# ✅ Тестирование
# ============================================================================

log_info "Тестирование Registry..."

# Проверка доступности
if curl -s http://$REGISTRY_SERVER:5000/v2/ | grep -q "{}"; then
    log_info "✅ Registry доступен"
else
    log_error "❌ Registry недоступен"
    exit 1
fi

# Проверка каталога
log_info "Список образов в Registry:"
curl -s http://$REGISTRY_SERVER:5000/v2/_catalog | python3 -m json.tool 2>/dev/null || echo "Каталог пуст"

echo ""
echo -e "${GREEN}🎉 Docker Registry готов к использованию!${NC}"
echo ""
echo "📊 Информация:"
echo "  • URL: http://$REGISTRY_SERVER:5000"
echo "  • Catalog: http://$REGISTRY_SERVER:5000/v2/_catalog"
echo ""
echo "🔧 Использование:"
echo "  docker tag image:latest $REGISTRY_SERVER:5000/image:latest"
echo "  docker push $REGISTRY_SERVER:5000/image:latest"
echo "  docker pull $REGISTRY_SERVER:5000/image:latest" 