#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 ДЕПЛОЙ ИСПРАВЛЕНИЙ ТРАНСКРИБАЦИИ И POLLING КОНФЛИКТОВ
# ═══════════════════════════════════════════════════════════════════════════════
# Исправления:
# 1. Добавлен ffmpeg в Docker образ
# 2. Исправлен путь storage в audio service 
# 3. Добавлен SET_POLLING для предотвращения конфликтов
# 4. Standby бот не делает polling
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Конфигурация
PROD_SERVER="192.168.0.10"
PROD_USER="aisha"
REGISTRY_SERVER="192.168.0.4"
REGISTRY_PORT="5000"
PROJECT_ROOT="/opt/aisha-backend"

# Логирование
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

# Проверка токена
check_telegram_token() {
    if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
        log_error "Переменная TELEGRAM_BOT_TOKEN не установлена!"
        log_info "Экспортируйте токен: export TELEGRAM_BOT_TOKEN=your_token_here"
        exit 1
    fi
    
    # Проверка валидности токена
    if ! curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" | grep -q '"ok":true'; then
        log_error "Токен Telegram недействителен!"
        exit 1
    fi
    
    log_info "✅ Токен Telegram валидный"
}

# Сборка исправленных образов
build_fixed_images() {
    log_step "🔨 Сборка исправленных образов..."
    
    # Bot с ffmpeg и правильной логикой polling
    log_info "Сборка исправленного Bot образа (с ffmpeg + SET_POLLING)..."
    docker build -f docker/Dockerfile.bot -t localhost:${REGISTRY_PORT}/aisha-bot:fixed .
    
    log_info "✅ Исправленные образы собраны"
}

# Отправка образов
push_images() {
    log_step "📤 Отправка исправленных образов..."
    
    docker push localhost:${REGISTRY_PORT}/aisha-bot:fixed || {
        log_error "Ошибка отправки bot образа"
        exit 1
    }
    
    log_info "✅ Образы отправлены"
}

# Исправленный деплой
deploy_fixes() {
    log_step "🚀 Деплой исправлений на продакшн..."
    
    ssh ${PROD_USER}@${PROD_SERVER} "
        cd ${PROJECT_ROOT}
        
        echo '🔄 Получение исправленных образов...'
        docker pull localhost:${REGISTRY_PORT}/aisha-bot:fixed
        
        echo '⏹️ Остановка ботов...'
        export TELEGRAM_BOT_TOKEN='${TELEGRAM_BOT_TOKEN}'
        docker-compose -f docker-compose.bot.registry.yml down || true
        
        echo '🧹 Очистка старых контейнеров...'
        docker system prune -f
        
        echo '🏷️ Перетегивание исправленного образа...'
        docker tag localhost:${REGISTRY_PORT}/aisha-bot:fixed localhost:${REGISTRY_PORT}/aisha-bot:latest
        
        echo '🤖 Запуск исправленного Bot кластера...'
        docker-compose -f docker-compose.bot.registry.yml up -d
        
        echo '⏳ Ожидание запуска...'
        sleep 30
        
        echo '📊 Проверка статуса...'
        docker ps --filter 'name=aisha-bot' --format 'table {{.Names}}\\\t{{.Status}}\\\t{{.Command}}'
    " || {
        log_error "Ошибка деплоя исправлений"
        exit 1
    }
}

# Проверка исправлений
check_fixes() {
    log_step "🔍 Проверка исправлений..."
    
    ssh ${PROD_USER}@${PROD_SERVER} "
        cd ${PROJECT_ROOT}
        
        echo '=== ПРОВЕРКА POLLING КОНФЛИКТОВ ==='
        echo 'Основной бот (должен делать polling):'
        docker logs aisha-bot-polling-1 --tail 5 | grep -E '(polling|SET_POLLING)' || echo 'Нет логов'
        
        echo
        echo 'Standby бот (НЕ должен делать polling):'
        docker logs aisha-bot-polling-2 --tail 5 | grep -E '(polling|standby|SET_POLLING)' || echo 'Нет логов'
        
        echo
        echo '=== ПРОВЕРКА FFMPEG ==='
        echo 'Проверка наличия ffmpeg в контейнере:'
        docker exec aisha-bot-polling-1 which ffmpeg || echo 'ffmpeg не найден'
        
        echo
        echo '=== ПРОВЕРКА STORAGE ДИРЕКТОРИИ ==='
        echo 'Проверка /app/storage/temp:'
        docker exec aisha-bot-polling-1 ls -la /app/storage/ || echo 'Директория недоступна'
        
        echo
        echo '=== ПРОВЕРКА НА КОНФЛИКТЫ TELEGRAM ==='
        conflict_count=\$(docker logs aisha-bot-polling-1 --since 2m 2>&1 | grep -i -c 'conflict.*getUpdates' || echo 0)
        if [[ \$conflict_count -eq 0 ]]; then
            echo '✅ ОТЛИЧНО: Нет конфликтов Telegram за последние 2 минуты'
        else
            echo '❌ ПРОБЛЕМА: Найдены конфликты Telegram (\$conflict_count)'
        fi
    "
}

# Тестирование транскрибации
test_transcription() {
    log_step "🎤 Тестирование транскрибации..."
    
    log_info "Для тестирования транскрибации:"
    echo "1. 🎤 Отправьте голосовое сообщение боту в Telegram"
    echo "2. 📝 Проверьте обработку в реальном времени:"
    echo "   ssh aisha@192.168.0.10 'docker logs aisha-bot-polling-1 --follow | grep -E \"(audio|transcript|ffmpeg)\"'"
    echo ""
    log_info "Ожидаемые улучшения:"
    echo "✅ Нет ошибок Permission denied"
    echo "✅ ffprobe доступен"
    echo "✅ Успешная обработка аудио"
    echo "✅ Транскрипция работает"
}

