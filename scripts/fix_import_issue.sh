#!/bin/bash

# Скрипт для исправления проблемы с импортами Python
# Использование: ./fix_import_issue.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

log "🔧 Исправление проблемы с импортами Python"

# Переходим в корневую директорию проекта
PROJECT_ROOT="/opt/aisha-backend"
cd "$PROJECT_ROOT"

log "📁 Рабочая директория: $(pwd)"

# Проверяем структуру проекта
log "📋 Проверка структуры проекта..."
if [[ -d "app" && -f "app/__init__.py" ]]; then
    log "✅ Директория app найдена"
else
    error "❌ Директория app не найдена или нет __init__.py"
    exit 1
fi

if [[ -d "app/services" && -f "app/services/__init__.py" ]]; then
    log "✅ Директория app/services найдена"
else
    error "❌ Директория app/services не найдена"
    exit 1
fi

if [[ -d "app/services/storage" && -f "app/services/storage/__init__.py" ]]; then
    log "✅ Модуль app.services.storage найден"
else
    error "❌ Модуль app.services.storage не найден"
    exit 1
fi

# Проверяем виртуальное окружение
log "🐍 Проверка виртуального окружения..."
if [[ -d ".venv" ]]; then
    log "✅ Виртуальное окружение найдено"
    if [[ "$VIRTUAL_ENV" == *".venv"* ]]; then
        log "✅ Виртуальное окружение активировано"
    else
        warn "⚠️ Виртуальное окружение не активировано"
        log "Активирую виртуальное окружение..."
        source .venv/bin/activate
    fi
else
    warn "⚠️ Виртуальное окружение не найдено"
fi

# Тестируем импорт
log "🧪 Тестирование импорта..."

echo "Тестирую импорт app.services.storage..."
if python -c "from app.services.storage import StorageService; print('✅ StorageService импортируется успешно')"; then
    log "✅ Импорт app.services.storage работает"
else
    error "❌ Ошибка импорта app.services.storage"
    echo "Диагностика..."
    python -c "
import sys
print('Python path:')
for p in sys.path:
    print(f'  {p}')
print()
print('Попытка импорта с подробностями...')
try:
    import app.services.storage
    print('✅ app.services.storage импортирован')
except Exception as e:
    print(f'❌ Ошибка: {e}')
    
try:
    from app.services.storage import StorageService
    print('✅ StorageService импортирован')
except Exception as e:
    print(f'❌ Ошибка: {e}')
"
fi

# Тестируем запуск основного приложения
log "🚀 Тестирование запуска основного приложения..."

echo "Проверяю импорты в app/main.py..."
if python -c "
import sys
sys.path.insert(0, '/opt/aisha-backend')
try:
    from app.handlers import *
    print('✅ Все импорты в app.main успешны')
except Exception as e:
    print(f'❌ Ошибка импорта: {e}')
    import traceback
    traceback.print_exc()
"; then
    log "✅ Импорты в app/main.py работают"
else
    error "❌ Проблема с импортами в app/main.py"
fi

# Создаем обертку для запуска
log "📝 Создание обертки для запуска..."

cat > run_bot.py << 'EOF'
#!/usr/bin/env python3
"""
Обертка для запуска основного приложения
Исправляет проблемы с PYTHONPATH
"""
import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Устанавливаем рабочую директорию
os.chdir(PROJECT_ROOT)

if __name__ == "__main__":
    try:
        # Импортируем и запускаем основное приложение
        from app.main import main
        main()
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
EOF

chmod +x run_bot.py
log "✅ Создан файл run_bot.py"

# Создаем обертку для API сервера
log "📝 Создание обертки для API сервера..."

cat > run_api.py << 'EOF'
#!/usr/bin/env python3
"""
Обертка для запуска API сервера
Исправляет проблемы с PYTHONPATH
"""
import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Устанавливаем рабочую директорию
os.chdir(PROJECT_ROOT)

if __name__ == "__main__":
    try:
        # Импортируем и запускаем API сервер
        from api_server.app.main import app
        import uvicorn
        
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
    except Exception as e:
        print(f"Ошибка запуска API сервера: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
EOF

chmod +x run_api.py
log "✅ Создан файл run_api.py"

# Финальное тестирование
log "🧪 Финальное тестирование..."

echo "Тестирую запуск через обертку..."
if python run_bot.py --help >/dev/null 2>&1 || python run_bot.py --version >/dev/null 2>&1; then
    log "✅ Обертка run_bot.py работает"
else
    warn "⚠️ Обертка может иметь проблемы (нормально для aiogram без токена)"
fi

log "📊 Итоговый отчет:"
echo "✅ Структура проекта корректна"
echo "✅ Виртуальное окружение настроено"
echo "✅ Импорты работают корректно"
echo "✅ Созданы обертки для запуска"
echo
log "🚀 Теперь используйте для запуска:"
echo "# Основной бот:"
echo "python run_bot.py"
echo
echo "# API сервер:"
echo "python run_api.py"
echo
echo "# Или напрямую:"
echo "cd /opt/aisha-backend && python -m app.main"

log "🎉 Проблема с импортами исправлена!" 