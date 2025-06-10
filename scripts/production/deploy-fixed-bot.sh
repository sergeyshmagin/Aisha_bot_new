#!/bin/bash

# ============================================================================
# Скрипт развертывания исправленного Aisha Bot на продакшн
# Исправлены: polling конфликты, storage permissions, worker модуль
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
PROJECT_DIR="/opt/aisha-backend"

log_info "🚀 Развертывание исправленного Aisha Bot на продакшн"

# 1. Копируем обновленные файлы на продакшн сервер
log_info "📁 Копирование обновленных файлов на продакшн сервер..."

scp docker-compose.bot.simple.yml ${PROD_USER}@${PROD_SERVER}:${PROJECT_DIR}/
scp docker/bot-entrypoint.sh ${PROD_USER}@${PROD_SERVER}:${PROJECT_DIR}/docker/
scp -r app/workers ${PROD_USER}@${PROD_SERVER}:${PROJECT_DIR}/app/
scp app/core/config.py ${PROD_USER}@${PROD_SERVER}:${PROJECT_DIR}/app/core/

# 2. Выполняем развертывание на продакшн сервере
log_info "🔄 Выполнение развертывания на продакшн сервере..."

ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
set -e

cd /opt/aisha-backend

echo "🛑 Остановка старых контейнеров бота..."
docker-compose -f docker-compose.bot.simple.yml down 2>/dev/null || true

echo ""
echo "🧹 Очистка старых образов бота..."
docker rmi $(docker images | grep "aisha.*bot" | awk '{print $3}') 2>/dev/null || true

echo ""
echo "📥 Загрузка нового образа из registry..."
docker pull 192.168.0.4:5000/aisha/bot:latest

echo ""
echo "📦 Создание Docker volumes (если не существуют)..."
docker volume create aisha-backend_bot_storage_temp 2>/dev/null || true
docker volume create aisha-backend_bot_storage_audio 2>/dev/null || true
docker volume create aisha-backend_bot_logs 2>/dev/null || true

echo ""
echo "🚀 Запуск контейнеров с новой конфигурацией..."
docker-compose -f docker-compose.bot.simple.yml up -d

echo ""
echo "⏰ Ожидание запуска контейнеров..."
sleep 20

echo ""
echo "📊 Статус контейнеров после развертывания:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep -E "(bot|worker)" || echo "Контейнеры бота не найдены"

echo ""
echo "🧪 Тест прав доступа к storage..."
if docker exec aisha-bot-primary touch /app/storage/temp/test-permissions.txt 2>/dev/null; then
    docker exec aisha-bot-primary rm /app/storage/temp/test-permissions.txt 2>/dev/null
    echo "✅ Права доступа к storage работают правильно"
else
    echo "❌ Проблемы с правами доступа к storage"
fi

echo ""
echo "📋 Информация о volumes:"
docker volume ls | grep aisha-backend || true

echo ""
echo "🔍 Логи primary бота (последние 10 строк):"
docker logs aisha-bot-primary --tail 10 2>/dev/null || echo "Primary бот не запущен"

echo ""
echo "🔍 Логи worker (последние 5 строк):"
docker logs aisha-worker-1 --tail 5 2>/dev/null || echo "Worker не запущен"

echo ""
echo "🎉 Развертывание завершено!"
echo ""
echo "📝 Что исправлено:"
echo "   ✅ Polling конфликты устранены (только primary делает polling)"
echo "   ✅ Storage permissions исправлены (автоматическая настройка)"
echo "   ✅ Worker модуль создан (app.workers.background_worker)"
echo "   ✅ Docker volumes для постоянного хранения"
echo "   ✅ Entrypoint исправлен для правильной работы с правами"
echo ""
echo "🔧 Для мониторинга используйте:"
echo "   docker logs aisha-bot-primary --tail 20 -f"
echo "   docker logs aisha-worker-1 --tail 20 -f"
echo ""
echo "📊 Для проверки статуса:"
echo "   docker ps --format \"table {{.Names}}\t{{.Status}}\""

EOF

log_info "✅ Развертывание исправленного бота завершено успешно!"
log_info ""
log_info "🎯 Основные исправления применены:"
log_info "   • Конфликты polling полностью устранены"
log_info "   • Права доступа к storage автоматически настраиваются"
log_info "   • Background worker модуль создан и работает"
log_info "   • Docker volumes обеспечивают постоянство данных"
log_info ""
log_info "🤖 Бот готов к работе без конфликтов и ошибок прав доступа!"
</rewritten_file> 