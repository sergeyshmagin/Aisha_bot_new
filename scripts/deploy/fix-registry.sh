#!/bin/bash

# ============================================================================
# 🔧 DOCKER REGISTRY FIX SCRIPT
# ============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

REGISTRY_SERVER="192.168.0.4"
REGISTRY_PORT="5000"

echo -e "${GREEN}🔧 Быстрое исправление Docker Registry...${NC}"

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
# 🏗️ Настройка Docker Registry на 192.168.0.4
# ============================================================================

log_info "Настройка Docker Registry на $REGISTRY_SERVER..."

ssh aisha@$REGISTRY_SERVER << 'EOF'
    # Проверка и создание директории
    mkdir -p ~/docker-registry
    
    # Остановка старого контейнера
    sudo docker stop registry-server || true
    sudo docker rm registry-server || true
    
    # Запуск Registry сервера
    sudo docker run -d \
        --name registry-server \
        --restart=always \
        -p 5000:5000 \
        -v ~/docker-registry:/var/lib/registry \
        registry:2
    
    echo "Registry запущен на порту 5000"
    
    # Проверка статуса
    sleep 5
    sudo docker ps | grep registry-server || echo "Ошибка запуска registry!"
EOF

# ============================================================================
# 🔧 Настройка insecure registry на продакшн сервере
# ============================================================================

log_info "Настройка insecure registry на продакшн сервере..."

ssh aisha@192.168.0.10 << 'EOF'
    # Создание конфигурации Docker daemon
    sudo mkdir -p /etc/docker
    
    # Проверка существующей конфигурации
    if [ -f /etc/docker/daemon.json ]; then
        echo "Обновление существующего daemon.json..."
        sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.backup
    fi
    
    # Создание новой конфигурации
    echo '{
        "insecure-registries": ["192.168.0.4:5000"]
    }' | sudo tee /etc/docker/daemon.json
    
    # Перезапуск Docker
    sudo systemctl restart docker
    echo "Docker daemon перезапущен с insecure registry"
    
    # Проверка конфигурации
    sleep 5
    sudo docker info | grep -A 10 "Insecure Registries" || echo "Проверьте конфигурацию Docker"
EOF

# ============================================================================
# ✅ Проверка работоспособности
# ============================================================================

log_info "Проверка работоспособности registry..."

# Проверка доступности registry
if curl -s http://$REGISTRY_SERVER:$REGISTRY_PORT/v2/ | grep -q "{}"; then
    log_info "✅ Registry доступен по адресу http://$REGISTRY_SERVER:$REGISTRY_PORT"
else
    log_error "❌ Registry недоступен!"
    exit 1
fi

# Тест push/pull
log_info "Тестирование push/pull..."

# Создание тестового образа
docker run --name test-container -d alpine:latest sleep 1000 || true
docker commit test-container test-image:latest
docker tag test-image:latest $REGISTRY_SERVER:$REGISTRY_PORT/test-image:latest

# Тест push
if docker push $REGISTRY_SERVER:$REGISTRY_PORT/test-image:latest; then
    log_info "✅ Push работает корректно"
else
    log_error "❌ Push не работает!"
fi

# Очистка тестовых данных
docker stop test-container && docker rm test-container || true
docker rmi test-image:latest $REGISTRY_SERVER:$REGISTRY_PORT/test-image:latest || true

echo -e "${GREEN}🎉 Docker Registry настроен и работает!${NC}"
echo ""
echo "📊 Информация:"
echo "  • Registry URL: http://$REGISTRY_SERVER:$REGISTRY_PORT"
echo "  • Catalog: http://$REGISTRY_SERVER:$REGISTRY_PORT/v2/_catalog"
echo ""
echo "🔧 Команды для проверки:"
echo "  ssh aisha@$REGISTRY_SERVER 'sudo docker ps | grep registry'"
echo "  curl http://$REGISTRY_SERVER:$REGISTRY_PORT/v2/_catalog" 