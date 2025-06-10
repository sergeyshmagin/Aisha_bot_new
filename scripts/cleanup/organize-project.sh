#!/bin/bash

# ============================================================================
# Скрипт организации и очистки проекта Aisha
# Перемещает устаревшие файлы в архив, оставляет только активные
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

PROJECT_ROOT=$(pwd)

log_info "🧹 Организация и очистка проекта Aisha"

# 1. Создаем структуру архива
create_archive_structure() {
    log_info "📁 Создание структуры архива..."
    
    mkdir -p archive/{legacy_compose,legacy_scripts,old_deployments,deprecated_configs}
    
    log_info "✅ Структура архива создана"
}

# 2. Перемещаем устаревшие docker-compose файлы
organize_compose_files() {
    log_info "📦 Организация Docker Compose файлов..."
    
    # Активные файлы (оставляем в корне)
    ACTIVE_COMPOSE=(
        "docker-compose.bot.simple.yml"    # Основной продакшн
        "docker-compose.bot.local.yml"     # Локальное тестирование
    )
    
    # Перемещаем все остальные в архив
    for file in docker-compose*.yml; do
        if [[ -f "$file" ]]; then
            is_active=false
            for active in "${ACTIVE_COMPOSE[@]}"; do
                if [[ "$file" == "$active" ]]; then
                    is_active=true
                    break
                fi
            done
            
            if [[ "$is_active" == false ]]; then
                log_warn "📦 Перемещаем в архив: $file"
                mv "$file" "archive/legacy_compose/${file}_LEGACY"
            else
                log_info "✅ Активный файл: $file"
            fi
        fi
    done
    
    log_info "✅ Docker Compose файлы организованы"
}

# 3. Организуем скрипты
organize_scripts() {
    log_info "📜 Организация скриптов..."
    
    # Активные скрипты (оставляем)
    ACTIVE_SCRIPTS=(
        "scripts/production/deploy-fixed-bot.sh"
        "scripts/production/monitor-errors.sh"
        "scripts/production/check-transcription.sh"
        "scripts/production/restart-with-logs.sh"
        "scripts/production/setup-logging.sh"
        "scripts/cleanup/organize-project.sh"
    )
    
    # Устаревшие скрипты для перемещения
    LEGACY_SCRIPTS=(
        "check-prod-readiness.sh"
        "deploy-nginx.sh"
        "deploy-to-production.sh"
        "deploy-webhook-prod.sh"
        "nginx-management.sh"
    )
    
    for script in "${LEGACY_SCRIPTS[@]}"; do
        if [[ -f "scripts/$script" ]]; then
            log_warn "📜 Перемещаем устаревший скрипт: $script"
            mv "scripts/$script" "archive/legacy_scripts/${script}_LEGACY"
        fi
    done
    
    log_info "✅ Скрипты организованы"
}

# 4. Создаем актуальный README для активных файлов
create_active_files_readme() {
    log_info "📝 Создание документации активных файлов..."
    
    cat > ACTIVE_FILES.md << 'EOF'
# 🚀 Активные файлы проекта Aisha

## 📦 Docker Compose файлы

### Продакшн
- `docker-compose.bot.simple.yml` - **Основной продакшн файл**
  - Запускает aisha-bot-primary (polling) + aisha-worker-1 (background tasks)
  - Использует Docker volumes для постоянного хранения
  - Подключается к внешним сервисам (PostgreSQL, Redis, MinIO)

### Локальная разработка
- `docker-compose.bot.local.yml` - **Локальное тестирование**
  - Тестирование перед развертыванием на продакшн
  - Подключается к продакшн сервисам
  - Изолированные локальные volumes

## 📜 Активные скрипты

### Продакшн операции
- `scripts/production/deploy-fixed-bot.sh` - Развертывание исправленного бота
- `scripts/production/monitor-errors.sh` - Мониторинг ошибок в реальном времени
- `scripts/production/check-transcription.sh` - Проверка логов транскрибации
- `scripts/production/restart-with-logs.sh` - Перезапуск с мониторингом
- `scripts/production/setup-logging.sh` - Настройка детального логирования

### Обслуживание
- `scripts/cleanup/organize-project.sh` - Организация и очистка проекта

## 🗂️ Архив

Все устаревшие файлы перемещены в:
- `archive/legacy_compose/` - Старые docker-compose файлы
- `archive/legacy_scripts/` - Устаревшие скрипты
- `archive/old_deployments/` - Старые файлы развертывания
- `archive/deprecated_configs/` - Устаревшие конфигурации

## 🎯 Быстрые команды

### Локальное тестирование
```bash
# Запуск локального тестирования
docker-compose -f docker-compose.bot.local.yml up -d

# Проверка логов
docker logs aisha-bot-primary-local --tail 20 -f
```

### Продакшн управление
```bash
# Развертывание на продакшн
./scripts/production/deploy-fixed-bot.sh

# Мониторинг ошибок
ssh aisha@192.168.0.10 'cd /opt/aisha-backend && ./scripts/production/monitor-errors.sh'

# Проверка транскрибации
ssh aisha@192.168.0.10 'cd /opt/aisha-backend && ./scripts/production/check-transcription.sh'
```

## 🔧 Инфраструктура

### Сервисы
- **PostgreSQL**: 192.168.0.4:5432
- **Redis**: 192.168.0.3:6379  
- **MinIO**: 192.168.0.4:9000
- **Docker Registry**: 192.168.0.4:5000
- **Продакшн сервер**: 192.168.0.10

### Контейнеры на продакшн
- `aisha-bot-primary` - Основной бот (polling)
- `aisha-worker-1` - Фоновые задачи
- `aisha-webhook-api-1/2` - FAL AI webhooks

## 📊 Статус

✅ Все основные проблемы решены:
- Конфликты polling устранены
- Storage permissions исправлены  
- Worker модуль создан
- Детальное логирование настроено

EOF

    log_info "✅ Документация создана: ACTIVE_FILES.md"
}

