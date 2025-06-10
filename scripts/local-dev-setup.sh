#!/bin/bash
# ==============================================================================
# 🔧 НАСТРОЙКА ЛОКАЛЬНОЙ РАЗРАБОТКИ AISHA BOT
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Функция для проверки зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose не установлен"
        exit 1
    fi
    
    log_success "Все зависимости установлены"
}

# Функция для настройки .env файла
setup_env() {
    log_info "Настройка переменных окружения..."
    
    if [[ ! -f ".env.local" ]]; then
        log_warning ".env.local не найден, копирую с продакшн сервера..."
        if scp aisha@192.168.0.10:/opt/aisha-backend/.env .env.local 2>/dev/null; then
            log_success ".env.local скопирован с продакшн сервера"
        else
            log_error "Не удалось скопировать .env файл с сервера"
            log_info "Создайте .env.local вручную или используйте .env.example как шаблон"
            exit 1
        fi
    fi
    
    if [[ ! -f ".env" ]]; then
        log_info "Создаю .env файл из .env.local..."
        cp .env.local .env
        log_success ".env файл создан"
    else
        log_info "Обновляю .env файл из .env.local..."
        cp .env.local .env
        log_success ".env файл обновлен"
    fi
    
    # Добавляем недостающие переменные если их нет
    if ! grep -q "FAL_WEBHOOK_SECRET" .env; then
        echo "FAL_WEBHOOK_SECRET=secure_webhook_secret_2024" >> .env
        log_info "Добавлена переменная FAL_WEBHOOK_SECRET"
    fi
}

# Функция для проверки переменных окружения
check_env_vars() {
    log_info "Проверка критически важных переменных..."
    
    # Проверяем что файл существует и не пустой
    if [[ ! -f ".env" ]] || [[ ! -s ".env" ]]; then
        log_error ".env файл не существует или пустой"
        exit 1
    fi
    
    # Проверяем критически важные переменные
    local required_vars=(
        "TELEGRAM_BOT_TOKEN"
        "OPENAI_API_KEY" 
        "FAL_API_KEY"
        "DATABASE_URL"
        "REDIS_URL"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Отсутствуют обязательные переменные в .env файле:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi
    
    log_success "Все обязательные переменные настроены"
}

# Функция для тестирования подключения к сервисам
test_connections() {
    log_info "Тестирование подключения к внешним сервисам..."
    
    # Тест PostgreSQL
    if nc -z 192.168.0.4 5432 2>/dev/null; then
        log_success "PostgreSQL (192.168.0.4:5432) доступен"
    else
        log_warning "PostgreSQL (192.168.0.4:5432) недоступен"
    fi
    
    # Тест Redis
    if nc -z 192.168.0.3 6379 2>/dev/null; then
        log_success "Redis (192.168.0.3:6379) доступен"
    else
        log_warning "Redis (192.168.0.3:6379) недоступен"
    fi
    
    # Тест MinIO
    if nc -z 192.168.0.4 9000 2>/dev/null; then
        log_success "MinIO (192.168.0.4:9000) доступен"
    else
        log_warning "MinIO (192.168.0.4:9000) недоступен"
    fi
}

# Функция для запуска разработки
start_development() {
    log_info "Запуск локальной разработки..."
    
    # Остановить существующие контейнеры если есть
    if docker-compose -f docker-compose.bot.dev.yml ps -q 2>/dev/null | grep -q .; then
        log_info "Останавливаю существующие контейнеры..."
        docker-compose -f docker-compose.bot.dev.yml down
    fi
    
    # Запустить новые контейнеры
    log_info "Запускаю контейнеры разработки..."
    docker-compose -f docker-compose.bot.dev.yml up -d
    
    log_success "Разработка запущена!"
    log_info "Команды для мониторинга:"
    echo "  docker-compose -f docker-compose.bot.dev.yml logs -f aisha-bot-dev"
    echo "  docker-compose -f docker-compose.bot.dev.yml ps"
}

# Функция для показа инструкций
show_usage() {
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  setup    - Полная настройка локальной разработки"
    echo "  env      - Настройка только .env файлов"
    echo "  check    - Проверка переменных окружения и подключений"
    echo "  start    - Запуск разработки"
    echo "  stop     - Остановка контейнеров"
    echo "  logs     - Показать логи"
    echo "  status   - Статус контейнеров"
    echo ""
    echo "Примеры:"
    echo "  $0 setup    # Полная настройка и запуск"
    echo "  $0 start    # Просто запустить разработку"
    echo "  $0 logs     # Посмотреть логи"
}

# Основная логика
case "${1:-setup}" in
    "setup")
        echo "🚀 Настройка локальной разработки Aisha Bot"
        echo "=============================================="
        check_dependencies
        setup_env
        check_env_vars
        test_connections
        start_development
        echo ""
        log_success "Настройка завершена! Бот готов к разработке."
        ;;
    
    "env")
        setup_env
        check_env_vars
        ;;
    
    "check")
        check_env_vars
        test_connections
        ;;
    
    "start")
        start_development
        ;;
    
    "stop")
        log_info "Остановка контейнеров разработки..."
        docker-compose -f docker-compose.bot.dev.yml down
        log_success "Контейнеры остановлены"
        ;;
    
    "logs")
        docker-compose -f docker-compose.bot.dev.yml logs -f aisha-bot-dev
        ;;
    
    "status")
        docker-compose -f docker-compose.bot.dev.yml ps
        ;;
    
    "--help"|"-h"|"help")
        show_usage
        ;;
    
    *)
        log_error "Неизвестная команда: $1"
        show_usage
        exit 1
        ;;
esac 