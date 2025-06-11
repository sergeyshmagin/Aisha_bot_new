#!/bin/bash

# ============================================================================
# Быстрый деплой исправлений в продакшн
# ============================================================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Настройки
REGISTRY="192.168.0.4:5000"
IMAGE_NAME="aisha/bot"
PROD_SERVER="192.168.0.10"
PROD_USER="aisha"

# Функции логирования
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Генерация тега с текущим временем
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TAG="fix-help-${TIMESTAMP}"

log_info "🚀 Быстрый деплой исправления: ${TAG}"

# Проверка виртуального окружения
if [[ "$VIRTUAL_ENV" == "" ]]; then
    log_warn "⚠️  Виртуальное окружение не активировано"
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
        log_info "✅ Виртуальное окружение активировано"
    else
        log_error "❌ Виртуальное окружение не найдено"
        exit 1
    fi
fi

# 1. Сборка образа
log_info "🔨 Сборка образа с тегом ${TAG}..."
docker build -t ${REGISTRY}/${IMAGE_NAME}:${TAG} -f docker/Dockerfile.bot .

# 2. Отправка в registry
log_info "📤 Отправка образа в registry..."
docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}

# 3. Обновление latest тега
log_info "🏷️  Обновление latest тега..."
docker tag ${REGISTRY}/${IMAGE_NAME}:${TAG} ${REGISTRY}/${IMAGE_NAME}:latest
docker push ${REGISTRY}/${IMAGE_NAME}:latest

# 4. Деплой на продакшн
log_info "🚀 Деплой на продакшн сервер..."
ssh ${PROD_USER}@${PROD_SERVER} << EOF
    set -e
    
    echo "📥 Получение нового образа..."
    docker pull ${REGISTRY}/${IMAGE_NAME}:latest
    
    echo "🔄 Перезапуск bot контейнеров..."
    cd /opt/aisha-backend
    docker-compose -f docker-compose.bot.simple.yml down
    docker-compose -f docker-compose.bot.simple.yml up -d
    
    echo "⏳ Ожидание запуска..."
    sleep 10
    
    echo "📊 Статус контейнеров:"
    docker-compose -f docker-compose.bot.simple.yml ps
    
    echo "🎉 Деплой завершен!"
EOF

log_info "✅ Исправление успешно развернуто!"
log_info "🏷️  Тег: ${TAG}"
log_info "📋 Проверка логов: ssh ${PROD_USER}@${PROD_SERVER} 'docker-compose -f /opt/aisha-backend/docker-compose.bot.simple.yml logs -f --tail=50'" 