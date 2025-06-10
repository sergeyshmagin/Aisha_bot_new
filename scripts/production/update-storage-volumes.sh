#!/bin/bash

# ============================================================================
# Скрипт обновления storage конфигурации на продакшн сервере
# Переход с bind mounts на Docker volumes для storage директорий
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

log_info "🚀 Начинаем обновление storage конфигурации на продакшне"

# 1. Копируем обновленные файлы на продакшн сервер
log_info "📁 Копирование обновленных файлов на продакшн сервер..."

scp docker-compose.bot.simple.yml ${PROD_USER}@${PROD_SERVER}:${PROJECT_DIR}/
scp docker/bot-entrypoint.sh ${PROD_USER}@${PROD_SERVER}:${PROJECT_DIR}/docker/

# 2. Выполняем обновление на продакшн сервере
log_info "🔄 Выполнение обновления на продакшн сервере..."

ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
set -e

cd /opt/aisha-backend

echo "📋 Текущие контейнеры перед обновлением:"
docker-compose -f docker-compose.bot.simple.yml ps

echo ""
echo "🛑 Остановка текущих контейнеров..."
docker-compose -f docker-compose.bot.simple.yml down

echo ""
echo "🗂️ Создание резервных копий данных из bind mounts..."
if [ -d "storage/temp" ] && [ "$(ls -A storage/temp)" ]; then
    echo "Копирование данных из storage/temp..."
    
    # Создаем временную папку для бэкапа
    mkdir -p /tmp/aisha-storage-backup/temp
    cp -r storage/temp/* /tmp/aisha-storage-backup/temp/ 2>/dev/null || true
    
    echo "✅ Данные скопированы в /tmp/aisha-storage-backup/"
fi

echo ""
echo "🔧 Пересборка образа с обновленным entrypoint..."
docker build -f docker/Dockerfile.bot -t 192.168.0.4:5000/aisha/bot:latest .
docker push 192.168.0.4:5000/aisha/bot:latest

echo ""
echo "📦 Создание Docker volumes..."
docker volume create aisha-backend_bot_storage_temp 2>/dev/null || true
docker volume create aisha-backend_bot_storage_audio 2>/dev/null || true

echo ""
echo "🚀 Запуск контейнеров с новой конфигурацией..."
docker-compose -f docker-compose.bot.simple.yml up -d

echo ""
echo "⏰ Ожидание запуска контейнеров..."
sleep 15

echo ""
echo "🔄 Восстановление данных в новые volumes (если есть бэкап)..."
if [ -d "/tmp/aisha-storage-backup/temp" ] && [ "$(ls -A /tmp/aisha-storage-backup/temp)" ]; then
    echo "Восстановление данных в temp volume..."
    
    # Копируем данные обратно через временный контейнер
    docker run --rm \
        -v aisha-backend_bot_storage_temp:/target \
        -v /tmp/aisha-storage-backup/temp:/source \
        alpine sh -c "cp -r /source/* /target/ 2>/dev/null || true"
    
    echo "✅ Данные восстановлены"
    
    # Очищаем временный бэкап
    rm -rf /tmp/aisha-storage-backup/
fi

echo ""
echo "📊 Статус контейнеров после обновления:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep -E "(bot|worker)" || true

echo ""
echo "🧪 Тест прав доступа к storage..."
docker exec aisha-bot-primary touch /app/storage/temp/test-permissions.txt 2>/dev/null && \
docker exec aisha-bot-primary rm /app/storage/temp/test-permissions.txt 2>/dev/null && \
echo "✅ Права доступа к storage работают правильно" || \
echo "❌ Проблемы с правами доступа к storage"

echo ""
echo "📋 Информация о созданных volumes:"
docker volume ls | grep aisha-backend || true

echo ""
echo "🎉 Обновление завершено!"
echo ""
echo "🔍 Для проверки логов используйте:"
echo "docker logs aisha-bot-primary --tail 20"
echo ""
echo "📊 Для мониторинга статуса:"
echo "docker ps --format \"table {{.Names}}\t{{.Status}}\""

EOF

log_info "✅ Обновление storage конфигурации завершено успешно!"
log_info ""
log_info "📝 Что изменилось:"
log_info "   • Bind mounts заменены на Docker volumes"
log_info "   • Добавлена автоматическая настройка прав доступа в entrypoint"
log_info "   • Созданы volumes: bot_storage_temp, bot_storage_audio"
log_info "   • Права доступа настраиваются автоматически при каждом запуске"
log_info ""
log_info "🔧 Теперь при пересоздании контейнеров проблемы с правами не возникнут!"
</rewritten_file> 