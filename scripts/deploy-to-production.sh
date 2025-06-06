#!/bin/bash

# Скрипт для развертывания nginx на продакшн сервер
# Запускать с dev сервера (192.168.0.3)

set -euo pipefail

# Конфигурация
PROD_SERVER="192.168.0.10"
PROD_USER="aisha"
PROJECT_PATH="/opt/aisha-backend"
DEPLOY_METHOD=${1:-"git"}  # git, registry, или image

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка подключения к продакшн серверу
check_connection() {
    log_info "Проверка подключения к $PROD_SERVER..."
    if ! ssh -o ConnectTimeout=5 $PROD_USER@$PROD_SERVER "echo 'Подключение успешно'" > /dev/null 2>&1; then
        log_error "Не удается подключиться к $PROD_SERVER"
        exit 1
    fi
    log_success "Подключение установлено"
}

# Метод 1: Развертывание через Git (рекомендуемый)
deploy_via_git() {
    log_info "Развертывание через Git..."
    
    CURRENT_COMMIT=$(git rev-parse HEAD)
    
    # Копируем SSL сертификаты и конфигурацию
    log_info "Копирование файлов..."
    scp ssl_certificate/* $PROD_USER@$PROD_SERVER:$PROJECT_PATH/ssl_certificate/
    scp .env.docker.prod $PROD_USER@$PROD_SERVER:$PROJECT_PATH/ 2>/dev/null || true
    
    # Развертывание на продакшн сервере
    ssh $PROD_USER@$PROD_SERVER << EOF
        cd $PROJECT_PATH
        
        # Обновляем код
        git fetch origin
        git checkout main
        git reset --hard $CURRENT_COMMIT
        
        # Делаем скрипты исполняемыми
        chmod +x scripts/*.sh docker/nginx/healthcheck.sh
        
        # Запускаем развертывание nginx
        sudo ./scripts/deploy-nginx.sh
EOF
    
    log_success "Развертывание через Git завершено"
}

# Метод 2: Развертывание через Docker Registry
deploy_via_registry() {
    log_info "Развертывание через Docker Registry..."
    
    REGISTRY="192.168.0.3:5000"
    IMAGE_NAME="aisha-nginx"
    VERSION=$(git rev-parse --short HEAD)
    
    # Сборка и публикация образа
    docker build -t $REGISTRY/$IMAGE_NAME:$VERSION docker/nginx/
    docker push $REGISTRY/$IMAGE_NAME:$VERSION
    
    # Развертывание на продакшн
    ssh $PROD_USER@$PROD_SERVER << EOF
        cd $PROJECT_PATH
        docker pull $REGISTRY/$IMAGE_NAME:$VERSION
        docker-compose -f docker-compose.prod.yml up -d nginx
EOF
    
    log_success "Развертывание через Registry завершено"
}

# Метод 3: Развертывание через Docker Save/Load
deploy_via_image() {
    log_info "Развертывание через Docker Save/Load..."
    
    # Сборка образа локально
    log_info "Сборка образа nginx..."
    docker-compose -f docker-compose.prod.yml build nginx
    
    # Сохранение образа в файл
    IMAGE_FILE="nginx-image-$(date +%Y%m%d_%H%M%S).tar.gz"
    log_info "Сохранение образа в файл $IMAGE_FILE..."
    docker save aisha-backend_nginx:latest | gzip > /tmp/$IMAGE_FILE
    
    # Копирование на продакшн сервер
    log_info "Копирование образа на продакшн сервер..."
    scp /tmp/$IMAGE_FILE $PROD_USER@$PROD_SERVER:/tmp/
    scp docker-compose.prod.yml $PROD_USER@$PROD_SERVER:$PROJECT_PATH/
    scp ssl_certificate/* $PROD_USER@$PROD_SERVER:$PROJECT_PATH/ssl_certificate/
    scp .env.docker.prod $PROD_USER@$PROD_SERVER:$PROJECT_PATH/ 2>/dev/null || true
    
    # Загрузка и запуск на продакшн сервере
    ssh $PROD_USER@$PROD_SERVER << EOF
        cd $PROJECT_PATH
        
        # Загружаем образ
        gunzip -c /tmp/$IMAGE_FILE | docker load
        
        # Удаляем временный файл
        rm -f /tmp/$IMAGE_FILE
        
        # Запускаем контейнер
        docker-compose -f docker-compose.prod.yml up -d nginx
        
        # Проверяем статус
        sleep 10
        docker-compose -f docker-compose.prod.yml ps nginx
EOF
    
    # Удаляем локальный временный файл
    rm -f /tmp/$IMAGE_FILE
    
    if [ $? -eq 0 ]; then
        log_success "Развертывание через Image завершено успешно"
    else
        log_error "Ошибка при развертывании через Image"
        exit 1
    fi
}

# Проверка здоровья после развертывания
check_deployment_health() {
    log_info "Проверка здоровья развертывания..."
    
    sleep 15  # Даем время на запуск
    
    ssh $PROD_USER@$PROD_SERVER << 'EOF'
        cd /opt/aisha-backend
        
        echo "=== Статус контейнеров ==="
        docker-compose -f docker-compose.prod.yml ps
        
        echo -e "\n=== Health Check ==="
        # Проверка HTTP
        if curl -s http://localhost/health > /dev/null; then
            echo "✓ HTTP health check: OK"
        else
            echo "✗ HTTP health check: FAILED"
        fi
        
        # Проверка HTTPS
        if curl -sk https://localhost:8443/health > /dev/null; then
            echo "✓ HTTPS health check: OK"
        else
            echo "✗ HTTPS health check: FAILED"
        fi
        
        echo -e "\n=== Логи nginx (последние 10 строк) ==="
        docker-compose -f docker-compose.prod.yml logs --tail=10 nginx
        
        echo -e "\n=== Использование ресурсов ==="
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" aisha-nginx-prod
EOF
}

# Функция отката
rollback_deployment() {
    log_warning "Выполняется откат развертывания..."
    
    ssh $PROD_USER@$PROD_SERVER << 'EOF'
        cd /opt/aisha-backend
        
        # Останавливаем контейнер
        docker-compose -f docker-compose.prod.yml stop nginx
        
        # Возвращаемся к предыдущему коммиту (если используется git)
        if [ -d ".git" ]; then
            git checkout HEAD~1
            sudo ./scripts/deploy-nginx.sh
        fi
EOF
    
    log_warning "Откат завершен"
}

# Основная логика
main() {
    echo "=== Развертывание Aisha Backend на продакшн ==="
    echo "Метод: $DEPLOY_METHOD | Сервер: $PROD_SERVER"
    
    check_connection
    
    case $DEPLOY_METHOD in
        "git")
            deploy_via_git
            ;;
        "registry") 
            deploy_via_registry
            ;;
        "image")
            deploy_via_image
            ;;
        *)
            log_error "Неизвестный метод: $DEPLOY_METHOD"
            echo "Доступные методы: git, registry, image"
            exit 1
            ;;
    esac
    
    # Проверка здоровья
    check_deployment_health
    
    log_success "Развертывание завершено!"
    log_info "Nginx доступен: https://$PROD_SERVER:8443"
}

# Обработка сигналов для отката
trap 'log_error "Развертывание прервано!"; rollback_deployment; exit 1' INT TERM

# Запуск основной логики
main "$@" 