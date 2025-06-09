#!/bin/bash

# ============================================================================
# Локальный скрипт развертывания кластера Aisha Bot
# Запускается непосредственно на продакшн сервере
# ============================================================================

set -e

# Конфигурация
REGISTRY_URL="192.168.0.4:5000"
DOMAIN="aibots.kz"
IMAGE_VERSION="latest"
DEPLOY_DIR="/opt/aisha-backend"

# Параметры командной строки
FORCE_PULL=false
SKIP_REGISTRY_CHECK=false
VERBOSE=false

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Показать справку
show_help() {
    cat << EOF
Использование: $0 [версия] [опции]

Локальный скрипт развертывания кластера Aisha Bot

Аргументы:
  версия               Версия образов из registry (по умолчанию: latest)

Опции:
  --force-pull        Принудительно скачать образы из registry
  --skip-registry     Пропустить проверку registry
  --verbose           Подробный вывод команд
  -h, --help          Показать эту справку

Примеры:
  $0                          # Развернуть latest версию
  $0 v2.1.0                   # Развернуть версию v2.1.0
  $0 v2.1.0 --force-pull      # Принудительно скачать v2.1.0

Требования:
  - Docker registry доступен на ${REGISTRY_URL}
  - Образы запушены в registry:
    • ${REGISTRY_URL}/aisha/nginx:${IMAGE_VERSION}
    • ${REGISTRY_URL}/aisha/webhook:${IMAGE_VERSION}
    • ${REGISTRY_URL}/aisha/bot:${IMAGE_VERSION}

EOF
}

# Обработка параметров командной строки
parse_args() {
    # Сначала обрабатываем позиционный аргумент версии
    if [[ $# -gt 0 && ! "$1" =~ ^-- ]]; then
        IMAGE_VERSION="$1"
        shift
    fi
    
    # Затем обрабатываем флаги
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force-pull)
                FORCE_PULL=true
                shift
                ;;
            --skip-registry)
                SKIP_REGISTRY_CHECK=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            --*)
                log_error "Неизвестный параметр: $1"
                log_info "Используйте '$0 --help' для справки"
                exit 1
                ;;
            *)
                log_error "Неожиданный аргумент: $1"
                log_info "Используйте '$0 --help' для справки"
                exit 1
                ;;
        esac
    done
}

# Проверка registry
check_registry_access() {
    if [[ "$SKIP_REGISTRY_CHECK" == "true" ]]; then
        log_step "⏭️ Пропуск проверки registry"
        return 0
    fi
    
    log_step "🐳 Проверка доступности Docker Registry..."
    
    # Проверка доступности registry
    if nc -z 192.168.0.4 5000 2>/dev/null; then
        log_info "✅ Registry $REGISTRY_URL доступен"
    else
        log_error "❌ Registry $REGISTRY_URL недоступен"
        exit 1
    fi
    
    # Проверка образов в registry
    local images=("nginx" "webhook" "bot")
    
    for image in "${images[@]}"; do
        local registry_path="/aisha/${image}/tags/list"
        
        if curl -f -s http://$REGISTRY_URL/v2${registry_path} | grep -q "\"${IMAGE_VERSION}\""; then
            log_info "✅ ${image}:${IMAGE_VERSION} найден в registry"
        else
            log_warn "⚠️ ${image}:${IMAGE_VERSION} не найден в registry"
        fi
    done
}