# Мониторинг после исправлений
monitor_after_fixes() {
    log_step "📊 Мониторинг после исправлений..."
    
    ssh ${PROD_USER}@${PROD_SERVER} "
        cd ${PROJECT_ROOT}
        
        echo '📈 Статистика за последние 5 минут:'
        
        # Подсчет различных метрик
        handled_count=\$(docker logs aisha-bot-polling-1 --since 5m 2>&1 | grep -c 'is handled' || echo 0)
        error_count=\$(docker logs aisha-bot-polling-1 --since 5m 2>&1 | grep -c 'ERROR' || echo 0)
        conflict_count=\$(docker logs aisha-bot-polling-1 --since 5m 2>&1 | grep -i -c 'conflict.*getUpdates' || echo 0)
        audio_count=\$(docker logs aisha-bot-polling-1 --since 5m 2>&1 | grep -c 'audio.*processing' || echo 0)
        ffmpeg_count=\$(docker logs aisha-bot-polling-1 --since 5m 2>&1 | grep -c 'ffmpeg' || echo 0)
        
        echo '   • Обработанные сообщения: '\$handled_count
        echo '   • Ошибки: '\$error_count
        echo '   • Конфликты polling: '\$conflict_count
        echo '   • Обработка аудио: '\$audio_count
        echo '   • Использование ffmpeg: '\$ffmpeg_count
        
        echo
        echo '🎯 РЕЗУЛЬТАТ ИСПРАВЛЕНИЙ:'
        if [[ \$conflict_count -eq 0 ]]; then
            echo '✅ ИСПРАВЛЕНО: Конфликты polling устранены'
        else
            echo '❌ НЕ ИСПРАВЛЕНО: Все еще есть конфликты polling'
        fi
        
        if [[ \$error_count -lt 10 ]]; then
            echo '✅ ХОРОШО: Мало ошибок (менее 10 за 5 мин)'
        else
            echo '⚠️ ВНИМАНИЕ: Много ошибок (\$error_count за 5 мин)'
        fi
        
        if [[ \$handled_count -gt 0 ]]; then
            echo '✅ РАБОТАЕТ: Бот обрабатывает сообщения'
        else
            echo '⚠️ ПРОВЕРИТЬ: Нет обработанных сообщений за 5 минут'
        fi
    "
}

# Создание скрипта быстрой диагностики
create_quick_debug() {
    log_step "🛠️ Создание скрипта быстрой диагностики..."
    
    ssh ${PROD_USER}@${PROD_SERVER} "
        cat > /tmp/quick-debug.sh << 'EOF'
#!/bin/bash
echo '🔍 БЫСТРАЯ ДИАГНОСТИКА AISHA BOT'
echo '================================'

echo '📦 Статус контейнеров:'
docker ps --filter 'name=aisha-bot' --format 'table {{.Names}}\\\t{{.Status}}'

echo
echo '🤖 Основной бот (последние 3 строки):'
docker logs aisha-bot-polling-1 --tail 3

echo
echo '💤 Standby бот (последние 3 строки):'
docker logs aisha-bot-polling-2 --tail 3 2>/dev/null || echo 'Не запущен'

echo
echo '🎤 Проверка транскрибации (поиск аудио активности):'
docker logs aisha-bot-polling-1 --since 10m | grep -i audio | tail -3 || echo 'Нет активности'

echo
echo '⚡ Конфликты polling (последние 10 минут):'
conflict_count=\\\$(docker logs aisha-bot-polling-1 --since 10m 2>&1 | grep -i -c 'conflict.*getUpdates' || echo 0)
echo \"Найдено конфликтов: \\\$conflict_count\"

echo '================================'
echo '✅ Диагностика завершена'
EOF
        chmod +x /tmp/quick-debug.sh
        echo 'Создан /tmp/quick-debug.sh для быстрой диагностики'
    "
}

# Основная функция
main() {
    log_info "🔧 Деплой исправлений транскрибации и polling конфликтов"
    log_info "📍 Сервер: ${PROD_USER}@${PROD_SERVER}"
    log_info "🕒 $(date)"
    echo
    
    # Проверки
    check_telegram_token
    
    # Сборка и деплой исправлений
    build_fixed_images
    push_images
    deploy_fixes
    
    # Проверка и тестирование
    check_fixes
    echo
    monitor_after_fixes
    echo
    test_transcription
    echo
    create_quick_debug
    
    echo
    log_info "🎉 Деплой исправлений завершен!"
    log_info "📊 Для мониторинга: ./scripts/utils/debug-transcription.sh"
    log_info "🚀 Для быстрой проверки: ssh aisha@192.168.0.10 '/tmp/quick-debug.sh'"
}

# Обработка ошибок
trap 'log_error "❌ Скрипт прерван на строке $LINENO"' ERR

# Справка
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Использование: $0"
    echo
    echo "Исправления:"
    echo "  🔧 ffmpeg добавлен в Docker образ"
    echo "  📁 Исправлен путь /app/storage/temp"  
    echo "  📡 SET_POLLING=true только для основного бота"
    echo "  💤 SET_POLLING=false для standby бота"
    echo
    echo "Переменные окружения:"
    echo "  TELEGRAM_BOT_TOKEN  - обязательно"
    echo
    echo "Пример:"
    echo "  export TELEGRAM_BOT_TOKEN=8063965284:AAHbvpOdnfTopf14xxTLdsXiMEl4sjqEVXU"
    echo "  $0"
    exit 0
fi

# Запуск
main "$@" 