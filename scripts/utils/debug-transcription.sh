#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# 🔍 ДИАГНОСТИКА ТРАНСКРИБАЦИИ AISHA BOT
# ═══════════════════════════════════════════════════════════════════════════════
# Версия: 1.0
# Дата: 2025-06-09
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

# Логирование
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "${CYAN}[===]${NC} $1"; }

# Проверка статуса бота
check_bot_status() {
    log_section "🤖 СТАТУС ОСНОВНОГО БОТА"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "📦 Контейнер:"
        docker ps --filter "name=aisha-bot-polling-1" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        echo
        echo "💚 Health статус:"
        docker inspect aisha-bot-polling-1 --format="{{.State.Health.Status}}" 2>/dev/null || echo "No health check"
        
        echo
        echo "📝 Последние 10 строк логов:"
        docker logs aisha-bot-polling-1 --tail 10
    '
}

# Поиск ошибок транскрибации
search_transcription_errors() {
    log_section "🔍 ПОИСК ОШИБОК ТРАНСКРИБАЦИИ"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "🚨 Ошибки связанные с транскрибацией:"
        docker logs aisha-bot-polling-1 2>&1 | grep -i -E "(transcript|audio|voice|whisper|ERROR)" | tail -20 || echo "Нет ошибок транскрибации в логах"
        
        echo
        echo "📊 Статистика обработки сообщений:"
        docker logs aisha-bot-polling-1 2>&1 | grep -c "Update.*is handled" | tail -5 || echo "0"
    '
}

# Проверка worker'ов
check_workers() {
    log_section "⚙️ ПРОВЕРКА WORKER'ОВ"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "📦 Worker контейнеры:"
        docker ps --filter "name=aisha-worker" --format "table {{.Names}}\t{{.Status}}"
        
        echo
        echo "📝 Логи worker-1:"
        docker logs aisha-worker-1 --tail 5 2>/dev/null || echo "Worker-1 не найден"
    '
}

# Проверка Redis очередей
check_redis_queues() {
    log_section "🟥 ПРОВЕРКА REDIS ОЧЕРЕДЕЙ"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "📊 Очереди Redis:"
        docker exec redis-prod redis-cli LLEN transcript_queue 2>/dev/null && echo "transcript_queue found" || echo "transcript_queue not found"
        docker exec redis-prod redis-cli LLEN audio_queue 2>/dev/null && echo "audio_queue found" || echo "audio_queue not found"
        
        echo
        echo "🔍 Проверка ключей Redis:"
        docker exec redis-prod redis-cli KEYS "*transcript*" 2>/dev/null | head -5 || echo "Нет ключей transcript"
        docker exec redis-prod redis-cli KEYS "*audio*" 2>/dev/null | head -5 || echo "Нет ключей audio"
    '
}

# Проверка обработчиков транскрибации
check_handlers() {
    log_section "🎧 ПРОВЕРКА ОБРАБОТЧИКОВ"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "📝 Поиск активности обработчиков аудио:"
        docker logs aisha-bot-polling-1 2>&1 | grep -i -E "(audio.*handler|transcript.*handler|voice.*message)" | tail -10 || echo "Нет активности обработчиков"
        
        echo
        echo "🔍 Поиск ошибок импорта:"
        docker logs aisha-bot-polling-1 2>&1 | grep -i -E "(import.*error|module.*not.*found)" | tail -5 || echo "Нет ошибок импорта"
    '
}

# Проверка переменных окружения
check_env_vars() {
    log_section "🌍 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "🔑 Ключевые переменные:"
        docker exec aisha-bot-polling-1 env | grep -E "(OPENAI|TELEGRAM|REDIS|POSTGRES|MINIO)" | head -10
        
        echo
        echo "📁 Проверка директорий:"
        docker exec aisha-bot-polling-1 ls -la /app/storage/ 2>/dev/null || echo "Директория /app/storage недоступна"
    '
}

# Проверка внешних сервисов
check_external_services() {
    log_section "🌐 ВНЕШНИЕ СЕРВИСЫ"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        echo "🐘 PostgreSQL:"
        docker exec postgres-prod pg_isready -U aisha 2>/dev/null && echo "✅ PostgreSQL готов" || echo "❌ PostgreSQL недоступен"
        
        echo
        echo "🟥 Redis:"
        docker exec redis-prod redis-cli ping 2>/dev/null && echo "✅ Redis готов" || echo "❌ Redis недоступен"
        
        echo
        echo "📦 MinIO:"
        curl -s http://localhost:9000/minio/health/ready && echo "✅ MinIO готов" || echo "❌ MinIO недоступен"
    '
}

