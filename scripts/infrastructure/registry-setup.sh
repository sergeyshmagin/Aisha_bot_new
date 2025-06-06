#!/bin/bash

# ============================================================================
# 📦 ADVANCED DOCKER REGISTRY SETUP SCRIPT
# ============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

REGISTRY_SERVER="192.168.0.4"
REGISTRY_PORT="5000"

echo -e "${GREEN}📦 Продвинутая настройка Docker Registry...${NC}"

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
# 🏗️ Настройка Registry сервера с постоянным хранилищем
# ============================================================================

log_info "Настройка Registry сервера на $REGISTRY_SERVER..."

ssh aisha@$REGISTRY_SERVER << 'EOF'
    # Создание структуры директорий
    mkdir -p ~/docker-registry/{data,auth,certs,config}
    
    # Остановка и удаление старых контейнеров
    sudo docker stop registry-server registry-ui 2>/dev/null || true
    sudo docker rm registry-server registry-ui 2>/dev/null || true
    
    # Создание конфигурации Registry
    cat > ~/docker-registry/config/config.yml << 'CONFIG'
version: 0.1
log:
  level: info
  formatter: text
storage:
  filesystem:
    rootdirectory: /var/lib/registry
  delete:
    enabled: true
http:
  addr: :5000
  headers:
    X-Content-Type-Options: [nosniff]
    Access-Control-Allow-Origin: ['*']
    Access-Control-Allow-Methods: ['GET', 'POST', 'PUT', 'DELETE']
    Access-Control-Allow-Headers: ['Authorization', 'Accept', 'Cache-Control']
health:
  storagedriver:
    enabled: true
    interval: 10s
    threshold: 3
CONFIG
    
    # Запуск Registry с конфигурацией
    sudo docker run -d \
        --name registry-server \
        --restart=always \
        -p 5000:5000 \
        -v ~/docker-registry/data:/var/lib/registry \
        -v ~/docker-registry/config/config.yml:/etc/docker/registry/config.yml \
        registry:2
    
    # Запуск Registry UI для удобного управления
    sudo docker run -d \
        --name registry-ui \
        --restart=always \
        -p 8080:80 \
        -e REGISTRY_URL=http://localhost:5000 \
        -e DELETE_IMAGES=true \
        -e REGISTRY_TITLE="Aisha Docker Registry" \
        joxit/docker-registry-ui:latest
    
    echo "✅ Registry сервер запущен с UI на порту 8080"
    
    # Проверка запуска
    sleep 5
    if sudo docker ps | grep -q registry-server; then
        echo "✅ Registry Server: OK"
    else
        echo "❌ Registry Server: FAILED"
        exit 1
    fi
    
    if sudo docker ps | grep -q registry-ui; then
        echo "✅ Registry UI: OK"
    else
        echo "⚠️ Registry UI: FAILED"
    fi
EOF

# ============================================================================
# 🔧 Настройка клиентов (insecure registry)
# ============================================================================

log_info "Настройка клиентов для работы с Registry..."

# Продакшн сервер (192.168.0.10)
log_info "Настройка продакшн сервера..."
ssh aisha@192.168.0.10 << 'EOF'
    # Создание конфигурации Docker daemon
    sudo mkdir -p /etc/docker
    
    # Бэкап существующей конфигурации
    if [ -f /etc/docker/daemon.json ]; then
        sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.backup
    fi
    
    # Создание новой конфигурации
    cat << 'DAEMON' | sudo tee /etc/docker/daemon.json
{
    "insecure-registries": ["192.168.0.4:5000"],
    "registry-mirrors": [],
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}
DAEMON
    
    # Перезапуск Docker
    sudo systemctl restart docker
    
    # Проверка конфигурации
    sleep 3
    if sudo docker info | grep -q "192.168.0.4:5000"; then
        echo "✅ Insecure registry настроен"
    else
        echo "❌ Ошибка настройки insecure registry"
        exit 1
    fi
EOF

