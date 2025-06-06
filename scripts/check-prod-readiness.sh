#!/bin/bash

# =============================================================================
# Скрипт проверки готовности продакшн среды для webhook API
# =============================================================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Конфигурация
PROD_SERVER="192.168.0.10"
PROD_USER="aisha"
REDIS_HOST="192.168.0.3"
POSTGRES_HOST="192.168.0.4"
MINIO_HOST="192.168.0.4"
REGISTRY_HOST="192.168.0.3"

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

# Проверка внешних сервисов
check_external_services() {
    log_info "🔍 Проверка доступности внешних сервисов..."
    
    # Redis
    if command -v nc >/dev/null 2>&1; then
        if nc -zv $REDIS_HOST 6379 2>/dev/null; then
            log_success "✅ Redis ($REDIS_HOST:6379) доступен"
        else
            log_error "❌ Redis ($REDIS_HOST:6379) недоступен"
            return 1
        fi
        
        # PostgreSQL
        if nc -zv $POSTGRES_HOST 5432 2>/dev/null; then
            log_success "✅ PostgreSQL ($POSTGRES_HOST:5432) доступен"
        else
            log_error "❌ PostgreSQL ($POSTGRES_HOST:5432) недоступен"
            return 1
        fi
        
        # MinIO
        if nc -zv $MINIO_HOST 9000 2>/dev/null; then
            log_success "✅ MinIO ($MINIO_HOST:9000) доступен"
        else
            log_error "❌ MinIO ($MINIO_HOST:9000) недоступен"
            return 1
        fi
        
        # Registry
        if nc -zv $REGISTRY_HOST 5000 2>/dev/null; then
            log_success "✅ Registry ($REGISTRY_HOST:5000) доступен"
        else
            log_warning "⚠️ Registry ($REGISTRY_HOST:5000) недоступен - может потребоваться ручная настройка"
        fi
    else
        log_warning "⚠️ nc (netcat) не установлен, пропускаем проверку портов"
    fi
}

# Проверка продакшн сервера
check_production_server() {
    log_info "🖥️ Проверка продакшн сервера ($PROD_SERVER)..."
    
    # Проверяем ping
    if ping -c 1 $PROD_SERVER >/dev/null 2>&1; then
        log_success "✅ Сервер $PROD_SERVER доступен"
    else
        log_error "❌ Сервер $PROD_SERVER недоступен"
        return 1
    fi
    
    # Проверяем SSH доступ
    if ssh -o ConnectTimeout=10 -o BatchMode=yes $PROD_USER@$PROD_SERVER exit 2>/dev/null; then
        log_success "✅ SSH доступ к $PROD_USER@$PROD_SERVER работает"
    else
        log_error "❌ SSH доступ к $PROD_USER@$PROD_SERVER недоступен"
        log_info "💡 Настройте SSH ключи: ssh-copy-id $PROD_USER@$PROD_SERVER"
        return 1
    fi
}

# Проверка Docker на продакшн сервере
check_docker_on_prod() {
    log_info "🐳 Проверка Docker на продакшн сервере..."
    
    # Проверяем установку Docker
    if ssh $PROD_USER@$PROD_SERVER "command -v docker >/dev/null 2>&1"; then
        log_success "✅ Docker установлен"
        
        # Проверяем версию
        DOCKER_VERSION=$(ssh $PROD_USER@$PROD_SERVER "docker --version" 2>/dev/null)
        log_info "📦 $DOCKER_VERSION"
        
        # Проверяем права пользователя
        if ssh $PROD_USER@$PROD_SERVER "docker ps >/dev/null 2>&1"; then
            log_success "✅ Пользователь $PROD_USER имеет права на Docker"
        else
            log_warning "⚠️ Пользователь $PROD_USER не имеет прав на Docker"
            log_info "💡 Выполните: sudo usermod -aG docker $PROD_USER"
        fi
    else
        log_error "❌ Docker не установлен на продакшн сервере"
        return 1
    fi
    
    # Проверяем docker-compose
    if ssh $PROD_USER@$PROD_SERVER "command -v docker-compose >/dev/null 2>&1"; then
        log_success "✅ docker-compose установлен"
        COMPOSE_VERSION=$(ssh $PROD_USER@$PROD_SERVER "docker-compose --version" 2>/dev/null)
        log_info "📦 $COMPOSE_VERSION"
    else
        log_error "❌ docker-compose не установлен"
        return 1
    fi
}

# Проверка SSL сертификатов
check_ssl_certificates() {
    log_info "🔐 Проверка SSL сертификатов..."
    
    if [[ -f "ssl/aibots_kz_full.crt" ]] && [[ -f "ssl/aibots.kz.key" ]]; then
        log_success "✅ SSL сертификаты найдены локально"
        
        # Проверяем срок действия
        if command -v openssl >/dev/null 2>&1; then
            CERT_EXPIRY=$(openssl x509 -in ssl/aibots_kz_full.crt -noout -enddate 2>/dev/null | cut -d= -f2)
            log_info "📅 Сертификат действителен до: $CERT_EXPIRY"
        fi
    else
        log_error "❌ SSL сертификаты не найдены в папке ssl/"
        log_info "💡 Разместите сертификаты:"
        log_info "   - ssl/aibots_kz_full.crt"
        log_info "   - ssl/aibots.kz.key"
        return 1
    fi
}

# Проверка конфигурационных файлов
check_config_files() {
    log_info "📋 Проверка конфигурационных файлов..."
    
    local files=(
        "docker-compose.webhook.prod.yml"
        "docker/nginx/nginx.conf"
        "docker/Dockerfile.webhook"
        "scripts/deploy-webhook-prod.sh"
    )
    
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "✅ $file найден"
        else
            log_error "❌ $file не найден"
            return 1
        fi
    done
}

# Создание директории на продакшн сервере
prepare_prod_directory() {
    log_info "📁 Подготовка директории на продакшн сервере..."
    
    ssh $PROD_USER@$PROD_SERVER "mkdir -p /opt/aisha-webhook"
    ssh $PROD_USER@$PROD_SERVER "mkdir -p /opt/aisha-webhook/ssl"
    ssh $PROD_USER@$PROD_SERVER "mkdir -p /opt/aisha-webhook/logs"
    
    log_success "✅ Директории созданы"
}

# Главная функция
main() {
    echo "========================================"
    echo "🔍 Проверка готовности продакшн среды"
    echo "========================================"
    
    # Проверки
    check_external_services
    check_production_server
    check_docker_on_prod
    check_ssl_certificates
    check_config_files
    
    # Подготовка
    prepare_prod_directory
    
    echo "========================================"
    log_success "✅ Проверка завершена!"
    echo ""
    echo "🚀 Следующие шаги:"
    echo "1. Запустите развертывание: ./scripts/deploy-webhook-prod.sh"
    echo "2. Или используйте Makefile: make -f Makefile.webhook deploy"
    echo "========================================"
}

# Если аргумент передан, выполняем конкретную проверку
case "${1:-}" in
    "services")
        check_external_services
        ;;
    "server")
        check_production_server
        ;;
    "docker")
        check_docker_on_prod
        ;;
    "ssl")
        check_ssl_certificates
        ;;
    "config")
        check_config_files
        ;;
    *)
        main
        ;;
esac 