# Настройка Docker
setup_docker() {
    log_step "🐳 Настройка Docker..."
    
    # Проверка установки Docker
    log_info "🔍 Проверка установки Docker..."
    if ! command -v docker >/dev/null 2>&1; then
        log_error "❌ Docker не установлен"
        log_error "Установите Docker: curl -fsSL https://get.docker.com | sh"
        exit 1
    fi
    
    # Проверка запуска Docker службы
    log_info "🔍 Проверка запуска Docker службы..."
    if ! sudo systemctl is-active docker >/dev/null 2>&1; then
        log_info "🚀 Запуск Docker службы..."
        sudo systemctl start docker || {
            log_error "❌ Не удалось запустить Docker службу"
            exit 1
        }
    fi
    
    # Проверка настройки insecure registry
    log_info "🔧 Проверка настройки insecure registry..."
    if docker info 2>/dev/null | grep -q "$REGISTRY_URL"; then
        log_info "✅ Registry $REGISTRY_URL уже настроен в Docker"
    else
        log_info "⚙️ Настройка insecure registry..."
        sudo mkdir -p /etc/docker || true
        echo "{\"insecure-registries\": [\"$REGISTRY_URL\"]}" | sudo tee /etc/docker/daemon.json || true
        sudo systemctl restart docker || {
            log_warn "⚠️ Не удалось перезапустить Docker daemon"
            log_warn "Попробуйте вручную: sudo systemctl restart docker"
        }
        
        # Ожидание перезапуска Docker
        log_info "⏳ Ожидание перезапуска Docker..."
        sleep 10
        
        # Проверка что Docker запустился
        local retries=0
        local max_retries=6
        while [[ $retries -lt $max_retries ]]; do
            if docker info >/dev/null 2>&1; then
                log_info "✅ Docker успешно перезапущен"
                break
            fi
            
            log_info "⏳ Ожидание Docker... ($((retries + 1))/$max_retries)"
            sleep 5
            ((retries++))
        done
        
        if [[ $retries -eq $max_retries ]]; then
            log_error "❌ Docker не отвечает после перезапуска"
            exit 1
        fi
    fi
    
    log_info "✅ Docker настроен"
}

# Подготовка рабочей директории
prepare_deploy_dir() {
    log_step "📁 Подготовка рабочей директории..."
    
    # Проверка и создание директории
    if [[ ! -d "$DEPLOY_DIR" ]]; then
        log_info "📁 Создание директории $DEPLOY_DIR..."
        sudo mkdir -p "$DEPLOY_DIR" || {
            log_error "Не удалось создать директорию $DEPLOY_DIR"
            exit 1
        }
        sudo chown $USER:$USER "$DEPLOY_DIR" || {
            log_error "Не удалось изменить владельца директории $DEPLOY_DIR"
            exit 1
        }
    else
        log_info "✅ Директория $DEPLOY_DIR уже существует"
    fi
    
    cd "$DEPLOY_DIR"
    log_info "✅ Рабочая директория готова: $DEPLOY_DIR"
}

# Создание Docker сетей
create_networks() {
    log_step "🌐 Создание Docker сетей..."
    
    # Удаление существующих сетей
    docker network rm aisha_cluster aisha_bot_cluster 2>/dev/null || true
    
    # Создание новых сетей
    docker network create --driver bridge --subnet=172.25.0.0/16 aisha_cluster || true
    docker network create --driver bridge --subnet=172.26.0.0/16 aisha_bot_cluster || true
    
    log_info "✅ Docker сети созданы"
}

# Пулл образов из registry
pull_images() {
    log_step "📥 Загрузка образов из registry..."
    
    local images=("nginx" "webhook" "bot")
    
    for image in "${images[@]}"; do
        local registry_image="${REGISTRY_URL}/aisha/${image}:${IMAGE_VERSION}"
        
        log_info "📥 Загрузка $registry_image..."
        
        if [[ "$FORCE_PULL" == "true" ]]; then
            docker pull $registry_image
        else
            docker pull $registry_image 2>/dev/null || true
        fi
    done
    
    log_info "✅ Образы загружены"
}

# Остановка старых контейнеров
stop_old_containers() {
    log_step "🛑 Остановка старых контейнеров..."
    
    # Остановка docker-compose сервисов
    docker-compose -f docker-compose.registry.yml --env-file cluster.env down 2>/dev/null || true
    docker-compose -f docker-compose.bot.registry.yml --env-file cluster.env down 2>/dev/null || true
    
    # Принудительная остановка всех Aisha контейнеров
    docker stop $(docker ps -q --filter 'name=aisha') 2>/dev/null || true
    docker rm $(docker ps -aq --filter 'name=aisha') 2>/dev/null || true
    
    log_info "✅ Старые контейнеры остановлены"
}