# Локальная машина (если нужно)
if [ "$HOSTNAME" != "192.168.0.4" ] && [ "$HOSTNAME" != "192.168.0.10" ]; then
    log_info "Настройка локальной машины..."
    
    # Создание конфигурации Docker daemon локально
    if [ ! -f /etc/docker/daemon.json ]; then
        echo '{"insecure-registries": ["192.168.0.4:5000"]}' | sudo tee /etc/docker/daemon.json
        sudo systemctl restart docker
        log_info "✅ Локальная машина настроена"
    else
        log_warn "⚠️ /etc/docker/daemon.json уже существует, проверьте конфигурацию вручную"
    fi
fi

# ============================================================================
# 🧪 Тестирование Registry
# ============================================================================

log_info "Тестирование Registry..."

# Проверка доступности API
if curl -s http://$REGISTRY_SERVER:$REGISTRY_PORT/v2/ | grep -q "{}"; then
    log_info "✅ Registry API доступен"
else
    log_error "❌ Registry API недоступен"
    exit 1
fi

# Проверка UI
if curl -s http://$REGISTRY_SERVER:8080 | grep -q "Docker Registry UI"; then
    log_info "✅ Registry UI доступен"
else
    log_warn "⚠️ Registry UI может быть недоступен"
fi

# Тест push/pull с реальным образом
log_info "Тестирование push/pull..."

# Загрузка тестового образа
docker pull alpine:latest

# Тегирование для registry
docker tag alpine:latest $REGISTRY_SERVER:$REGISTRY_PORT/test-alpine:latest

# Push в registry
if docker push $REGISTRY_SERVER:$REGISTRY_PORT/test-alpine:latest; then
    log_info "✅ Push успешен"
else
    log_error "❌ Push неуспешен"
    exit 1
fi

# Удаление локального образа
docker rmi alpine:latest $REGISTRY_SERVER:$REGISTRY_PORT/test-alpine:latest

# Pull из registry
if docker pull $REGISTRY_SERVER:$REGISTRY_PORT/test-alpine:latest; then
    log_info "✅ Pull успешен"
else
    log_error "❌ Pull неуспешен"
    exit 1
fi

# Очистка тестового образа
docker rmi $REGISTRY_SERVER:$REGISTRY_PORT/test-alpine:latest

# ============================================================================
# 📊 Информация о Registry
# ============================================================================

log_info "Получение информации о Registry..."

# Список образов в Registry
log_info "Список образов в Registry:"
curl -s http://$REGISTRY_SERVER:$REGISTRY_PORT/v2/_catalog | python3 -m json.tool 2>/dev/null || echo "Каталог пуст или недоступен"

# Статистика использования
ssh aisha@$REGISTRY_SERVER << 'EOF'
    echo ""
    echo "📊 Статистика использования:"
    echo "Размер данных Registry: $(du -sh ~/docker-registry/data 2>/dev/null | cut -f1 || echo 'Неизвестно')"
    echo "Статус контейнеров:"
    sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep registry
EOF

echo ""
echo -e "${GREEN}🎉 Docker Registry готов к использованию!${NC}"
echo ""
echo "📊 Информация о Registry:"
echo "  • API URL:     http://$REGISTRY_SERVER:$REGISTRY_PORT"
echo "  • UI URL:      http://$REGISTRY_SERVER:8080"
echo "  • Catalog:     http://$REGISTRY_SERVER:$REGISTRY_PORT/v2/_catalog"
echo "  • Health:      http://$REGISTRY_SERVER:$REGISTRY_PORT/v2/"
echo ""
echo "🔧 Команды для работы:"
echo "  docker tag image:tag $REGISTRY_SERVER:$REGISTRY_PORT/image:tag"
echo "  docker push $REGISTRY_SERVER:$REGISTRY_PORT/image:tag"
echo "  docker pull $REGISTRY_SERVER:$REGISTRY_PORT/image:tag"
echo ""
echo "🌐 Веб-интерфейс:"
echo "  Откройте http://$REGISTRY_SERVER:8080 для управления образами"
echo ""
echo "🔧 Управление сервисом:"
echo "  ssh aisha@$REGISTRY_SERVER 'sudo docker restart registry-server'"
echo "  ssh aisha@$REGISTRY_SERVER 'sudo docker logs registry-server'"

log_info "Registry готов! 🚀" 