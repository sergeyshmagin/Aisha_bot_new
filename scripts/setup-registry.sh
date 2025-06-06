#!/bin/bash

# =============================================================================
# Скрипт настройки Docker Registry на сервере инфраструктуры
# Целевой сервер: 192.168.0.4 (PostgreSQL + MinIO + Registry)
# =============================================================================

set -euo pipefail

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Конфигурация
INFRA_SERVER="192.168.0.4"
INFRA_USER="aisha"  # или другой пользователь
REGISTRY_PORT="5000"
REGISTRY_VERSION="2"

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

# Проверка доступности сервера инфраструктуры
check_infra_server() {
    log_info "🔍 Проверка сервера инфраструктуры ($INFRA_SERVER)..."
    
    if ! ping -c 1 $INFRA_SERVER >/dev/null 2>&1; then
        log_error "❌ Сервер $INFRA_SERVER недоступен"
        exit 1
    fi
    
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $INFRA_USER@$INFRA_SERVER exit 2>/dev/null; then
        log_error "❌ SSH доступ к $INFRA_USER@$INFRA_SERVER недоступен"
        log_info "💡 Настройте SSH ключи: ssh-copy-id $INFRA_USER@$INFRA_SERVER"
        exit 1
    fi
    
    log_success "✅ Сервер инфраструктуры доступен"
}

# Проверка Docker на сервере инфраструктуры
check_docker() {
    log_info "🐳 Проверка Docker на сервере инфраструктуры..."
    
    if ! ssh $INFRA_USER@$INFRA_SERVER "command -v docker >/dev/null 2>&1"; then
        log_error "❌ Docker не установлен на сервере $INFRA_SERVER"
        exit 1
    fi
    
    if ! ssh $INFRA_USER@$INFRA_SERVER "docker ps >/dev/null 2>&1"; then
        log_error "❌ Пользователь $INFRA_USER не имеет прав на Docker"
        log_info "💡 Выполните на сервере: sudo usermod -aG docker $INFRA_USER"
        exit 1
    fi
    
    log_success "✅ Docker готов к использованию"
}

# Проверка существующего registry
check_existing_registry() {
    log_info "📦 Проверка существующего registry..."
    
    if ssh $INFRA_USER@$INFRA_SERVER "docker ps --format 'table {{.Names}}' | grep -q registry" 2>/dev/null; then
        log_warning "⚠️ Registry уже запущен"
        
        # Показываем информацию о существующем registry
        log_info "📊 Информация о существующем registry:"
        ssh $INFRA_USER@$INFRA_SERVER "docker ps --filter name=registry --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
        
        read -p "Хотите пересоздать registry? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "🛑 Остановка существующего registry..."
            ssh $INFRA_USER@$INFRA_SERVER "docker stop registry && docker rm registry" || true
        else
            log_info "📦 Используем существующий registry"
            return 0
        fi
    fi
}

# Настройка registry
setup_registry() {
    log_info "🏗️ Настройка Docker Registry..."
    
    # Создаем директории для registry
    ssh $INFRA_USER@$INFRA_SERVER "mkdir -p /opt/registry/data /opt/registry/config"
    
    # Создаем конфигурацию registry
    ssh $INFRA_USER@$INFRA_SERVER "cat > /opt/registry/config/config.yml << 'EOF'
version: 0.1
log:
  fields:
    service: registry
storage:
  cache:
    blobdescriptor: inmemory
  filesystem:
    rootdirectory: /var/lib/registry
  delete:
    enabled: true
http:
  addr: :5000
  headers:
    X-Content-Type-Options: [nosniff]
    Access-Control-Allow-Origin: ['*']
    Access-Control-Allow-Methods: ['HEAD', 'GET', 'OPTIONS', 'DELETE']
    Access-Control-Allow-Headers: ['Authorization', 'Accept', 'Cache-Control']
health:
  storagedriver:
    enabled: true
    interval: 10s
    threshold: 3
EOF"
    
    log_success "✅ Конфигурация registry создана"
}

# Запуск registry
start_registry() {
    log_info "🚀 Запуск Docker Registry..."
    
    ssh $INFRA_USER@$INFRA_SERVER "docker run -d \
        --name registry \
        --restart unless-stopped \
        -p $REGISTRY_PORT:5000 \
        -v /opt/registry/data:/var/lib/registry \
        -v /opt/registry/config/config.yml:/etc/docker/registry/config.yml \
        registry:$REGISTRY_VERSION"
    
    # Ждем запуска
    sleep 5
    
    # Проверяем статус
    if ssh $INFRA_USER@$INFRA_SERVER "docker ps --filter name=registry --filter status=running | grep -q registry"; then
        log_success "✅ Registry запущен успешно"
    else
        log_error "❌ Ошибка запуска registry"
        log_info "📋 Логи registry:"
        ssh $INFRA_USER@$INFRA_SERVER "docker logs registry"
        exit 1
    fi
}

