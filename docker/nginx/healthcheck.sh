#!/bin/sh

# Healthcheck скрипт для nginx контейнера
# Проверяет доступность nginx и backend сервисов

# Функция для логирования
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Проверка nginx процесса
if ! pgrep nginx > /dev/null; then
    log "ERROR: nginx процесс не запущен"
    exit 1
fi

# Проверка HTTP порта
if ! curl -sf http://localhost/health > /dev/null; then
    log "ERROR: HTTP healthcheck не прошел"
    exit 1
fi

# Проверка HTTPS порта (если есть SSL сертификаты)
if [ -f /etc/nginx/ssl/aibots_kz.crt ]; then
    if ! curl -sfk https://localhost/health > /dev/null; then
        log "ERROR: HTTPS healthcheck не прошел"
        exit 1
    fi
fi

# Проверка backend API (если доступен)
if ! curl -sf http://aisha-api-prod:8000/health > /dev/null 2>&1; then
    log "WARNING: Backend API недоступен"
    # Не завершаем с ошибкой, так как nginx может работать без backend
fi

log "SUCCESS: Все проверки прошли успешно"
exit 0 