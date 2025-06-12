#!/bin/bash

# ===============================================
# Скрипт запуска DEV бота Aisha
# ===============================================

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
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

# Определяем корневую директорию проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_info "🚀 Запуск DEV бота Aisha"
log_info "📁 Проект: $PROJECT_ROOT"

# Переходим в корень проекта
cd "$PROJECT_ROOT"

# Проверяем наличие виртуального окружения
if [[ ! -d ".venv" ]]; then
    log_error "❌ Виртуальное окружение .venv не найдено!"
    log_info "💡 Создайте его командой: python -m venv .venv"
    exit 1
fi

# Проверяем наличие .env файла
if [[ ! -f ".env" ]]; then
    log_error "❌ Файл .env не найден!"
    log_info "💡 Скопируйте из шаблона: cp env.example .env"
    exit 1
fi

# Активируем виртуальное окружение
log_info "🔧 Активация виртуального окружения..."
source .venv/bin/activate

# Проверяем активацию
if [[ -z "$VIRTUAL_ENV" ]]; then
    log_error "❌ Не удалось активировать виртуальное окружение!"
    exit 1
fi

log_success "✅ Виртуальное окружение активировано: $VIRTUAL_ENV"

# Очищаем переменные окружения, которые могут конфликтовать
log_info "🧹 Очистка конфликтующих переменных окружения..."
unset TELEGRAM_TOKEN
unset TELEGRAM_BOT_TOKEN
unset TELEGRAM_DEV_TOKEN

# Проверяем токен в .env
DEV_TOKEN=$(grep "^TELEGRAM_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
if [[ -z "$DEV_TOKEN" ]]; then
    log_error "❌ TELEGRAM_TOKEN не найден в .env файле!"
    exit 1
fi

# Извлекаем ID бота из токена
BOT_ID=$(echo "$DEV_TOKEN" | cut -d':' -f1)
log_info "🤖 Запуск бота с ID: $BOT_ID"

# Проверяем что это DEV токен (не продакшн)
if [[ "$BOT_ID" == "8063965284" ]]; then
    log_warning "⚠️  Внимание! Используется ПРОДАКШН токен!"
    log_warning "⚠️  Убедитесь что продакшн бот остановлен"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "❌ Запуск отменен"
        exit 1
    fi
fi

# Проверяем доступность базы данных
log_info "🔍 Проверка подключения к базе данных..."
if ! python -c "
import asyncio
import sys
sys.path.append('.')
from app.database.connection import get_db_session

async def test_db():
    try:
        async with get_db_session() as session:
            await session.execute('SELECT 1')
        print('✅ База данных доступна')
        return True
    except Exception as e:
        print(f'❌ Ошибка подключения к БД: {e}')
        return False

result = asyncio.run(test_db())
sys.exit(0 if result else 1)
" 2>/dev/null; then
    log_success "✅ База данных доступна"
else
    log_error "❌ Не удалось подключиться к базе данных!"
    log_info "💡 Проверьте настройки DATABASE_URL в .env"
    exit 1
fi

# Запускаем бота
log_info "🚀 Запуск DEV бота..."
log_info "📋 Для остановки нажмите Ctrl+C"
echo "=================================================="

# Запуск с обработкой сигналов
trap 'log_info "🛑 Получен сигнал остановки..."; exit 0' INT TERM

python -m app.main

log_success "✅ DEV бот завершен" 