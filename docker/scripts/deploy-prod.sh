#!/bin/bash

# 🚀 Скрипт развертывания Aisha Bot v2 в продакшн (/opt/aisha-backend)

set -e

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

# Проверка, что запускаем из правильной директории
if [ ! -f "docker-compose.prod.yml" ]; then
    log_error "Файл docker-compose.prod.yml не найден. Запустите скрипт из /opt/aisha-backend"
    exit 1
fi

# Проверка переменных окружения
if [ ! -f ".env.docker.prod" ]; then
    log_error "Файл .env.docker.prod не найден. Создайте его на основе env.docker.prod.template"
    exit 1
fi

log "🚀 Начинаем развертывание Aisha Bot v2 в продакшн..."

# 1. Проверка внешних сервисов
log "📋 Проверка доступности внешних сервисов..."
if ! ./docker/scripts/health-check.sh; then
    log_error "Не все внешние сервисы доступны. Остановка развертывания."
    exit 1
fi

# 2. Создание директорий для логов
log "📁 Создание директории для логов..."
sudo mkdir -p /opt/aisha-backend/logs
sudo chown -R $USER:$USER /opt/aisha-backend/logs
sudo chmod 755 /opt/aisha-backend/logs

# 3. Создание директории для логов nginx (если не существует)
if [ ! -d "/var/log/aisha" ]; then
    log "📁 Создание директории для логов nginx..."
    sudo mkdir -p /var/log/aisha
    sudo chown www-data:www-data /var/log/aisha
    sudo chmod 755 /var/log/aisha
fi

# 4. Остановка старых контейнеров (если есть)
log "🛑 Остановка существующих контейнеров..."
docker-compose -f docker-compose.prod.yml down --remove-orphans || true

# 5. Удаление старых образов (опционально)
if [ "$1" = "--rebuild" ]; then
    log "🔄 Удаление старых образов..."
    docker images | grep aisha | awk '{print $3}' | xargs docker rmi -f || true
fi

# 6. Сборка образов
log "🔨 Сборка Docker образов..."
docker-compose -f docker-compose.prod.yml build --no-cache

# 7. Запуск контейнеров
log "🚀 Запуск контейнеров..."
docker-compose -f docker-compose.prod.yml up -d

# 8. Ожидание запуска сервисов
log "⏱️  Ожидание запуска сервисов..."
sleep 30

# 9. Проверка состояния контейнеров
log "🔍 Проверка состояния контейнеров..."
if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    log_error "Контейнеры не запустились корректно"
    docker-compose -f docker-compose.prod.yml logs --tail=50
    exit 1
fi

# 10. Проверка health check
log "💊 Проверка health check..."
for i in {1..12}; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log_success "API сервер отвечает"
        break
    fi
    if [ $i -eq 12 ]; then
        log_error "API сервер не отвечает после 60 секунд"
        docker-compose -f docker-compose.prod.yml logs aisha-api --tail=20
        exit 1
    fi
    log "Ожидание API сервера... ($i/12)"
    sleep 5
done

# 11. Проверка nginx конфигурации
log "🌐 Проверка nginx конфигурации..."
if nginx -t 2>/dev/null; then
    log_success "Конфигурация nginx корректна"
    
    # 12. Перезагрузка nginx
    log "🔄 Перезагрузка nginx..."
    sudo systemctl reload nginx
    log_success "Nginx перезагружен"
else
    log_warning "Проблемы с конфигурацией nginx. Проверьте вручную."
fi

# 13. Создание/обновление systemd сервисов
log "🔧 Настройка systemd сервисов..."

# Создание systemd unit файла для Docker Compose
cat > /tmp/aisha-v2.service << EOF
[Unit]
Description=Aisha Bot v2 Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/aisha-backend
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/aisha-v2.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable aisha-v2.service

log_success "Systemd сервис настроен"

# 14. Финальная проверка
log "🔍 Финальная проверка системы..."
echo ""
echo "📊 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🌐 Проверка endpoints:"
if curl -s http://localhost:8000/health | grep -q "ok"; then
    log_success "✅ Health endpoint работает"
else
    log_warning "⚠️  Health endpoint не отвечает"
fi

if curl -k -s https://aibots.kz:8443/health | grep -q "ok"; then
    log_success "✅ HTTPS endpoint работает"
else
    log_warning "⚠️  HTTPS endpoint не отвечает"
fi

echo ""
log_success "🎉 Развертывание завершено!"
echo ""
echo "📋 Полезные команды:"
echo "  - Логи всех сервисов: docker-compose -f docker-compose.prod.yml logs -f"
echo "  - Логи бота: docker-compose -f docker-compose.prod.yml logs -f aisha-bot"
echo "  - Логи API: docker-compose -f docker-compose.prod.yml logs -f aisha-api"
echo "  - Статус: docker-compose -f docker-compose.prod.yml ps"
echo "  - Перезапуск: sudo systemctl restart aisha-v2"
echo "  - Остановка: docker-compose -f docker-compose.prod.yml down"
echo ""
echo "🔗 Endpoints:"
echo "  - Health check: https://aibots.kz:8443/health"
echo "  - Webhook: https://aibots.kz:8443/api/v1/avatar/status_update"
echo ""

log "📝 Логи сохраняются в /opt/aisha-backend/logs/ и /var/log/aisha/" 