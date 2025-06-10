#!/bin/bash

# ============================================================================
# Быстрые команды для разработки Aisha Bot
# Новая архитектура: webhook на продакшн, bot - локальная разработка
# ============================================================================

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

case "${1:-help}" in
    "dev-start")
        echo "🚀 Запуск локальной разработки..."
        docker-compose -f docker-compose.bot.dev.yml up -d
        echo "✅ Dev контейнеры запущены"
        echo "📊 Статус:"
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(dev|worker-dev)"
        ;;
    "dev-stop")
        echo "🛑 Остановка локальной разработки..."
        docker-compose -f docker-compose.bot.dev.yml down
        echo "✅ Dev контейнеры остановлены"
        ;;
    "dev-logs")
        echo "📋 Логи разработки:"
        docker-compose -f docker-compose.bot.dev.yml logs -f "${2:-aisha-bot-dev}"
        ;;
    "dev-rebuild")
        echo "🔨 Пересборка dev контейнеров..."
        docker-compose -f docker-compose.bot.dev.yml down
        docker-compose -f docker-compose.bot.dev.yml build --no-cache
        docker-compose -f docker-compose.bot.dev.yml up -d
        echo "✅ Пересборка завершена"
        ;;
    "dev-test")
        echo "🧪 Быстрый тест разработки..."
        docker-compose -f docker-compose.bot.dev.yml up -d
        sleep 15
        echo "📊 Статус контейнеров:"
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(dev|worker-dev)"
        echo ""
        echo "📋 Последние логи:"
        docker logs aisha-bot-dev --tail 10
        ;;
    "deploy")
        echo "🚀 Запуск полного деплоя через registry..."
        ./scripts/production/deploy-via-registry.sh
        ;;
    "webhook-status")
        echo "📊 Статус webhook на продакшн..."
        ./scripts/production/manage-webhook.sh status
        ;;
    "webhook-logs")
        echo "📋 Логи webhook на продакшн..."
        ./scripts/production/manage-webhook.sh logs "${2:-all}"
        ;;
    "prod-status")
        echo "📊 Статус продакшн сервера..."
        ssh aisha@192.168.0.10 "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'"
        ;;
    "prod-clean")
        echo "🧹 Очистка продакшн от bot контейнеров..."
        ./scripts/production/manage-webhook.sh remove-bot
        ;;
    "transcription-test")
        echo "🎙️ Тест транскрибации (локально)..."
        if docker ps | grep -q "aisha-bot-dev"; then
            echo "✅ Dev бот запущен"
            echo "📝 Отправьте голосовое сообщение боту и проверьте логи:"
            docker logs aisha-bot-dev --tail 20 -f
        else
            echo "❌ Dev бот не запущен. Запустите: $0 dev-start"
        fi
        ;;
    "build-push")
        echo "📦 Сборка и отправка в registry..."
        VERSION=$(date +%Y%m%d-%H%M%S)
        REGISTRY="192.168.0.4:5000"
        IMAGE="${REGISTRY}/aisha/bot:${VERSION}"
        LATEST="${REGISTRY}/aisha/bot:latest"
        
        echo "🔨 Сборка образа..."
        docker build -f docker/Dockerfile.bot -t $IMAGE -t $LATEST .
        
        echo "📤 Отправка в registry..."
        docker push $IMAGE
        docker push $LATEST
        
        echo "✅ Образ отправлен: $IMAGE"
        ;;
    "health-check")
        echo "🔍 Полная проверка здоровья системы..."
        echo ""
        echo "=== Локальная разработка ==="
        if docker ps | grep -q "aisha-bot-dev"; then
            echo "✅ Dev контейнеры запущены"
            docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(dev|worker-dev)"
        else
            echo "❌ Dev контейнеры не запущены"
        fi
        
        echo ""
        echo "=== Продакшн webhook ==="
        ./scripts/production/manage-webhook.sh health
        
        echo ""
        echo "=== Внешние сервисы ==="
        echo "🔍 PostgreSQL (192.168.0.4:5432)..."
        if nc -z 192.168.0.4 5432 2>/dev/null; then
            echo "✅ PostgreSQL доступен"
        else
            echo "❌ PostgreSQL недоступен"
        fi
        
        echo "🔍 Redis (192.168.0.3:6379)..."
        if nc -z 192.168.0.3 6379 2>/dev/null; then
            echo "✅ Redis доступен"
        else
            echo "❌ Redis недоступен"
        fi
        
        echo "🔍 MinIO (192.168.0.4:9000)..."
        if nc -z 192.168.0.4 9000 2>/dev/null; then
            echo "✅ MinIO доступен"
        else
            echo "❌ MinIO недоступен"
        fi
        
        echo "🔍 Registry (192.168.0.4:5000)..."
        if nc -z 192.168.0.4 5000 2>/dev/null; then
            echo "✅ Registry доступен"
        else
            echo "❌ Registry недоступен"
        fi
        ;;
    *)
        echo -e "${CYAN}🚀 Быстрые команды для разработки Aisha Bot${NC}"
        echo ""
        echo -e "${GREEN}=== Локальная разработка ===${NC}"
        echo "  dev-start       - Запустить локальную разработку"
        echo "  dev-stop        - Остановить разработку"
        echo "  dev-logs [srv]  - Показать логи (aisha-bot-dev или aisha-worker-dev)"
        echo "  dev-rebuild     - Пересобрать и запустить"
        echo "  dev-test        - Быстрый тест разработки"
        echo "  transcription-test - Тест транскрибации с логами"
        echo ""
        echo -e "${YELLOW}=== Деплой на продакшн ===${NC}"
        echo "  deploy          - Полный деплой через registry"
        echo "  build-push      - Только сборка и отправка в registry"
        echo ""
        echo -e "${BLUE}=== Управление продакшн ===${NC}"
        echo "  webhook-status  - Статус webhook сервисов"
        echo "  webhook-logs    - Логи webhook сервисов"
        echo "  prod-status     - Статус всех контейнеров на продакшн"
        echo "  prod-clean      - Удалить bot с продакшн (оставить только webhook)"
        echo ""
        echo -e "${RED}=== Диагностика ===${NC}"
        echo "  health-check    - Полная проверка здоровья системы"
        echo ""
        echo -e "${CYAN}Примеры использования:${NC}"
        echo "  $0 dev-start             # Начать разработку"
        echo "  $0 transcription-test    # Протестировать транскрибацию"
        echo "  $0 deploy               # Задеплоить на продакшн"
        echo "  $0 webhook-status       # Проверить webhook"
        echo "  $0 health-check         # Полная диагностика"
        echo ""
        echo -e "${YELLOW}🏗️ Новая архитектура:${NC}"
        echo "  📍 Продакшн (192.168.0.10): только webhook сервисы"
        echo "  💻 Локально: разработка и тестирование бота"
        echo "  📦 Registry (192.168.0.4:5000): деплой через Docker образы"
        ;;
esac 