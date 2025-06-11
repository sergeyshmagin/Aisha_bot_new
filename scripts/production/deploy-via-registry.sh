#!/bin/bash

# ============================================================================
# Скрипт деплоя Aisha Bot через Docker Registry (v2.0)
# Улучшения:
# - Проверка и создание Docker сети
# - Кеширование зависимостей
# - Быстрый режим деплоя
# - Улучшенная обработка ошибок
# ============================================================================

set -e

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Настройки
REGISTRY="192.168.0.4:5000"
IMAGE_NAME="aisha/bot"
PROD_SERVER="192.168.0.10"
PROD_USER="aisha"
PROD_DIR="/opt/aisha-backend"
DOCKER_NETWORK="aisha_bot_cluster"

# Параметры командной строки
SKIP_LOCAL_TEST=false
SKIP_BUILD=false
FORCE_REBUILD=false

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-test)
            SKIP_LOCAL_TEST=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        --help|-h)
            echo "Использование: $0 [OPTIONS]"
            echo "OPTIONS:"
            echo "  --skip-test      Пропустить локальное тестирование"
            echo "  --skip-build     Пропустить сборку (использовать существующий образ)"
            echo "  --force-rebuild  Принудительная пересборка без кеша"
            echo "  --help, -h       Показать справку"
            exit 0
            ;;
        *)
            log_error "Неизвестная опция: $1"
            exit 1
            ;;
    esac
done

# Получение версии из git или timestamp
get_version() {
    if git rev-parse --git-dir > /dev/null 2>&1; then
        # Используем short commit hash
        VERSION=$(git rev-parse --short HEAD)
        if [ -n "$(git status --porcelain)" ]; then
            VERSION="${VERSION}-dirty"
        fi
    else
        # Используем timestamp
        VERSION=$(date +%Y%m%d-%H%M%S)
    fi
    echo $VERSION
}

VERSION=$(get_version)
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${VERSION}"
LATEST_IMAGE="${REGISTRY}/${IMAGE_NAME}:latest"

log_info "🚀 Деплой Aisha Bot через Docker Registry v2.0"
log_info "📦 Образ: ${FULL_IMAGE}"
log_info "🏷️ Версия: ${VERSION}"
echo ""

# ============================================================================
# Шаг 1: Проверка окружения
# ============================================================================

check_environment() {
    log_step "1️⃣ Проверка окружения..."
    
    # Проверяем Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен"
        exit 1
    fi
    
    # Проверяем Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен"
        exit 1
    fi
    
    # Проверяем подключение к registry
    if ! docker pull ${REGISTRY}/hello-world:latest 2>/dev/null; then
        log_warn "Не удается подключиться к registry ${REGISTRY}"
        log_info "Попробуем продолжить..."
    fi
    
    # Проверяем подключение к продакшн серверу
    if ! ssh -o ConnectTimeout=5 ${PROD_USER}@${PROD_SERVER} "echo 'SSH connected'" &>/dev/null; then
        log_error "Не удается подключиться к продакшн серверу ${PROD_SERVER}"
        exit 1
    fi
    
    # Проверяем и создаем Docker сеть на продакшне
    log_info "🔗 Проверка Docker сети на продакшне..."
    ssh ${PROD_USER}@${PROD_SERVER} << EOF
if ! docker network ls | grep -q "${DOCKER_NETWORK}"; then
    echo "Создание Docker сети ${DOCKER_NETWORK} с подсетью..."
    docker network create --subnet=172.26.0.0/16 ${DOCKER_NETWORK}
    echo "✅ Сеть ${DOCKER_NETWORK} создана"
else
    # Проверяем есть ли подсеть
    NETWORK_INFO=\$(docker network inspect ${DOCKER_NETWORK} 2>/dev/null | grep -o '"Subnet": "[^"]*"' | head -1)
    if [ -z "\$NETWORK_INFO" ]; then
        echo "Пересоздание сети ${DOCKER_NETWORK} с подсетью..."
        docker network rm ${DOCKER_NETWORK}
        docker network create --subnet=172.26.0.0/16 ${DOCKER_NETWORK}
        echo "✅ Сеть ${DOCKER_NETWORK} пересоздана с подсетью"
    else
        echo "✅ Сеть ${DOCKER_NETWORK} уже существует с подсетью"
    fi
fi
EOF
    
    log_info "✅ Окружение проверено"
}

