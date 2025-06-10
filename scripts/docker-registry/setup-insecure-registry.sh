#!/bin/bash

# 🔓 Настройка Insecure Docker Registry для разработки
# Более простая альтернатива HTTPS для внутренней сети

set -euo pipefail

REGISTRY_HOST="192.168.0.4"
REGISTRY_PORT="5000"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >&2
}

configure_docker_daemon() {
    log "🔧 Настройка Docker daemon для insecure registry..."
    
    # Создаем конфигурацию daemon.json
    DAEMON_CONFIG="/etc/docker/daemon.json"
    
    # Создаем резервную копию если файл существует
    if [[ -f "$DAEMON_CONFIG" ]]; then
        sudo cp "$DAEMON_CONFIG" "$DAEMON_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        log "📋 Создана резервная копия: $DAEMON_CONFIG.backup.*"
    fi
    
    # Создаем новую конфигурацию
    sudo tee "$DAEMON_CONFIG" > /dev/null << EOF
{
  "insecure-registries": [
    "$REGISTRY_HOST:$REGISTRY_PORT"
  ],
  "registry-mirrors": [],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
    
    log "✅ Конфигурация Docker daemon обновлена"
}

restart_docker() {
    log "🔄 Перезапуск Docker..."
    
    if command -v systemctl &> /dev/null; then
        sudo systemctl restart docker
        sleep 5
        if systemctl is-active --quiet docker; then
            log "✅ Docker перезапущен успешно"
        else
            log_error "❌ Ошибка перезапуска Docker"
            exit 1
        fi
    else
        log "⚠️  systemctl не найден. Перезапустите Docker вручную"
    fi
}

test_registry() {
    log "🧪 Тестирование подключения к registry..."
    
    # Тестируем HTTP подключение
    if curl -f "http://$REGISTRY_HOST:$REGISTRY_PORT/v2/" &>/dev/null; then
        log "✅ HTTP подключение к registry работает"
        
        # Показываем каталог
        CATALOG=$(curl -s "http://$REGISTRY_HOST:$REGISTRY_PORT/v2/_catalog")
        log "📋 Каталог образов: $CATALOG"
    else
        log_error "❌ Не удается подключиться к registry"
        return 1
    fi
}

show_usage() {
    log "📖 Использование insecure registry:"
    cat << EOF

1. Тегирование образа:
   docker tag my-image:latest $REGISTRY_HOST:$REGISTRY_PORT/my-image:latest

2. Push образа:
   docker push $REGISTRY_HOST:$REGISTRY_PORT/my-image:latest

3. Pull образа:
   docker pull $REGISTRY_HOST:$REGISTRY_PORT/my-image:latest

4. Список репозиториев:
   curl http://$REGISTRY_HOST:$REGISTRY_PORT/v2/_catalog

5. Просмотр тегов:
   curl http://$REGISTRY_HOST:$REGISTRY_PORT/v2/my-image/tags/list

⚠️  ВНИМАНИЕ: Insecure registry не использует шифрование!
   Используйте только во внутренней сети для разработки.

EOF
}

main() {
    log "🔓 Настройка insecure Docker registry клиента"
    
    # Проверяем права
    if [[ $EUID -eq 0 ]]; then
        log_error "Не запускайте скрипт от root"
        exit 1
    fi
    
    # Выполняем настройку
    configure_docker_daemon
    
    # Перезапускаем Docker если возможно
    if command -v systemctl &> /dev/null; then
        restart_docker
    else
        log "⚠️  Перезапустите Docker Desktop вручную для применения изменений"
    fi
    
    # Тестируем подключение
    test_registry
    
    # Показываем примеры использования
    show_usage
    
    log "🎉 Insecure registry настроен успешно!"
}

# Запуск скрипта
main "$@" 