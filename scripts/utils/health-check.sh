#!/bin/bash

# ============================================================================
# 🏥 COMPREHENSIVE SYSTEM HEALTH CHECK
# ============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏥 Комплексная проверка здоровья системы Aisha Bot${NC}"

# Переходим в корень проекта
cd "$(dirname "$0")/../.."

# ============================================================================
# 🔧 Функции логирования
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Счетчики для финального отчета
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

check_result() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    case $1 in
        "pass") PASSED_CHECKS=$((PASSED_CHECKS + 1)) ;;
        "fail") FAILED_CHECKS=$((FAILED_CHECKS + 1)) ;;
        "warn") WARNING_CHECKS=$((WARNING_CHECKS + 1)) ;;
    esac
}

# ============================================================================
# 🌐 Проверка сетевых подключений
# ============================================================================

log_info "🌐 Проверка сетевых подключений..."

# Redis Server (192.168.0.3)
if timeout 5 redis-cli -h 192.168.0.3 -a wd7QuwAbG0wtyoOOw3Sm ping >/dev/null 2>&1; then
    log_success "✅ Redis Server (192.168.0.3) доступен"
    check_result "pass"
else
    log_error "❌ Redis Server (192.168.0.3) недоступен"
    check_result "fail"
fi

# PostgreSQL (192.168.0.4)
if timeout 5 pg_isready -h 192.168.0.4 -p 5432 >/dev/null 2>&1; then
    log_success "✅ PostgreSQL Server (192.168.0.4) доступен"
    check_result "pass"
else
    log_warning "⚠️ PostgreSQL Server (192.168.0.4) может быть недоступен"
    check_result "warn"
fi

# MinIO (192.168.0.4:9000)
if timeout 5 curl -s http://192.168.0.4:9000/minio/health/live >/dev/null 2>&1; then
    log_success "✅ MinIO Server (192.168.0.4:9000) доступен"
    check_result "pass"
else
    log_warning "⚠️ MinIO Server (192.168.0.4:9000) может быть недоступен"
    check_result "warn"
fi

# Docker Registry (192.168.0.4:5000)
if timeout 5 curl -s http://192.168.0.4:5000/v2/ >/dev/null 2>&1; then
    log_success "✅ Docker Registry (192.168.0.4:5000) доступен"
    check_result "pass"
else
    log_warning "⚠️ Docker Registry (192.168.0.4:5000) может быть недоступен"
    check_result "warn"
fi

# Webhook API (192.168.0.10:8443)
if timeout 5 curl -k -s https://192.168.0.10:8443/health >/dev/null 2>&1; then
    log_success "✅ Webhook API (192.168.0.10:8443) доступен"
    check_result "pass"
else
    log_warning "⚠️ Webhook API (192.168.0.10:8443) может быть недоступен"
    check_result "warn"
fi

# ============================================================================
# 🐳 Проверка Docker сервисов
# ============================================================================

log_info "🐳 Проверка Docker сервисов..."

# Проверка Docker daemon
if docker info >/dev/null 2>&1; then
    log_success "✅ Docker daemon работает"
    check_result "pass"
else
    log_error "❌ Docker daemon не доступен"
    check_result "fail"
fi

# Проверка docker-compose
if command -v docker-compose >/dev/null 2>&1; then
    log_success "✅ Docker Compose установлен"
    check_result "pass"
else
    log_error "❌ Docker Compose не установлен"
    check_result "fail"
fi

# Проверка запущенных контейнеров
RUNNING_CONTAINERS=$(docker ps -q | wc -l)
if [ "$RUNNING_CONTAINERS" -gt 0 ]; then
    log_success "✅ Запущено контейнеров: $RUNNING_CONTAINERS"
    check_result "pass"
    
    # Детальная информация о контейнерах
    echo "   Список запущенных контейнеров:"
    docker ps --format "   • {{.Names}}: {{.Status}}"
else
    log_warning "⚠️ Нет запущенных контейнеров"
    check_result "warn"
fi

# ============================================================================
# 💾 Проверка файловой системы
# ============================================================================

log_info "💾 Проверка файловой системы..."

# Проверка свободного места
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    log_success "✅ Свободное место на диске: $((100-DISK_USAGE))%"
    check_result "pass"
elif [ "$DISK_USAGE" -lt 90 ]; then
    log_warning "⚠️ Мало свободного места на диске: $((100-DISK_USAGE))%"
    check_result "warn"
else
    log_error "❌ Критически мало места на диске: $((100-DISK_USAGE))%"
    check_result "fail"
fi

