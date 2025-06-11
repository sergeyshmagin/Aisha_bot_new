#!/bin/bash

# 🚀 Скрипт деплоя Aisha Bot через Docker Registry
# Версия: 2.0 (2025-06-11)

set -euo pipefail

# 🎨 Цвета для вывода
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# 📋 Конфигурация
readonly REGISTRY="192.168.0.4:5000"
readonly PROD_SERVER="192.168.0.10"
readonly PROD_USER="aisha"

# 🚀 Функции логирования
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

# 🔍 Проверка предварительных условий
check_prerequisites() {
    log_info "Проверка предварительных условий..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен!"
        exit 1
    fi
    
    if ! command -v ssh &> /dev/null; then
        log_error "SSH клиент не установлен!"
        exit 1
    fi
    
    # Проверка доступности реестра
    if ! curl -s "http://${REGISTRY}/v2/" > /dev/null; then
        log_error "Docker Registry ${REGISTRY} недоступен!"
        exit 1
    fi
    
    log_success "Все предварительные условия выполнены"
}

# 🏗️ Сборка и пуш образов
build_and_push() {
    local image_tag=${1:-"latest"}
    
    log_info "Сборка образа aisha-bot:${image_tag}..."
    docker build -t "aisha-bot:${image_tag}" -f docker/Dockerfile.bot .
    
    log_info "Тегирование для реестра..."
    docker tag "aisha-bot:${image_tag}" "${REGISTRY}/aisha-bot:${image_tag}"
    
    log_info "Пуш в реестр ${REGISTRY}..."
    docker push "${REGISTRY}/aisha-bot:${image_tag}"
    
    log_success "Образ ${REGISTRY}/aisha-bot:${image_tag} загружен в реестр"
}

# 🔄 Деплой на продакшн
deploy_to_production() {
    local image_tag=${1:-"latest"}
    
    log_info "Деплой на продакшн сервер ${PROD_SERVER}..."
    
    # Обновление docker-compose файла
    ssh "${PROD_USER}@${PROD_SERVER}" "
        cd /opt/aisha-backend && 
        sed -i 's|image: .*aisha-bot.*|image: ${REGISTRY}/aisha-bot:${image_tag}|g' docker-compose.bot.simple.yml
    "
    
    # Загрузка нового образа
    ssh "${PROD_USER}@${PROD_SERVER}" "
        cd /opt/aisha-backend && 
        docker pull ${REGISTRY}/aisha-bot:${image_tag}
    "
    
    # Перезапуск контейнеров
    ssh "${PROD_USER}@${PROD_SERVER}" "
        cd /opt/aisha-backend && 
        docker-compose -f docker-compose.bot.simple.yml down &&
        docker-compose -f docker-compose.bot.simple.yml up -d
    "
    
    log_success "Деплой завершен успешно!"
}

# 🔍 Проверка состояния
check_health() {
    log_info "Проверка состояния сервисов..."
    
    ssh "${PROD_USER}@${PROD_SERVER}" "
        cd /opt/aisha-backend && 
        docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'
    "
    
    log_info "Проверка логов..."
    ssh "${PROD_USER}@${PROD_SERVER}" "
        cd /opt/aisha-backend && 
        docker logs aisha-bot-primary --tail 10
    "
}

# 📋 Показать справку
show_help() {
    cat << EOF
🚀 Скрипт деплоя Aisha Bot через Docker Registry

Использование: $0 [ОПЦИИ] [ТЕГ]

ОПЦИИ:
  --build-only     Только собрать и загрузить образ
  --deploy-only    Только деплой (без сборки) 
  --check-health   Только проверка состояния
  --help          Показать эту справку

ТЕГ:
  latest          По умолчанию
  v1.0.0          Версионный тег
  fix-123         Тег исправления

Примеры:
  $0                        # Полный деплой с тегом latest
  $0 --build-only v1.0.0    # Только сборка версии v1.0.0  
  $0 --deploy-only          # Только деплой latest
  $0 --check-health         # Проверка состояния

Серверы:
  Registry: ${REGISTRY}
  Production: ${PROD_USER}@${PROD_SERVER}
EOF
}

# 🎯 Основная функция
main() {
    local build_only=false
    local deploy_only=false
    local check_health_only=false
    local image_tag="latest"
    
    # Парсинг аргументов
    while [[ $# -gt 0 ]]; do
        case $1 in
            --build-only)
                build_only=true
                shift
                ;;
            --deploy-only)
                deploy_only=true
                shift
                ;;
            --check-health)
                check_health_only=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                image_tag="$1"
                shift
                ;;
        esac
    done
    
    log_info "🚀 Запуск деплоя Aisha Bot"
    log_info "📋 Тег образа: ${image_tag}"
    log_info "🏗️ Registry: ${REGISTRY}"
    log_info "🎯 Production: ${PROD_USER}@${PROD_SERVER}"
    
    check_prerequisites
    
    if [[ "$check_health_only" == true ]]; then
        check_health
        exit 0
    fi
    
    if [[ "$deploy_only" != true ]]; then
        build_and_push "$image_tag"
    fi
    
    if [[ "$build_only" != true ]]; then
        deploy_to_production "$image_tag"
        check_health
    fi
    
    log_success "🎉 Деплой завершен успешно!"
}

# Запуск
main "$@" 