# ============================================================================
# Шаг 2: Локальное тестирование (опционально)
# ============================================================================

local_test() {
    if [ "$SKIP_LOCAL_TEST" = true ]; then
        log_info "⏭️ Локальное тестирование пропущено"
        return 0
    fi
    
    log_step "2️⃣ Локальное тестирование..."
    
    # Останавливаем существующие dev контейнеры
    log_info "🛑 Остановка существующих dev контейнеров..."
    docker-compose -f docker-compose.bot.dev.yml down || true
    
    # Собираем образ для тестирования с кешированием
    log_info "🔨 Сборка образа для тестирования..."
    if [ "$FORCE_REBUILD" = true ]; then
        docker-compose -f docker-compose.bot.dev.yml build --no-cache aisha-bot-dev
    else
        docker-compose -f docker-compose.bot.dev.yml build aisha-bot-dev
    fi
    
    # Запускаем для тестирования
    log_info "🧪 Запуск локального тестирования..."
    docker-compose -f docker-compose.bot.dev.yml up -d
    
    # Ждем запуска
    log_info "⏱️ Ожидание запуска (30 секунд)..."
    sleep 30
    
    # Проверяем health
    log_info "🔍 Проверка состояния контейнеров..."
    if ! docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(aisha-bot-dev|aisha-worker-dev)"; then
        log_error "Контейнеры не запустились"
        docker-compose -f docker-compose.bot.dev.yml logs
        exit 1
    fi
    
    # Проверяем логи на ошибки
    log_info "📋 Проверка логов на критические ошибки..."
    if docker-compose -f docker-compose.bot.dev.yml logs --tail 50 | grep -i "critical\|fatal\|error" | grep -v "TelegramNetworkError\|Request timeout\|Token is invalid"; then
        log_warn "Обнаружены ошибки в логах, но продолжаем..."
    fi
    
    log_info "✅ Локальное тестирование завершено"
    
    # Запрашиваем подтверждение
    echo ""
    read -p "$(echo -e ${YELLOW}Продолжить деплой на продакшн? [y/N]: ${NC})" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Деплой отменен пользователем"
        docker-compose -f docker-compose.bot.dev.yml down
        exit 0
    fi
}

# ============================================================================
# Шаг 3: Сборка и пуш в Registry (опционально)
# ============================================================================

build_and_push() {
    if [ "$SKIP_BUILD" = true ]; then
        log_info "⏭️ Сборка пропущена, используется существующий образ"
        return 0
    fi
    
    log_step "3️⃣ Сборка и отправка в Registry..."
    
    # Проверяем, существует ли образ
    if [ "$FORCE_REBUILD" = false ] && docker manifest inspect ${LATEST_IMAGE} &>/dev/null; then
        log_info "🔄 Образ уже существует в registry"
        read -p "$(echo -e ${YELLOW}Пересобрать образ? [y/N]: ${NC})" -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Используется существующий образ"
            return 0
        fi
    fi
    
    # Сборка production образа с кешированием
    log_info "🔨 Сборка production образа..."
    BUILD_ARGS=""
    if [ "$FORCE_REBUILD" = false ]; then
        BUILD_ARGS="--cache-from ${LATEST_IMAGE}"
    else
        BUILD_ARGS="--no-cache"
    fi
    
    docker build -f docker/Dockerfile.bot ${BUILD_ARGS} -t ${FULL_IMAGE} -t ${LATEST_IMAGE} .
    
    # Пуш образов в registry
    log_info "📤 Отправка в registry..."
    docker push ${FULL_IMAGE}
    docker push ${LATEST_IMAGE}
    
    log_info "✅ Образ отправлен в registry"
}

# ============================================================================
# Шаг 4: Деплой на продакшн
# ============================================================================

