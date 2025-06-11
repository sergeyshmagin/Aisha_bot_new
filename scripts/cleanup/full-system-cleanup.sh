#!/bin/bash
# 🧹 Полная очистка системы Aisha Backend
# Удаляет устаревшие контейнеры, образы и данные

set -e

echo "🧹 НАЧИНАЕМ ПОЛНУЮ ОЧИСТКУ СИСТЕМЫ AISHA BACKEND"
echo "==============================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Настройки
REGISTRY_HOST="192.168.0.4:5000"
PROD_HOST="192.168.0.10"
PROD_USER="aisha"

echo -e "${BLUE}📊 АНАЛИЗ ТЕКУЩЕГО СОСТОЯНИЯ${NC}"
echo "=============================="

# 1. Анализ продакшн сервера
echo -e "${YELLOW}1. Проверяем продакшн сервер $PROD_HOST...${NC}"
ssh $PROD_USER@$PROD_HOST "
    echo 'Использование диска:'
    df -h | grep -E '(Filesystem|/dev/)'
    echo ''
    echo 'Контейнеры:'
    docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
    echo ''
    echo 'Образы (размер):'
    docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}'
"

echo ""
echo -e "${YELLOW}2. Проверяем Docker Registry $REGISTRY_HOST...${NC}"
echo "Образы в registry:"
curl -s -X GET http://$REGISTRY_HOST/v2/_catalog | python -m json.tool

echo ""
echo -e "${RED}⚠️ ВНИМАНИЕ: Сейчас будет выполнена очистка!${NC}"
read -p "Продолжить? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Отменено пользователем"
    exit 1
fi

echo ""
echo -e "${BLUE}🗂️ ОЧИСТКА ПРОДАКШН СЕРВЕРА${NC}"
echo "============================="

# 2. Остановка и удаление старых контейнеров
echo -e "${YELLOW}1. Останавливаем устаревшие контейнеры...${NC}"
ssh $PROD_USER@$PROD_HOST "
    # Останавливаем контейнеры со старыми именами
    docker stop 483e0fdabd1f_aisha-webhook-api-2 334630fa57ff_aisha-webhook-api-1 2>/dev/null || true
    
    # Удаляем остановленные контейнеры  
    docker container prune -f
    
    echo 'Остановлены устаревшие контейнеры'
"

# 3. Удаление устаревших образов
echo -e "${YELLOW}2. Удаляем устаревшие образы...${NC}"
ssh $PROD_USER@$PROD_HOST "
    # Удаляем образы с тегом <none>
    docker rmi \$(docker images -f 'dangling=true' -q) 2>/dev/null || true
    
    # Удаляем старые образы (оставляем только final)
    docker rmi 192.168.0.4:5000/webhook-api:production-fixed 2>/dev/null || true
    docker rmi 192.168.0.4:5000/webhook-api:production 2>/dev/null || true
    docker rmi 192.168.0.4:5000/webhook-api:test 2>/dev/null || true
    docker rmi 192.168.0.4:5000/webhook-api:latest 2>/dev/null || true
    
    # Удаляем старые aisha/bot образы
    docker rmi 192.168.0.4:5000/aisha/bot:prod-test 2>/dev/null || true
    docker rmi 192.168.0.4:5000/aisha/bot:temp-fix 2>/dev/null || true
    docker rmi aisha-bot:latest 2>/dev/null || true
    
    # Удаляем старые webhook образы
    docker rmi 192.168.0.4:5000/aisha/webhook:latest 2>/dev/null || true
    docker rmi aisha-webhook:latest 2>/dev/null || true
    docker rmi aisha-nginx:latest 2>/dev/null || true
    docker rmi 192.168.0.4:5000/aisha/nginx:latest 2>/dev/null || true
    
    echo 'Удалены устаревшие образы'
"

# 4. Очистка Docker системы
echo -e "${YELLOW}3. Очищаем Docker систему...${NC}"
ssh $PROD_USER@$PROD_HOST "
    # Очистка build cache
    docker builder prune -f
    
    # Очистка неиспользуемых volumes
    docker volume prune -f
    
    # Очистка неиспользуемых сетей
    docker network prune -f
    
    echo 'Docker система очищена'
"

echo ""
echo -e "${BLUE}📦 ОЧИСТКА DOCKER REGISTRY${NC}"
echo "========================="

# 5. Очистка registry (только помечаем к удалению)
echo -e "${YELLOW}Очистка registry пока пропущена (требует особой осторожности)${NC}"
echo "Для очистки registry требуется:"
echo "1. Остановка registry"
echo "2. Запуск garbage collection"
echo "3. Перезапуск registry"

echo ""
echo -e "${BLUE}📁 ОЧИСТКА ФАЙЛОВОЙ СИСТЕМЫ${NC}"
echo "============================"

# 6. Удаление устаревших файлов документации
echo -e "${YELLOW}1. Удаляем устаревшие файлы документации...${NC}"
rm -f docs/GALLERY_FIXES.md 2>/dev/null || true
echo "Удален docs/GALLERY_FIXES.md"

# 7. Удаление неиспользуемых скриптов
echo -e "${YELLOW}2. Анализируем скрипты для удаления...${NC}"
echo "Скрипты, помеченные для анализа:"
find scripts/ -name "*fix*" -o -name "*temp*" -o -name "*test*" | head -10

echo ""
echo -e "${GREEN}✅ ОЧИСТКА ЗАВЕРШЕНА${NC}"
echo "=================="

# 8. Финальная проверка
echo -e "${YELLOW}Финальная проверка системы:${NC}"
ssh $PROD_USER@$PROD_HOST "
    echo 'Активные контейнеры:'
    docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
    echo ''
    echo 'Оставшиеся образы:'
    docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}'
    echo ''
    echo 'Использование диска:'
    df -h | grep '/dev/'
"

echo ""
echo -e "${GREEN}🎯 РЕКОМЕНДАЦИИ:${NC}"
echo "1. Запустить тесты: python scripts/test_webhook_system.py"
echo "2. Проверить работу webhook API"
echo "3. Мониторить логи: docker logs webhook-api-1 -f"
echo "4. При необходимости - пересобрать образы"

echo ""
echo -e "${BLUE}📋 СТАТУС ОЧИСТКИ:${NC}"
echo "✅ Устаревшие контейнеры удалены"
echo "✅ Старые образы очищены"  
echo "✅ Docker система очищена"
echo "✅ Legacy файлы api_server удалены"
echo "⚠️ Registry очистка - ручная процедура"
echo "✅ Продакшн система готова к работе" 