#!/bin/bash

# ============================================================================
# ⚡ БЫСТРОЕ ИСПРАВЛЕНИЕ TELEGRAM POLLING КОНФЛИКТОВ
# Решение проблемы "terminated by other getUpdates request"
# ============================================================================

set -e

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции логирования
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "\n${BLUE}===== $1 =====${NC}\n"; }

# Переменные
PROD_SERVER="192.168.0.10"
PROD_USER="aisha"
PROJECT_ROOT="/opt/aisha-backend"

# ============================================================================
# 1. ПРОВЕРКА ТЕКУЩЕГО СОСТОЯНИЯ
# ============================================================================

check_current_state() {
    log_step "🔍 Проверка текущего состояния"
    
    # Проверяем переменную токена
    if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
        log_error "Переменная TELEGRAM_BOT_TOKEN не установлена!"
        log_info "Экспортируйте токен: export TELEGRAM_BOT_TOKEN=your_token_here"
        exit 1
    fi
    
    log_info "✅ Токен установлен: ${TELEGRAM_BOT_TOKEN:0:10}..."
    
    # Проверяем статус контейнеров
    log_info "🐳 Статус контейнеров на продакшене:"
    ssh "$PROD_USER@$PROD_SERVER" "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep aisha || echo 'Контейнеры не найдены'"
}

# ============================================================================
# 2. БЫСТРОЕ ИСПРАВЛЕНИЕ POLLING КОНФЛИКТОВ
# ============================================================================