# Тест отправки голосового сообщения
test_voice_message() {
    log_section "🎤 ИНСТРУКЦИИ ДЛЯ ТЕСТИРОВАНИЯ"
    
    log_info "Для тестирования транскрибации:"
    echo "1. Откройте Telegram и найдите бота"
    echo "2. Отправьте короткое голосовое сообщение (до 30 сек)"
    echo "3. Следите за логами в реальном времени:"
    echo "   ssh aisha@192.168.0.10 'docker logs aisha-bot-polling-1 --follow'"
    echo "4. Ожидайте ответ бота с транскрипцией"
    echo ""
    log_warn "Если транскрибация не работает, проверьте:"
    echo "   - OpenAI API ключ"
    echo "   - Обработчики аудио сообщений"
    echo "   - Права доступа к storage директории"
}

# Краткая сводка проблем
problem_summary() {
    log_section "📋 КРАТКАЯ СВОДКА"
    
    ssh ${PROD_USER}@${PROD_SERVER} '
        # Подсчет различных типов проблем
        error_count=$(docker logs aisha-bot-polling-1 2>&1 | grep -c "ERROR" || echo 0)
        warning_count=$(docker logs aisha-bot-polling-1 2>&1 | grep -c "WARNING" || echo 0)
        handled_count=$(docker logs aisha-bot-polling-1 2>&1 | grep -c "is handled" || echo 0)
        
        echo "📊 Статистика за текущую сессию:"
        echo "   • Ошибки (ERROR): $error_count"
        echo "   • Предупреждения (WARNING): $warning_count" 
        echo "   • Обработанные сообщения: $handled_count"
        
        if [[ $error_count -gt 50 ]]; then
            echo "🚨 КРИТИЧНО: Много ошибок ($error_count)"
        elif [[ $error_count -gt 10 ]]; then
            echo "⚠️ ВНИМАНИЕ: Умеренное количество ошибок ($error_count)"
        else
            echo "✅ ХОРОШО: Мало ошибок ($error_count)"
        fi
        
        if [[ $handled_count -gt 0 ]]; then
            echo "✅ ХОРОШО: Бот обрабатывает сообщения ($handled_count)"
        else
            echo "❌ ПРОБЛЕМА: Нет обработанных сообщений"
        fi
    '
}

# Основная функция
main() {
    local mode="${1:-full}"
    
    log_info "🔍 Диагностика транскрибации Aisha Bot"
    log_info "📍 Сервер: ${PROD_USER}@${PROD_SERVER}"
    log_info "🕒 $(date)"
    echo
    
    case "$mode" in
        "status"|"s")
            check_bot_status
            ;;
        "errors"|"e")
            search_transcription_errors
            ;;
        "workers"|"w")
            check_workers
            ;;
        "redis"|"r")
            check_redis_queues
            ;;
        "handlers"|"h")
            check_handlers
            ;;
        "env")
            check_env_vars
            ;;
        "services")
            check_external_services
            ;;
        "test"|"t")
            test_voice_message
            ;;
        "summary"|"sum")
            problem_summary
            ;;
        "quick"|"q")
            check_bot_status
            echo
            search_transcription_errors
            echo
            problem_summary
            ;;
        "full"|*)
            check_bot_status
            echo
            search_transcription_errors
            echo
            check_workers
            echo
            check_redis_queues
            echo
            check_handlers
            echo
            check_env_vars
            echo
            check_external_services
            echo
            problem_summary
            echo
            test_voice_message
            ;;
    esac
    
    echo
    log_info "✅ Диагностика завершена"
}

# Справка
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Использование: $0 [режим]"
    echo
    echo "Режимы диагностики:"
    echo "  full, f        - Полная диагностика (по умолчанию)"
    echo "  quick, q       - Быстрая проверка"
    echo "  status, s      - Только статус бота"
    echo "  errors, e      - Только ошибки транскрибации"
    echo "  workers, w     - Только worker'ы"
    echo "  redis, r       - Только Redis очереди"
    echo "  handlers, h    - Только обработчики"
    echo "  env            - Только переменные окружения"
    echo "  services       - Только внешние сервисы"
    echo "  test, t        - Инструкции для тестирования"
    echo "  summary, sum   - Только сводка проблем"
    echo
    echo "Примеры:"
    echo "  $0              # Полная диагностика"
    echo "  $0 quick        # Быстрая проверка"
    echo "  $0 errors       # Только ошибки"
    exit 0
fi

# Запуск
main "$@" 