# Проверка ключевых директорий
REQUIRED_DIRS=(
    "app"
    "docker"
    "scripts"
    "ssl_certificate"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_success "✅ Директория $dir существует"
        check_result "pass"
    else
        log_error "❌ Директория $dir отсутствует"
        check_result "fail"
    fi
done

# Проверка ключевых файлов
REQUIRED_FILES=(
    "docker-compose.webhook.prod.yml"
    "prod.env"
    "requirements.txt"
    "run.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_success "✅ Файл $file существует"
        check_result "pass"
    else
        log_warning "⚠️ Файл $file отсутствует"
        check_result "warn"
    fi
done

# ============================================================================
# 🔒 Проверка SSL сертификатов
# ============================================================================

log_info "🔒 Проверка SSL сертификатов..."

SSL_DIR="ssl_certificate"
if [ -d "$SSL_DIR" ]; then
    # Проверка наличия ключевых файлов
    SSL_FILES=(
        "$SSL_DIR/aibots.kz.crt"
        "$SSL_DIR/aibots.kz.key"
    )
    
    for ssl_file in "${SSL_FILES[@]}"; do
        if [ -f "$ssl_file" ]; then
            # Проверка срока действия сертификата
            if [ "${ssl_file##*.}" = "crt" ]; then
                EXPIRY_DATE=$(openssl x509 -in "$ssl_file" -noout -enddate 2>/dev/null | cut -d= -f2)
                if [ -n "$EXPIRY_DATE" ]; then
                    EXPIRY_TIMESTAMP=$(date -d "$EXPIRY_DATE" +%s)
                    CURRENT_TIMESTAMP=$(date +%s)
                    DAYS_LEFT=$(( (EXPIRY_TIMESTAMP - CURRENT_TIMESTAMP) / 86400 ))
                    
                    if [ "$DAYS_LEFT" -gt 30 ]; then
                        log_success "✅ SSL сертификат действителен ($DAYS_LEFT дней)"
                        check_result "pass"
                    elif [ "$DAYS_LEFT" -gt 7 ]; then
                        log_warning "⚠️ SSL сертификат истекает через $DAYS_LEFT дней"
                        check_result "warn"
                    else
                        log_error "❌ SSL сертификат истекает через $DAYS_LEFT дней"
                        check_result "fail"
                    fi
                else
                    log_warning "⚠️ Не удалось проверить срок действия сертификата"
                    check_result "warn"
                fi
            else
                log_success "✅ SSL ключ $ssl_file найден"
                check_result "pass"
            fi
        else
            log_error "❌ SSL файл $ssl_file отсутствует"
            check_result "fail"
        fi
    done
else
    log_error "❌ Директория SSL сертификатов отсутствует"
    check_result "fail"
fi

# ============================================================================
# 🧠 Проверка системных ресурсов
# ============================================================================

log_info "🧠 Проверка системных ресурсов..."

# Проверка памяти
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$MEMORY_USAGE" -lt 80 ]; then
    log_success "✅ Использование памяти: ${MEMORY_USAGE}%"
    check_result "pass"
elif [ "$MEMORY_USAGE" -lt 90 ]; then
    log_warning "⚠️ Высокое использование памяти: ${MEMORY_USAGE}%"
    check_result "warn"
else
    log_error "❌ Критическое использование памяти: ${MEMORY_USAGE}%"
    check_result "fail"
fi

# Проверка CPU load average
LOAD_AVERAGE=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
CPU_CORES=$(nproc)
LOAD_PERCENT=$(echo "$LOAD_AVERAGE * 100 / $CPU_CORES" | bc -l | awk '{printf "%.0f", $1}')

if [ "$LOAD_PERCENT" -lt 70 ]; then
    log_success "✅ Загрузка CPU: ${LOAD_PERCENT}% (LA: $LOAD_AVERAGE)"
    check_result "pass"
elif [ "$LOAD_PERCENT" -lt 90 ]; then
    log_warning "⚠️ Высокая загрузка CPU: ${LOAD_PERCENT}% (LA: $LOAD_AVERAGE)"
    check_result "warn"
else
    log_error "❌ Критическая загрузка CPU: ${LOAD_PERCENT}% (LA: $LOAD_AVERAGE)"
    check_result "fail"
fi

# ============================================================================
# 📊 Проверка логов на ошибки
# ============================================================================

log_info "📊 Проверка логов на ошибки..."

# Проверка системных логов
ERROR_COUNT=$(journalctl --since "1 hour ago" --no-pager -q | grep -i error | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    log_success "✅ Нет ошибок в системных логах за последний час"
    check_result "pass"
elif [ "$ERROR_COUNT" -lt 10 ]; then
    log_warning "⚠️ Найдено $ERROR_COUNT ошибок в системных логах"
    check_result "warn"
else
    log_error "❌ Найдено $ERROR_COUNT ошибок в системных логах"
    check_result "fail"
fi

# Проверка Docker логов
if docker ps -q | head -1 >/dev/null 2>&1; then
    CONTAINER_ERRORS=0
    for container in $(docker ps --format "{{.Names}}"); do
        CONTAINER_ERROR_COUNT=$(docker logs --since=1h "$container" 2>&1 | grep -i error | wc -l)
        CONTAINER_ERRORS=$((CONTAINER_ERRORS + CONTAINER_ERROR_COUNT))
    done
    
    if [ "$CONTAINER_ERRORS" -eq 0 ]; then
        log_success "✅ Нет ошибок в логах контейнеров"
        check_result "pass"
    elif [ "$CONTAINER_ERRORS" -lt 5 ]; then
        log_warning "⚠️ Найдено $CONTAINER_ERRORS ошибок в логах контейнеров"
        check_result "warn"
    else
        log_error "❌ Найдено $CONTAINER_ERRORS ошибок в логах контейнеров"
        check_result "fail"
    fi
fi

# ============================================================================
# 📈 Финальный отчет
# ============================================================================

echo ""
echo "============================================================================"
echo -e "${BLUE}📊 ФИНАЛЬНЫЙ ОТЧЕТ О СОСТОЯНИИ СИСТЕМЫ${NC}"
echo "============================================================================"
echo ""

# Расчет процентов
if [ "$TOTAL_CHECKS" -gt 0 ]; then
    PASS_PERCENT=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    FAIL_PERCENT=$((FAILED_CHECKS * 100 / TOTAL_CHECKS))
    WARN_PERCENT=$((WARNING_CHECKS * 100 / TOTAL_CHECKS))
else
    PASS_PERCENT=0
    FAIL_PERCENT=0
    WARN_PERCENT=0
fi

echo "📋 Статистика проверок:"
echo "  • Всего проверок:      $TOTAL_CHECKS"
echo "  • Успешных:            $PASSED_CHECKS ($PASS_PERCENT%)"
echo "  • С предупреждениями:  $WARNING_CHECKS ($WARN_PERCENT%)"
echo "  • Неудачных:           $FAILED_CHECKS ($FAIL_PERCENT%)"
echo ""

# Общий статус системы
if [ "$FAILED_CHECKS" -eq 0 ] && [ "$WARNING_CHECKS" -eq 0 ]; then
    echo -e "${GREEN}🎉 СИСТЕМА В ОТЛИЧНОМ СОСТОЯНИИ${NC}"
    SYSTEM_STATUS="EXCELLENT"
elif [ "$FAILED_CHECKS" -eq 0 ]; then
    echo -e "${YELLOW}✅ СИСТЕМА В ХОРОШЕМ СОСТОЯНИИ (есть предупреждения)${NC}"
    SYSTEM_STATUS="GOOD"
elif [ "$FAILED_CHECKS" -lt 3 ]; then
    echo -e "${YELLOW}⚠️ СИСТЕМА РАБОТАЕТ С ПРОБЛЕМАМИ${NC}"
    SYSTEM_STATUS="ISSUES"
else
    echo -e "${RED}🚨 СИСТЕМА ТРЕБУЕТ ВНИМАНИЯ${NC}"
    SYSTEM_STATUS="CRITICAL"
fi

echo ""
echo "🔧 Рекомендации:"

if [ "$FAILED_CHECKS" -gt 0 ]; then
    echo "  • Исправьте критические проблемы в первую очередь"
    echo "  • Проверьте логи: ./scripts/utils/log-analyzer.sh"
fi

if [ "$WARNING_CHECKS" -gt 0 ]; then
    echo "  • Обратите внимание на предупреждения"
    echo "  • Рассмотрите профилактические меры"
fi

if [ "$SYSTEM_STATUS" = "EXCELLENT" ]; then
    echo "  • Система работает оптимально"
    echo "  • Продолжайте регулярный мониторинг"
fi

echo ""
echo "📞 Поддержка:"
echo "  • Для детального анализа: ./scripts/utils/log-analyzer.sh"
echo "  • Для очистки системы: ./scripts/utils/cleanup.sh"
echo "  • Для создания бекапа: ./scripts/utils/backup.sh"

echo ""
echo "============================================================================"

# Возврат кода состояния
case $SYSTEM_STATUS in
    "EXCELLENT") exit 0 ;;
    "GOOD") exit 0 ;;
    "ISSUES") exit 1 ;;
    "CRITICAL") exit 2 ;;
esac 