# Развертывание Webhook API кластера
deploy_api_cluster() {
    log_step "🚀 Развертывание Webhook API кластера..."
    
    # Установка переменной версии образа
    export IMAGE_VERSION=$IMAGE_VERSION
    docker-compose -f docker-compose.registry.yml --env-file cluster.env up -d
    
    # Ожидание запуска сервисов
    log_info "⏳ Ожидание запуска API сервисов..."
    sleep 15
    
    # Проверка health check
    local retries=0
    local max_retries=12
    while [[ $retries -lt $max_retries ]]; do
        if docker ps --filter 'name=aisha-webhook-api' --filter 'health=healthy' | grep -q aisha-webhook-api; then
            log_info "✅ Webhook API кластер готов"
            return 0
        fi
        
        log_info "⏳ Ожидание готовности API сервисов... ($((retries + 1))/$max_retries)"
        sleep 5
        ((retries++))
    done
    
    log_warn "⚠️ Webhook API сервисы могут быть еще не готовы"
}

# Развертывание Bot кластера
deploy_bot_cluster() {
    log_step "🤖 Развертывание Bot кластера..."
    
    # Развертывание ботов
    export IMAGE_VERSION=$IMAGE_VERSION
    docker-compose -f docker-compose.bot.registry.yml --env-file cluster.env up -d
    
    # Ожидание запуска ботов
    log_info "⏳ Ожидание запуска ботов..."
    sleep 10
    
    # Проверка health check
    local retries=0
    local max_retries=8
    while [[ $retries -lt $max_retries ]]; do
        if docker ps --filter 'name=aisha-bot' --filter 'health=healthy' | grep -q aisha-bot; then
            log_info "✅ Bot кластер готов"
            return 0
        fi
        
        log_info "⏳ Ожидание готовности Bot сервисов... ($((retries + 1))/$max_retries)"
        sleep 5
        ((retries++))
    done
    
    log_warn "⚠️ Bot сервисы могут быть еще не готовы"
}

# Финальная проверка
final_check() {
    log_step "🔍 Финальная проверка развертывания..."
    
    # Статус контейнеров
    log_info "📊 Статус контейнеров:"
    docker ps --filter 'name=aisha' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
    
    # Проверка доступности сервисов
    log_info "🌐 Проверка доступности..."
    
    # HTTP
    if curl -f -s -m 5 http://localhost/ >/dev/null 2>&1; then
        log_info "✅ HTTP (80) доступен"
    else
        log_warn "⚠️ HTTP (80) недоступен"
    fi
    
    # HTTPS
    if curl -f -s -k -m 5 https://localhost:8443/ >/dev/null 2>&1; then
        log_info "✅ HTTPS (8443) доступен"
    else
        log_warn "⚠️ HTTPS (8443) недоступен"
    fi
    
    log_info "📋 Мониторинг: docker ps"
}

# Основная функция
main() {
    # Парсинг аргументов
    parse_args "$@"
    
    log_info "🚀 Локальное развертывание кластера Aisha Bot"
    log_info "🐳 Registry: $REGISTRY_URL"
    log_info "🏷️ Версия: $IMAGE_VERSION"
    log_info "📁 Директория: $DEPLOY_DIR"
    
    if [[ "$FORCE_PULL" == "true" ]]; then
        log_warn "⚠️ Принудительная загрузка образов включена"
    fi
    
    # Выполнение шагов развертывания
    check_registry_access
    setup_docker
    prepare_deploy_dir
    create_networks
    pull_images
    stop_old_containers
    deploy_api_cluster
    deploy_bot_cluster
    final_check
    
    log_info "🎉 Локальное развертывание завершено успешно!"
    log_info "🌐 Доступ: http://$DOMAIN и https://$DOMAIN:8443"
}

# Обработка сигналов
trap 'log_error "🛑 Развертывание прервано"; exit 1' SIGINT SIGTERM

# Запуск
main "$@" 