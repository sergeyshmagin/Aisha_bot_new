#!/bin/bash

# ============================================================================
# Скрипт настройки подробного логирования для Aisha Bot
# Включает мониторинг ошибок транскрибации и других проблем
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

log_info "🔍 Настройка подробного логирования для Aisha Bot"

# Функция для мониторинга логов в реальном времени
setup_log_monitoring() {
    log_info "📊 Настройка мониторинга логов..."
    
    ssh ${PROD_USER}@${PROD_SERVER} << 'EOF'
    cd /opt/aisha-backend
    
    echo "🔧 Создание скриптов мониторинга..."
    
    # Создаем скрипт для мониторинга ошибок
    cat > scripts/production/monitor-errors.sh << 'MONITOR_EOF'
#!/bin/bash

# Мониторинг ошибок в логах Aisha Bot
echo "🔍 Мониторинг ошибок Aisha Bot"
echo "Press Ctrl+C to stop"
echo ""

# Функция для вывода цветных логов
show_logs() {
    docker logs "$1" --tail 0 -f 2>&1 | while read line; do
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        
        if echo "$line" | grep -qi "error\|exception\|traceback\|failed"; then
            echo -e "\033[0;31m[$timestamp] [$1] $line\033[0m"
        elif echo "$line" | grep -qi "transcrib"; then
            echo -e "\033[0;33m[$timestamp] [$1] $line\033[0m"
        elif echo "$line" | grep -qi "warning\|warn"; then
            echo -e "\033[1;33m[$timestamp] [$1] $line\033[0m"
        elif echo "$line" | grep -qi "info"; then
            echo -e "\033[0;32m[$timestamp] [$1] $line\033[0m"
        else
            echo "[$timestamp] [$1] $line"
        fi
    done
}

# Запускаем мониторинг для bot-primary и worker
show_logs "aisha-bot-primary" &
show_logs "aisha-worker-1" &

wait
MONITOR_EOF

    chmod +x scripts/production/monitor-errors.sh
    
    # Создаем скрипт для просмотра логов транскрибации
    cat > scripts/production/check-transcription.sh << 'TRANSCRIBE_EOF'
#!/bin/bash

echo "🎙️ Проверка логов транскрибации (последние 100 строк)"
echo "================================================"

echo ""
echo "🔍 Поиск ошибок транскрибации в primary bot:"
docker logs aisha-bot-primary --tail 100 | grep -E -i "(transcrib|audio|voice|speech)" --color=always || echo "Нет логов транскрибации"

echo ""
echo "🔍 Поиск общих ошибок:"
docker logs aisha-bot-primary --tail 50 | grep -E -i "(error|exception|failed)" --color=always || echo "Нет критических ошибок"

echo ""
echo "📊 Последние 10 строк логов primary bot:"
docker logs aisha-bot-primary --tail 10

echo ""
echo "📊 Последние 5 строк логов worker:"
docker logs aisha-worker-1 --tail 5

echo ""
echo "📈 Статус контейнеров:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep -E "(bot|worker)"

echo ""
echo "💾 Проверка прав доступа к storage:"
if docker exec aisha-bot-primary ls -la /app/storage/temp/ 2>/dev/null; then
    echo "✅ Доступ к storage в порядке"
else
    echo "❌ Проблемы с доступом к storage"
fi

echo ""
echo "🔧 Для непрерывного мониторинга используйте:"
echo "   ./scripts/production/monitor-errors.sh"
TRANSCRIBE_EOF

    chmod +x scripts/production/check-transcription.sh
    
    # Создаем скрипт для быстрого перезапуска с логами
    cat > scripts/production/restart-with-logs.sh << 'RESTART_EOF'
#!/bin/bash

echo "🔄 Перезапуск контейнеров с мониторингом логов"

# Останавливаем контейнеры
echo "🛑 Остановка контейнеров..."
docker-compose -f docker-compose.bot.simple.yml down

# Запускаем с логами
echo "🚀 Запуск контейнеров..."
docker-compose -f docker-compose.bot.simple.yml up -d

# Ждем запуска
echo "⏰ Ожидание запуска (15 секунд)..."
sleep 15

# Показываем статус
echo "📊 Статус контейнеров:"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "📋 Запуск мониторинга логов..."
exec ./scripts/production/monitor-errors.sh
RESTART_EOF

    chmod +x scripts/production/restart-with-logs.sh
    
    echo "✅ Скрипты мониторинга созданы:"
    echo "   📊 scripts/production/monitor-errors.sh - Мониторинг ошибок в реальном времени"
    echo "   🎙️ scripts/production/check-transcription.sh - Проверка логов транскрибации"
    echo "   🔄 scripts/production/restart-with-logs.sh - Перезапуск с мониторингом"

EOF
}

