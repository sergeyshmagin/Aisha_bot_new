#!/bin/bash

# ============================================================================
# Скрипт управления Webhook сервисами на продакшн
# Управляет только webhook контейнерами, не трогает bot
# ============================================================================

set -e

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

PROD_SERVER="192.168.0.10"
PROD_USER="aisha"
PROD_DIR="/opt/aisha-backend"

# Функции управления
webhook_status() {
    log_info "📊 Проверка статуса webhook сервисов..."
    
    ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
echo "=== Статус Webhook контейнеров ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(webhook|nginx)" || echo "Webhook контейнеры не найдены"

echo ""
echo "=== Логи webhook-api-1 (последние 5 строк) ==="
docker logs aisha-webhook-api-1 --tail 5 2>/dev/null || echo "Контейнер не запущен"

echo ""  
echo "=== Логи webhook-api-2 (последние 5 строк) ==="
docker logs aisha-webhook-api-2 --tail 5 2>/dev/null || echo "Контейнер не запущен"

echo ""
echo "=== Проверка портов ==="
netstat -tlnp | grep -E ":80|:443|:8001|:8002" || echo "Порты не прослушиваются"
EOF
}

webhook_logs() {
    local service=${1:-"all"}
    
    if [ "$service" = "all" ]; then
        log_info "📋 Логи всех webhook сервисов..."
        ssh ${PROD_USER}@${PROD_SERVER} "cd ${PROD_DIR} && docker-compose -f docker-compose.webhook.prod.yml logs -f"
    else
        log_info "📋 Логи сервиса: $service"
        ssh ${PROD_USER}@${PROD_SERVER} "cd ${PROD_DIR} && docker-compose -f docker-compose.webhook.prod.yml logs -f $service"
    fi
}

webhook_restart() {
    log_info "🔄 Перезапуск webhook сервисов..."
    
    ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
cd /opt/aisha-backend

echo "🛑 Остановка webhook сервисов..."
docker-compose -f docker-compose.webhook.prod.yml down

echo "🚀 Запуск webhook сервисов..."
docker-compose -f docker-compose.webhook.prod.yml up -d

echo "⏱️ Ожидание запуска (15 секунд)..."
sleep 15

echo "📊 Новый статус:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(webhook|nginx)"
EOF
}

webhook_update() {
    log_info "📥 Обновление webhook образов..."
    
    ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
cd /opt/aisha-backend

echo "📥 Загрузка новых образов..."
docker-compose -f docker-compose.webhook.prod.yml pull

echo "🔄 Перезапуск с новыми образами..."
docker-compose -f docker-compose.webhook.prod.yml up -d

echo "⏱️ Ожидание запуска (20 секунд)..."
sleep 20

echo "✅ Обновление завершено"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep -E "(webhook|nginx)"
EOF
}

webhook_stop() {
    log_warn "🛑 Остановка всех webhook сервисов..."
    
    ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
cd /opt/aisha-backend
docker-compose -f docker-compose.webhook.prod.yml down
echo "✅ Webhook сервисы остановлены"
EOF
}

webhook_start() {
    log_info "🚀 Запуск webhook сервисов..."
    
    ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
cd /opt/aisha-backend
docker-compose -f docker-compose.webhook.prod.yml up -d
echo "✅ Webhook сервисы запущены"
EOF
}

webhook_health() {
    log_info "🔍 Проверка здоровья webhook сервисов..."
    
    ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
echo "=== Health Check ==="

# Проверяем webhook-api-1
echo "🔍 Проверка webhook-api-1..."
if curl -s -f http://localhost:8001/health > /dev/null; then
    echo "✅ webhook-api-1: OK"
else
    echo "❌ webhook-api-1: FAILED"
fi

# Проверяем webhook-api-2  
echo "🔍 Проверка webhook-api-2..."
if curl -s -f http://localhost:8002/health > /dev/null; then
    echo "✅ webhook-api-2: OK"
else
    echo "❌ webhook-api-2: FAILED"
fi

# Проверяем nginx
echo "🔍 Проверка nginx..."
if curl -s -f http://localhost/health > /dev/null; then
    echo "✅ nginx: OK"
else
    echo "❌ nginx: FAILED"
fi

echo ""
echo "=== Порты ==="
netstat -tlnp | grep -E ":80|:8001|:8002" | head -10
EOF
}

bot_status_for_webhook() {
    log_info "🤖 Проверка совместимости с bot сервисами..."
    
    ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
echo "=== Bot контейнеры (должны быть остановлены) ==="
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(bot|worker)" || echo "✅ Bot контейнеры остановлены"

echo ""
echo "=== Все активные контейнеры ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"

echo ""
echo "=== Сетевые подключения ==="
docker network ls | grep -E "(aisha|webhook)"
EOF
}

# Удаляем bot контейнеры с продакшн (подготовка для webhook-only режима)
remove_bot_from_prod() {
    log_warn "🗑️ Удаление bot контейнеров с продакшн..."
    
    read -p "$(echo -e ${YELLOW}Вы уверены что хотите удалить bot с продакшн? [y/N]: ${NC})" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Отменено пользователем"
        return 0
    fi
    
    ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
cd /opt/aisha-backend

echo "🛑 Остановка bot контейнеров..."
docker-compose -f docker-compose.bot.simple.yml down 2>/dev/null || true

echo "🗑️ Удаление bot контейнеров..."
docker rm -f aisha-bot-primary aisha-worker-1 2>/dev/null || true

echo "🧹 Очистка bot образов..."
docker image rm 192.168.0.4:5000/aisha/bot:latest 2>/dev/null || true

echo "✅ Bot контейнеры удалены с продакшн"
echo "📊 Оставшиеся контейнеры:"
docker ps --format "table {{.Names}}\t{{.Status}}"
EOF
}

# Показ справки
show_help() {
    echo "🚀 Управление Webhook сервисами Aisha"
    echo ""
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды управления webhook:"
    echo "  status      - Показать статус webhook сервисов"
    echo "  logs [all]  - Показать логи (all - всех, или имя сервиса)"
    echo "  restart     - Перезапустить webhook сервисы"
    echo "  update      - Обновить образы и перезапустить"
    echo "  stop        - Остановить все webhook сервисы"
    echo "  start       - Запустить webhook сервисы"
    echo "  health      - Проверить здоровье сервисов"
    echo ""
    echo "Команды совместимости:"
    echo "  bot-status  - Проверить статус bot (должен быть выключен)"
    echo "  remove-bot  - Удалить bot контейнеры с продакшн"
    echo ""
    echo "Примеры:"
    echo "  $0 status                # Статус webhook"
    echo "  $0 logs webhook-api-1    # Логи конкретного сервиса"
    echo "  $0 health               # Health check"
    echo "  $0 remove-bot           # Подготовка к webhook-only режиму"
}

# Основная логика
case "${1:-help}" in
    "status")
        webhook_status
        ;;
    "logs")
        webhook_logs "$2"
        ;;
    "restart")
        webhook_restart
        ;;
    "update")
        webhook_update
        ;;
    "stop")
        webhook_stop
        ;;
    "start")
        webhook_start
        ;;
    "health")
        webhook_health
        ;;
    "bot-status")
        bot_status_for_webhook
        ;;
    "remove-bot")
        remove_bot_from_prod
        ;;
    *)
        show_help
        ;;
esac 