# Проверка работоспособности registry
test_registry() {
    log_info "🧪 Тестирование registry..."
    
    # Проверяем API registry
    if ssh $INFRA_USER@$INFRA_SERVER "curl -f http://localhost:$REGISTRY_PORT/v2/ >/dev/null 2>&1"; then
        log_success "✅ Registry API отвечает"
    else
        log_error "❌ Registry API недоступен"
        exit 1
    fi
    
    # Проверяем доступность с других серверов
    if curl -f -s "http://$INFRA_SERVER:$REGISTRY_PORT/v2/" >/dev/null 2>&1; then
        log_success "✅ Registry доступен извне"
    else
        log_warning "⚠️ Registry может быть недоступен с других серверов"
        log_info "💡 Проверьте firewall настройки"
    fi
}

# Настройка insecure registry на клиентах
setup_insecure_registry() {
    log_info "🔧 Настройка insecure registry..."
    
    # Проверяем, нужно ли настраивать insecure registry на локальной машине
    if ! grep -q "$INFRA_SERVER:$REGISTRY_PORT" /etc/docker/daemon.json 2>/dev/null; then
        log_warning "⚠️ Необходимо добавить registry в insecure-registries"
        log_info "💡 Добавьте в /etc/docker/daemon.json:"
        echo '{
  "insecure-registries": ["'$INFRA_SERVER:$REGISTRY_PORT'"]
}'
        log_info "💡 Затем перезапустите Docker: sudo systemctl restart docker"
    else
        log_success "✅ Registry уже настроен как insecure"
    fi
}

# Создание systemd сервиса (опционально)
create_systemd_service() {
    log_info "⚙️ Создание systemd сервиса для registry..."
    
    ssh $INFRA_USER@$INFRA_SERVER "sudo tee /etc/systemd/system/docker-registry.service > /dev/null << 'EOF'
[Unit]
Description=Docker Registry
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/docker start registry
ExecStop=/usr/bin/docker stop registry
User=$INFRA_USER

[Install]
WantedBy=multi-user.target
EOF"
    
    ssh $INFRA_USER@$INFRA_SERVER "sudo systemctl daemon-reload"
    ssh $INFRA_USER@$INFRA_SERVER "sudo systemctl enable docker-registry.service"
    
    log_success "✅ Systemd сервис создан"
}

# Показать информацию о registry
show_registry_info() {
    log_info "📊 Информация о registry:"
    echo "🌐 URL: http://$INFRA_SERVER:$REGISTRY_PORT"
    echo "📋 API: http://$INFRA_SERVER:$REGISTRY_PORT/v2/"
    echo "📦 Каталог: http://$INFRA_SERVER:$REGISTRY_PORT/v2/_catalog"
    echo ""
    echo "🔧 Команды для использования:"
    echo "  # Тегирование образа:"
    echo "  docker tag myimage:latest $INFRA_SERVER:$REGISTRY_PORT/myimage:latest"
    echo ""
    echo "  # Отправка образа:"
    echo "  docker push $INFRA_SERVER:$REGISTRY_PORT/myimage:latest"
    echo ""
    echo "  # Загрузка образа:"
    echo "  docker pull $INFRA_SERVER:$REGISTRY_PORT/myimage:latest"
    echo ""
    echo "🎯 Для webhook API:"
    echo "  docker build -t $INFRA_SERVER:$REGISTRY_PORT/aisha-webhook-api:latest -f docker/Dockerfile.webhook ."
    echo "  docker push $INFRA_SERVER:$REGISTRY_PORT/aisha-webhook-api:latest"
}

# Главная функция
main() {
    echo "========================================"
    echo "🏗️ Настройка Docker Registry"
    echo "📍 Сервер: $INFRA_SERVER:$REGISTRY_PORT"
    echo "========================================"
    
    check_infra_server
    check_docker
    check_existing_registry
    setup_registry
    start_registry
    test_registry
    setup_insecure_registry
    
    read -p "Создать systemd сервис для автозапуска? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_systemd_service
    fi
    
    echo "========================================"
    log_success "✅ Registry настроен успешно!"
    echo ""
    show_registry_info
    echo "========================================"
}

# Обработка аргументов
case "${1:-}" in
    "check")
        check_infra_server
        check_docker
        ;;
    "start")
        start_registry
        ;;
    "stop")
        ssh $INFRA_USER@$INFRA_SERVER "docker stop registry"
        ;;
    "restart")
        ssh $INFRA_USER@$INFRA_SERVER "docker restart registry"
        ;;
    "status")
        ssh $INFRA_USER@$INFRA_SERVER "docker ps --filter name=registry"
        ;;
    "logs")
        ssh $INFRA_USER@$INFRA_SERVER "docker logs registry"
        ;;
    "test")
        test_registry
        ;;
    "info")
        show_registry_info
        ;;
    *)
        main
        ;;
esac 