# Функция для улучшения конфигурации логирования
improve_logging_config() {
    log_info "🔧 Улучшение конфигурации логирования..."
    
    # Обновляем настройки логирования в config.py
    cat > /tmp/logging_patch.py << 'PATCH_EOF'
# Дополнения для app/core/config.py для улучшения логирования

# Настройки логирования (добавить в класс Settings)
LOG_LEVEL: str = Field(default="DEBUG", env="LOG_LEVEL")  # Изменено с INFO на DEBUG
ENABLE_SQL_LOGGING: bool = Field(default=True, env="ENABLE_SQL_LOGGING")
ENABLE_TELEGRAM_LOGGING: bool = Field(default=True, env="ENABLE_TELEGRAM_LOGGING")
ENABLE_TRANSCRIPTION_LOGGING: bool = Field(default=True, env="ENABLE_TRANSCRIPTION_LOGGING")
LOG_TO_FILE: bool = Field(default=True, env="LOG_TO_FILE")
LOG_FILE_PATH: str = Field(default="/app/logs/aisha-bot.log", env="LOG_FILE_PATH")
LOG_ROTATION_SIZE: str = Field(default="10MB", env="LOG_ROTATION_SIZE")
LOG_RETENTION_DAYS: int = Field(default=7, env="LOG_RETENTION_DAYS")

# Настройки детального логирования ошибок
ENABLE_DETAILED_ERROR_LOGGING: bool = Field(default=True, env="ENABLE_DETAILED_ERROR_LOGGING")
LOG_STACK_TRACES: bool = Field(default=True, env="LOG_STACK_TRACES")
TELEGRAM_ERROR_NOTIFICATION: bool = Field(default=False, env="TELEGRAM_ERROR_NOTIFICATION")

PATCH_EOF

    log_info "💾 Патч конфигурации создан в /tmp/logging_patch.py"
}

# Функция для создания детального логгера
create_detailed_logger() {
    log_info "📝 Создание модуля детального логирования..."
    
    cat > /tmp/detailed_logger.py << 'LOGGER_EOF'
"""
Модуль детального логирования для Aisha Bot
Включает специальное логирование для транскрибации и ошибок
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional
import asyncio

# Настройка форматирования
class DetailedFormatter(logging.Formatter):
    """Детальный форматтер с цветами для консоли"""
    
    COLORS = {
        'DEBUG': '\033[0;36m',    # Cyan
        'INFO': '\033[0;32m',     # Green
        'WARNING': '\033[1;33m',  # Yellow
        'ERROR': '\033[0;31m',    # Red
        'CRITICAL': '\033[1;31m', # Bold Red
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Добавляем цвет для консоли
        if hasattr(record, 'use_color') and record.use_color:
            color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{color}{record.levelname}{self.RESET}"
            record.msg = f"{color}{record.msg}{self.RESET}"
        
        # Детальная информация для ошибок
        if record.levelno >= logging.ERROR:
            if record.exc_info:
                record.msg = f"{record.msg}\n{'='*50}\nТрассировка:\n{traceback.format_exception(*record.exc_info)}"
        
        return super().format(record)

# Специальный логгер для транскрибации
def setup_transcription_logger():
    """Настройка специального логгера для транскрибации"""
    logger = logging.getLogger('transcription')
    logger.setLevel(logging.DEBUG)
    
    # Консольный хендлер с цветами
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    formatter = DetailedFormatter(
        '%(asctime)s - 🎙️ TRANSCRIPTION - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Добавляем флаг для цветного вывода
    console_handler.addFilter(lambda record: setattr(record, 'use_color', True) or True)
    
    logger.addHandler(console_handler)
    
    return logger

# Специальный логгер для ошибок
def setup_error_logger():
    """Настройка специального логгера для ошибок"""
    logger = logging.getLogger('errors')
    logger.setLevel(logging.ERROR)
    
    # Консольный хендлер с цветами
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.ERROR)
    
    formatter = DetailedFormatter(
        '%(asctime)s - ❌ ERROR - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Добавляем флаг для цветного вывода
    console_handler.addFilter(lambda record: setattr(record, 'use_color', True) or True)
    
    logger.addHandler(console_handler)
    
    return logger

# Функция для логирования исключений с контекстом
def log_exception_with_context(logger, message: str, exception: Exception, context: Optional[dict] = None):
    """Логирование исключения с дополнительным контекстом"""
    error_msg = f"{message}\n"
    error_msg += f"Тип ошибки: {type(exception).__name__}\n"
    error_msg += f"Сообщение: {str(exception)}\n"
    
    if context:
        error_msg += "Контекст:\n"
        for key, value in context.items():
            error_msg += f"  {key}: {value}\n"
    
    logger.error(error_msg, exc_info=True)

# Декоратор для автоматического логирования ошибок
def log_errors(logger_name: str = 'errors'):
    """Декоратор для автоматического логирования ошибок в функциях"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function': func.__name__,
                    'args': str(args)[:200],  # Ограничиваем длину
                    'kwargs': str(kwargs)[:200]
                }
                log_exception_with_context(
                    logger, 
                    f"Ошибка в функции {func.__name__}", 
                    e, 
                    context
                )
                raise
        
        def sync_wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function': func.__name__,
                    'args': str(args)[:200],
                    'kwargs': str(kwargs)[:200]
                }
                log_exception_with_context(
                    logger, 
                    f"Ошибка в функции {func.__name__}", 
                    e, 
                    context
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

LOGGER_EOF

    log_info "📝 Детальный логгер создан в /tmp/detailed_logger.py"
}

# Выполняем все функции
setup_log_monitoring
improve_logging_config
create_detailed_logger

log_info "✅ Настройка логирования завершена!"
log_info ""
log_info "🚀 Следующие шаги:"
log_info "1. Скопировать улучшения в код приложения"
log_info "2. Применить патчи логирования"
log_info "3. Перезапустить контейнеры"
log_info "4. Запустить мониторинг: ./scripts/production/monitor-errors.sh"
log_info ""
log_info "🔍 Для проверки транскрибации:"
log_info "   ssh aisha@192.168.0.10 'cd /opt/aisha-backend && ./scripts/production/check-transcription.sh'" 