deploy_to_production() {
    log_step "4️⃣ Деплой на продакшн сервер..."
    
    # Создаем backup конфигурации
    log_info "💾 Создание backup конфигурации..."
    ssh ${PROD_USER}@${PROD_SERVER} "cd ${PROD_DIR} && cp docker-compose.bot.simple.yml docker-compose.bot.simple.yml.backup.$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
    
    # Останавливаем только bot контейнеры, webhook оставляем
    log_info "🛑 Остановка bot контейнеров на продакшн..."
    ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
cd /opt/aisha-backend

# Останавливаем только bot контейнеры
docker-compose -f docker-compose.bot.simple.yml down || true

echo "Bot контейнеры остановлены"
EOF
    
    # Пуллим новый образ
    log_info "📥 Загрузка нового образа на продакшн..."
    ssh ${PROD_USER}@${PROD_SERVER} "docker pull ${LATEST_IMAGE}"
    
    # Запускаем обновленные контейнеры
    log_info "🚀 Запуск обновленных bot контейнеров..."
    ssh ${PROD_USER}@${PROD_SERVER} << EOF
cd /opt/aisha-backend

# Запускаем bot сервисы
docker-compose -f docker-compose.bot.simple.yml up -d

echo "Bot контейнеры запущены"
EOF
    
    log_info "✅ Деплой на продакшн завершен"
}

# ============================================================================
# Шаг 5: Проверка деплоя
# ============================================================================

verify_deployment() {
    log_step "5️⃣ Проверка деплоя..."
    
    # Ждем запуска
    log_info "⏱️ Ожидание запуска на продакшн (30 секунд)..."
    sleep 30
    
    # Проверяем статус контейнеров
    log_info "📊 Проверка статуса контейнеров..."
    ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
echo "=== Статус контейнеров ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep -E "(bot|webhook)"

echo ""
echo "=== Последние логи primary bot ==="
docker logs aisha-bot-primary --tail 10 2>/dev/null || echo "Контейнер aisha-bot-primary не найден"

echo ""
echo "=== Последние логи worker ==="
docker logs aisha-worker-1 --tail 5 2>/dev/null || echo "Контейнер aisha-worker-1 не найден"
EOF
    
    # Проверяем логи на ошибки
    log_info "🔍 Проверка на критические ошибки..."
    if ssh ${PROD_USER}@${PROD_SERVER} "docker logs aisha-bot-primary --tail 20 2>/dev/null" | grep -i "critical\|fatal" | grep -v "TelegramNetworkError"; then
        log_warn "Обнаружены критические ошибки в логах"
        log_warn "Проверьте логи: ssh ${PROD_USER}@${PROD_SERVER} 'cd ${PROD_DIR} && docker logs aisha-bot-primary --tail 50'"
    else
        log_info "✅ Критических ошибок не обнаружено"
    fi
    
    log_info "✅ Проверка деплоя завершена"
}

# ============================================================================
# Шаг 6: Очистка
# ============================================================================

cleanup() {
    log_step "6️⃣ Очистка..."
    
    # Остановка dev контейнеров
    if [ "$SKIP_LOCAL_TEST" = false ]; then
        log_info "🧹 Остановка dev контейнеров..."
        docker-compose -f docker-compose.bot.dev.yml down || true
    fi
    
    # Очистка неиспользуемых образов
    log_info "🗑️ Очистка старых образов..."
    docker image prune -f || true
    
    log_info "✅ Очистка завершена"
}

# ============================================================================
# Основной процесс
# ============================================================================

main() {
    echo "🎯 Цель: Деплой версии ${VERSION} на продакшн"
    echo "📍 Registry: ${REGISTRY}"
    echo "🖥️ Продакшн: ${PROD_SERVER}"
    echo "⚙️ Режим: skip-test=${SKIP_LOCAL_TEST}, skip-build=${SKIP_BUILD}, force-rebuild=${FORCE_REBUILD}"
    echo ""
    
    check_environment
    echo ""
    
    local_test
    echo ""
    
    build_and_push
    echo ""
    
    deploy_to_production
    echo ""
    
    verify_deployment
    echo ""
    
    cleanup
    echo ""
    
    log_info "🎉 Деплой версии ${VERSION} успешно завершен!"
    log_info ""
    log_info "📊 Команды для мониторинга:"
    log_info "   ssh ${PROD_USER}@${PROD_SERVER} 'cd ${PROD_DIR} && docker logs aisha-bot-primary --tail 50'"
    log_info "   ssh ${PROD_USER}@${PROD_SERVER} 'cd ${PROD_DIR} && docker ps'"
    log_info ""
    log_info "🚀 Быстрый деплой в следующий раз:"
    log_info "   bash scripts/production/deploy-via-registry.sh --skip-test --skip-build"
}

# Запуск с обработкой ошибок
trap 'log_error "Деплой прерван из-за ошибки"; cleanup; exit 1' ERR

main "$@" 