# 5. Обновляем .gitignore
update_gitignore() {
    log_info "🔧 Обновление .gitignore..."
    
    # Добавляем архив в .gitignore если его там нет
    if ! grep -q "archive/" .gitignore 2>/dev/null; then
        echo "" >> .gitignore
        echo "# Архив устаревших файлов" >> .gitignore
        echo "archive/" >> .gitignore
        log_info "✅ Добавлен archive/ в .gitignore"
    else
        log_info "✅ archive/ уже в .gitignore"
    fi
}

# 6. Создаем скрипт для быстрого доступа к логам
create_quick_logs_script() {
    log_info "📱 Создание скрипта быстрого доступа к логам..."
    
    cat > scripts/quick-logs.sh << 'EOF'
#!/bin/bash

# Быстрый доступ к логам Aisha Bot

case "${1:-help}" in
    "prod")
        echo "📊 Логи продакшн primary bot:"
        ssh aisha@192.168.0.10 "docker logs aisha-bot-primary --tail 20 -f"
        ;;
    "worker")
        echo "🔄 Логи продакшн worker:"
        ssh aisha@192.168.0.10 "docker logs aisha-worker-1 --tail 20 -f"
        ;;
    "transcription")
        echo "🎙️ Проверка транскрибации:"
        ssh aisha@192.168.0.10 'cd /opt/aisha-backend && ./scripts/production/check-transcription.sh'
        ;;
    "monitor")
        echo "🔍 Мониторинг ошибок:"
        ssh aisha@192.168.0.10 'cd /opt/aisha-backend && ./scripts/production/monitor-errors.sh'
        ;;
    "local")
        echo "📱 Логи локального бота:"
        docker logs aisha-bot-primary-local --tail 20 -f 2>/dev/null || echo "❌ Локальный бот не запущен"
        ;;
    "status")
        echo "📊 Статус контейнеров на продакшн:"
        ssh aisha@192.168.0.10 "docker ps --format 'table {{.Names}}\t{{.Status}}'"
        ;;
    *)
        echo "🚀 Быстрый доступ к логам Aisha Bot"
        echo ""
        echo "Использование: $0 [команда]"
        echo ""
        echo "Команды:"
        echo "  prod          - Логи primary bot на продакшн"
        echo "  worker        - Логи worker на продакшн"
        echo "  transcription - Проверка транскрибации"
        echo "  monitor       - Мониторинг ошибок"
        echo "  local         - Логи локального бота"
        echo "  status        - Статус контейнеров"
        echo ""
        echo "Примеры:"
        echo "  $0 prod       # Показать логи primary bot"
        echo "  $0 monitor    # Запустить мониторинг ошибок"
        ;;
esac
EOF

    chmod +x scripts/quick-logs.sh
    log_info "✅ Создан scripts/quick-logs.sh"
}

# Выполняем все функции
create_archive_structure
organize_compose_files
organize_scripts
create_active_files_readme
update_gitignore
create_quick_logs_script

log_info "✅ Организация проекта завершена!"
log_info ""
log_info "📊 Итоги:"
log_info "  • Активные docker-compose файлы: 2"
log_info "  • Активные скрипты: сохранены в scripts/"
log_info "  • Устаревшие файлы: перемещены в archive/"
log_info "  • Документация: ACTIVE_FILES.md"
log_info "  • Быстрые логи: scripts/quick-logs.sh"
log_info ""
log_info "🚀 Для просмотра логов используйте:"
log_info "   ./scripts/quick-logs.sh [команда]" 