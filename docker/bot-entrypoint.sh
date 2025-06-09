#!/bin/bash

# ============================================================================
# Entrypoint для масштабируемого Aisha Telegram Bot
# Поддержка режимов: polling, polling_standby, worker, webhook
# ============================================================================

set -e

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции логирования
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Проверка переменных окружения
check_required_env() {
    local required_vars=(
        "POSTGRES_HOST"
        "POSTGRES_DB" 
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "REDIS_HOST"
        "INSTANCE_ID"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_error "Обязательная переменная окружения $var не установлена"
            exit 1
        fi
    done
    
    log_info "✅ Все обязательные переменные окружения установлены"
}

# Проверка подключения к Redis
check_redis() {
    log_info "🔄 Проверка подключения к Redis..."
    
    python3 -c "
import redis
import os
import sys

try:
    r = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True,
        socket_timeout=5
    )
    r.ping()
    print('✅ Redis подключение успешно')
except Exception as e:
    print(f'❌ Ошибка подключения к Redis: {e}')
    sys.exit(1)
" || exit 1
}

# Проверка подключения к PostgreSQL
check_postgres() {
    log_info "🔄 Проверка подключения к PostgreSQL..."
    
    python3 -c "
import asyncpg
import asyncio
import os
import sys

async def check_db():
    try:
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        await conn.close()
        print('✅ PostgreSQL подключение успешно')
    except Exception as e:
        print(f'❌ Ошибка подключения к PostgreSQL: {e}')
        sys.exit(1)

asyncio.run(check_db())
" || exit 1
}

# Выполнение миграций (только для основного экземпляра)
run_migrations() {
    if [[ "${BOT_CLUSTER_NODE_ID:-1}" == "1" ]]; then
        log_info "🔄 Выполнение миграций базы данных..."
        
        python3 -c "
import asyncio
from alembic.config import Config
from alembic import command
import os

def run_migrations():
    try:
        alembic_cfg = Config('/app/alembic.ini')
        alembic_cfg.set_main_option('sqlalchemy.url', 
            f'postgresql+asyncpg://{os.getenv(\"POSTGRES_USER\")}:{os.getenv(\"POSTGRES_PASSWORD\")}@{os.getenv(\"POSTGRES_HOST\")}:{os.getenv(\"POSTGRES_PORT\")}/{os.getenv(\"POSTGRES_DB\")}')
        
        command.upgrade(alembic_cfg, 'head')
        print('✅ Миграции выполнены успешно')
    except Exception as e:
        print(f'❌ Ошибка выполнения миграций: {e}')
        raise

run_migrations()
" || {
            log_error "❌ Ошибка выполнения миграций"
            exit 1
        }
    else
        log_info "⏭️ Миграции пропущены (не основной экземпляр)"
    fi
}

# Основная функция запуска
main() {
    log_info "🚀 Запуск Aisha Bot - Экземпляр: ${INSTANCE_ID}"
    log_info "📍 Режим работы: ${1:-polling}"
    
    # Проверки
    check_required_env
    
    # Проверка подключений (без wait_for_service)
    check_redis
    check_postgres
    
    # Миграции
    run_migrations
    
    # Определяем режим запуска
    case "${1:-polling}" in
        "polling")
            log_info "🤖 Запуск в режиме polling"
            export BOT_MODE="polling"
            exec python3 main.py
            ;;
            
        "polling_standby")
            log_info "⏸️ Запуск в режиме polling standby"
            export BOT_MODE="polling_standby"
            # Задержка для standby экземпляра
            sleep 10
            exec python3 main.py
            ;;
            
        "worker")
            log_info "⚙️ Запуск в режиме background worker"
            export BOT_MODE="worker"
            exec python3 -c "
import asyncio
import sys
sys.path.append('/app')
from app.workers.background_worker import BackgroundWorker

async def main():
    worker = BackgroundWorker()
    await worker.start()

asyncio.run(main())
"
            ;;
            
        "webhook")
            log_info "🌐 Запуск в режиме webhook"
            export BOT_MODE="webhook"
            exec python3 main.py
            ;;
            
        *)
            log_error "❌ Неизвестный режим: $1"
            log_info "Доступные режимы: polling, polling_standby, worker, webhook"
            exit 1
            ;;
    esac
}

# Обработка сигналов для корректного завершения
trap 'log_info "🛑 Получен сигнал остановки, завершение работы..."; exit 0' SIGTERM SIGINT

# Запуск
main "$@" 