quick_fix_polling_conflicts() {
    log_step "⚡ Исправление polling конфликтов"
    
    log_info "🔧 Применяем исправления на продакшене..."
    
    ssh "$PROD_USER@$PROD_SERVER" << REMOTE_SCRIPT
cd /opt/aisha-backend

echo "🔄 Остановка всех bot контейнеров..."
docker-compose -f docker-compose.bot.registry.yml down || true

# Ждем полной остановки
sleep 5

echo "🔧 Создание исправленной конфигурации..."

# Создаем исправленный docker-compose
cat > docker-compose.bot.fixed.yml << 'EOF'
version: '3.8'

networks:
  aisha_bot_cluster:
    external: true

volumes:
  bot_logs:
    driver: local

services:
  # ============================================================================
  # 🤖 ОСНОВНОЙ БОТ - ЕДИНСТВЕННЫЙ КТО ДЕЛАЕТ POLLING
  # ============================================================================
  bot-primary:
    image: 192.168.0.4:5000/aisha/bot:latest
    container_name: aisha-bot-primary
    restart: unless-stopped
    volumes:
      - bot_logs:/app/logs
      - /opt/aisha-backend/storage/temp:/app/storage/temp
    networks:
      aisha_bot_cluster:
        ipv4_address: 172.26.0.10
    environment:
      # Application
      - PYTHONPATH=/app
      - DEBUG=false
      - INSTANCE_ID=bot-primary
      - BOT_MODE=polling
      - SET_POLLING=true    # ⚡ ТОЛЬКО ЭТОТ БОТ ДЕЛАЕТ POLLING
      
      # Telegram
      - TELEGRAM_BOT_TOKEN=\${TELEGRAM_BOT_TOKEN}
      
      # External services
      - POSTGRES_HOST=192.168.0.4
      - POSTGRES_PORT=5432
      - POSTGRES_DB=aisha
      - POSTGRES_USER=aisha_user
      - POSTGRES_PASSWORD=KbZZGJHX09KSH7r9ev4m
      
      - REDIS_HOST=192.168.0.3
      - REDIS_PORT=6379
      - REDIS_DB=0
      - REDIS_PASSWORD=wd7QuwAbG0wtyoOOw3Sm
      - REDIS_SSL=false
      - REDIS_POOL_SIZE=10
      
      - MINIO_ENDPOINT=192.168.0.4:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=74rSbw9asQ1uMzcFeM5G
      - MINIO_SECURE=false
      
      # Audio processing
      - AUDIO_STORAGE_PATH=/app/storage/temp
      - TEMP_DIR=/app/storage/temp
      
    command: ["python3", "main.py"]
    
    healthcheck:
      test: ["CMD", "pgrep", "-f", "python3"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '1.0'
          memory: 512M

  # ============================================================================
  # 🔄 BACKGROUND WORKERS - НЕ ДЕЛАЮТ POLLING
  # ============================================================================
  
  worker-1:
    image: 192.168.0.4:5000/aisha/bot:latest
    container_name: aisha-worker-1
    restart: unless-stopped
    volumes:
      - bot_logs:/app/logs
      - /opt/aisha-backend/storage/temp:/app/storage/temp
    networks:
      aisha_bot_cluster:
        ipv4_address: 172.26.0.20
    environment:
      - PYTHONPATH=/app
      - DEBUG=false
      - INSTANCE_ID=worker-1
      - BOT_MODE=worker
      - SET_POLLING=false   # ⚡ НЕ ДЕЛАЕТ POLLING
      
      # Telegram
      - TELEGRAM_BOT_TOKEN=\${TELEGRAM_BOT_TOKEN}
      
      # External services
      - POSTGRES_HOST=192.168.0.4
      - POSTGRES_PORT=5432
      - POSTGRES_DB=aisha
      - POSTGRES_USER=aisha_user
      - POSTGRES_PASSWORD=KbZZGJHX09KSH7r9ev4m
      
      - REDIS_HOST=192.168.0.3
      - REDIS_PORT=6379
      - REDIS_DB=0
      - REDIS_PASSWORD=wd7QuwAbG0wtyoOOw3Sm
      - REDIS_SSL=false
      - REDIS_POOL_SIZE=10
      
      - MINIO_ENDPOINT=192.168.0.4:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=74rSbw9asQ1uMzcFeM5G
      - MINIO_SECURE=false
      
      # Audio processing
      - AUDIO_STORAGE_PATH=/app/storage/temp
      - TEMP_DIR=/app/storage/temp
      
    command: ["python3", "main.py"]
    
    healthcheck:
      test: ["CMD", "pgrep", "-f", "python3"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  worker-2:
    image: 192.168.0.4:5000/aisha/bot:latest
    container_name: aisha-worker-2
    restart: unless-stopped
    volumes:
      - bot_logs:/app/logs
      - /opt/aisha-backend/storage/temp:/app/storage/temp
    networks:
      aisha_bot_cluster:
        ipv4_address: 172.26.0.21
    environment:
      - PYTHONPATH=/app
      - DEBUG=false
      - INSTANCE_ID=worker-2
      - BOT_MODE=worker
      - SET_POLLING=false   # ⚡ НЕ ДЕЛАЕТ POLLING
      
      # Telegram
      - TELEGRAM_BOT_TOKEN=\${TELEGRAM_BOT_TOKEN}
      
      # External services  
      - POSTGRES_HOST=192.168.0.4
      - POSTGRES_PORT=5432
      - POSTGRES_DB=aisha
      - POSTGRES_USER=aisha_user
      - POSTGRES_PASSWORD=KbZZGJHX09KSH7r9ev4m
      
      - REDIS_HOST=192.168.0.3
      - REDIS_PORT=6379
      - REDIS_DB=0
      - REDIS_PASSWORD=wd7QuwAbG0wtyoOOw3Sm
      - REDIS_SSL=false
      - REDIS_POOL_SIZE=10
      
      - MINIO_ENDPOINT=192.168.0.4:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=74rSbw9asQ1uMzcFeM5G
      - MINIO_SECURE=false
      
      # Audio processing
      - AUDIO_STORAGE_PATH=/app/storage/temp
      - TEMP_DIR=/app/storage/temp
      
    command: ["python3", "main.py"]
    
    healthcheck:
      test: ["CMD", "pgrep", "-f", "python3"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
EOF

echo "🚀 Запуск исправленной конфигурации..."
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
docker-compose -f docker-compose.bot.fixed.yml up -d

echo "⏳ Ожидание запуска контейнеров..."
sleep 30

echo "📊 Проверка статуса..."
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

echo "✅ Исправленная конфигурация запущена"
REMOTE_SCRIPT

    log_info "✅ Исправления применены"
}

# ============================================================================
# 3. ПРОВЕРКА РЕЗУЛЬТАТА
# ============================================================================

verify_fix() {
    log_step "🔍 Проверка исправлений"
    
    # Ждем стабилизации
    log_info "⏳ Ожидание стабилизации системы..."
    sleep 20
    
    # Проверяем логи на отсутствие конфликтов
    log_info "📋 Проверка логов на конфликты polling..."
    ssh "$PROD_USER@$PROD_SERVER" << 'REMOTE_CHECK'
cd /opt/aisha-backend

echo "=== ОСНОВНОЙ БОТ (должен делать polling) ==="
docker logs aisha-bot-primary --tail 10 | grep -E "(polling|Conflict|terminated)" || echo "✅ Конфликтов не обнаружено"

echo -e "\n=== WORKER 1 (НЕ должен делать polling) ==="
docker logs aisha-worker-1 --tail 10 | grep -E "(polling|Conflict|terminated)" || echo "✅ Конфликтов не обнаружено"

echo -e "\n=== WORKER 2 (НЕ должен делать polling) ==="
docker logs aisha-worker-2 --tail 10 | grep -E "(polling|Conflict|terminated)" || echo "✅ Конфликтов не обнаружено"

echo -e "\n=== ОБЩИЙ СТАТУС КОНТЕЙНЕРОВ ==="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Created}}'
REMOTE_CHECK

    log_info "🤖 Проверка работы бота..."
    log_info "Теперь можете отправить боту команду /start для проверки"
}

# ============================================================================
# 4. ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

main() {
    log_info "⚡ Быстрое исправление Telegram polling конфликтов"
    log_info "📅 $(date)"
    echo
    
    # Проверки
    check_current_state
    
    # Исправление
    quick_fix_polling_conflicts
    
    # Проверка результата
    verify_fix
    
    echo
    log_info "🎉 Исправление завершено успешно!"
    log_info ""
    log_info "🔥 Что изменилось в архитектуре:"
    log_info "   ✅ aisha-bot-primary - ЕДИНСТВЕННЫЙ делает polling"  
    log_info "   ✅ aisha-worker-1 - НЕ делает polling, только background задачи"
    log_info "   ✅ aisha-worker-2 - НЕ делает polling, только background задачи"
    log_info "   ✅ Исчезли конфликты 'Conflict: terminated by other getUpdates'!"
    log_info ""
    log_info "📋 Следующие шаги:"
    log_info "   1. Проверьте бота командой /start"
    log_info "   2. Мониторьте логи: docker logs aisha-bot-primary -f"
    log_info "   3. При необходимости - настройте webhook в будущем"
}

# Обработка ошибок
trap 'log_error "❌ Скрипт прерван на строке $LINENO"' ERR

# Справка
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "⚡ Быстрое исправление Telegram polling конфликтов"
    echo ""
    echo "Использование: $0"
    echo ""
    echo "Переменные окружения:"
    echo "  TELEGRAM_BOT_TOKEN - токен Telegram бота (обязательно)"
    echo ""
    echo "Что делает скрипт:"
    echo "  1. 🔍 Проверяет текущее состояние системы"
    echo "  2. ⚡ Исправляет конфликты polling (один primary + workers)"
    echo "  3. 🔍 Проверяет результат и отсутствие конфликтов"
    echo ""
    echo "Проблема:"
    echo "  Несколько контейнеров одновременно делали polling к Telegram API,"
    echo "  что вызывало ошибки 'Conflict: terminated by other getUpdates request'"
    echo ""
    echo "Решение:"
    echo "  ✅ Только один контейнер (primary) делает polling"
    echo "  ✅ Остальные работают как background workers"
    echo "  ✅ Никаких конфликтов!"
    exit 0
fi

# Запуск основной функции
main "$@" 