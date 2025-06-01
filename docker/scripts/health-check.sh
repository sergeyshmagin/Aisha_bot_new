#!/bin/bash

# 🔍 Проверка доступности внешних сервисов

set -e

# Загрузка переменных окружения
if [ -f .env.docker.dev ]; then
    source .env.docker.dev
elif [ -f .env.docker.prod ]; then
    source .env.docker.prod
else
    echo "❌ Файл переменных окружения не найден"
    exit 1
fi

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

check_service() {
    local service_name=$1
    local host=$2
    local port=$3
    local timeout=${4:-5}
    
    log "Проверка $service_name на $host:$port..."
    
    if timeout $timeout bash -c "nc -z $host $port" 2>/dev/null; then
        log_success "$service_name доступен"
        return 0
    else
        log_error "$service_name недоступен на $host:$port"
        return 1
    fi
}

check_minio_api() {
    local endpoint=$1
    local timeout=${2:-10}
    
    log "Проверка MinIO API на $endpoint..."
    
    if timeout $timeout bash -c "curl -s -f http://$endpoint/minio/health/live" >/dev/null 2>&1; then
        log_success "MinIO API доступен"
        return 0
    else
        log_warning "MinIO API недоступен, проверяю TCP соединение..."
        local host=$(echo $endpoint | cut -d: -f1)
        local port=$(echo $endpoint | cut -d: -f2)
        check_service "MinIO TCP" $host $port
        return $?
    fi
}

main() {
    log "🔍 Проверка внешних сервисов для Aisha Bot v2..."
    
    local all_ok=true
    
    # PostgreSQL
    if ! check_service "PostgreSQL" "$DATABASE_HOST" "5432"; then
        all_ok=false
    fi
    
    # Redis
    if ! check_service "Redis" "$REDIS_HOST" "6379"; then
        all_ok=false
    fi
    
    # MinIO
    if ! check_minio_api "$MINIO_ENDPOINT"; then
        all_ok=false
    fi
    
    echo ""
    if [ "$all_ok" = true ]; then
        log_success "🎉 Все внешние сервисы доступны! Можно запускать приложения."
        exit 0
    else
        log_error "❌ Не все сервисы доступны. Проверьте конфигурацию и доступность сервисов."
        echo ""
        echo "📋 Полезные команды для диагностики:"
        echo "  - PostgreSQL: psql -h $DATABASE_HOST -p 5432 -U aisha -d aisha_v2"
        echo "  - Redis: redis-cli -h $REDIS_HOST -p 6379 ping"
        echo "  - MinIO: curl http://$MINIO_ENDPOINT/minio/health/live"
        exit 1
    fi
}

main "$@" 