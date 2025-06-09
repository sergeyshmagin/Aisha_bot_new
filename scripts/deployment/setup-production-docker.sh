#!/bin/bash

# ============================================================================
# Скрипт настройки Docker на продакшн сервере
# Запускать НАПРЯМУЮ на продакшн сервере с sudo правами
# ============================================================================

set -e

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

# Основная функция
main() {
    log_info "🐳 Настройка Docker на продакшн сервере"
    
    # Проверка прав
    if [[ $EUID -ne 0 ]]; then
        log_error "❌ Скрипт должен запускаться с sudo правами"
        log_info "Запустите: sudo $0"
        exit 1
    fi
    
    # Шаг 1: Проверка установки Docker
    log_step "🔍 Проверка установки Docker..."
    if ! command -v docker >/dev/null 2>&1; then
        log_error "❌ Docker не установлен"
        exit 1
    fi
    log_info "✅ Docker установлен: $(docker --version)"
    
    # Шаг 2: Добавление пользователя в группу docker
    log_step "👤 Добавление пользователя aisha в группу docker..."
    usermod -aG docker aisha
    log_info "✅ Пользователь aisha добавлен в группу docker"
    
    # Шаг 3: Настройка insecure registry
    log_step "🔧 Настройка insecure registry..."
    mkdir -p /etc/docker
    
    # Создание конфигурации Docker daemon
    cat > /etc/docker/daemon.json << EOF
{
  "insecure-registries": ["192.168.0.4:5000"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
    
    log_info "✅ Конфигурация Docker daemon создана"
    
    # Шаг 4: Перезапуск Docker
    log_step "🔄 Перезапуск Docker daemon..."
    systemctl restart docker
    systemctl enable docker
    log_info "✅ Docker daemon перезапущен"
    
    # Шаг 5: Проверка настроек
    log_step "✅ Проверка настроек..."
    sleep 3
    
    # Проверка insecure registries
    if docker info | grep -q "192.168.0.4:5000"; then
        log_info "✅ Insecure registry 192.168.0.4:5000 настроен"
    else
        log_warn "⚠️ Insecure registry может быть не настроен"
    fi
    
    # Проверка группы docker
    if groups aisha | grep -q docker; then
        log_info "✅ Пользователь aisha в группе docker"
    else
        log_warn "⚠️ Пользователь aisha может не быть в группе docker"
    fi
    
    log_info "🎉 Настройка Docker завершена!"
    log_warn "⚠️ ВАЖНО: Пользователь aisha должен выйти и войти снова для применения группы docker"
    log_info "📝 Для проверки: su - aisha, затем docker ps"
}

# Запуск
main "$@" 