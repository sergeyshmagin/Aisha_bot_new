#!/bin/bash

# ============================================================================
# 🔧 MAKE ALL SCRIPTS EXECUTABLE
# ============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Установка прав на исполнение для всех скриптов...${NC}"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Переходим в корень проекта
cd "$(dirname "$0")/../.."

# ============================================================================
# 🔍 Поиск и обработка скриптов
# ============================================================================

log_info "Поиск всех .sh файлов в проекте..."

# Счетчики
FOUND=0
PROCESSED=0
ERRORS=0

# Поиск всех .sh файлов
while IFS= read -r -d '' file; do
    FOUND=$((FOUND + 1))
    
    # Проверка текущих прав
    CURRENT_PERMS=$(stat -c "%a" "$file")
    
    # Установка прав 755
    if chmod 755 "$file" 2>/dev/null; then
        NEW_PERMS=$(stat -c "%a" "$file")
        if [ "$CURRENT_PERMS" != "$NEW_PERMS" ]; then
            echo "  ✅ $file ($CURRENT_PERMS → $NEW_PERMS)"
        else
            echo "  ✓  $file (уже исполняемый)"
        fi
        PROCESSED=$((PROCESSED + 1))
    else
        log_error "❌ Не удалось установить права для $file"
        ERRORS=$((ERRORS + 1))
    fi
done < <(find . -name "*.sh" -type f -print0)

# ============================================================================
# 📊 Обработка Python скриптов в scripts/
# ============================================================================

log_info "Обработка Python скриптов в scripts/..."

while IFS= read -r -d '' file; do
    FOUND=$((FOUND + 1))
    
    # Проверка shebang в Python файлах
    if head -1 "$file" | grep -q "^#!/"; then
        CURRENT_PERMS=$(stat -c "%a" "$file")
        
        if chmod 755 "$file" 2>/dev/null; then
            NEW_PERMS=$(stat -c "%a" "$file")
            if [ "$CURRENT_PERMS" != "$NEW_PERMS" ]; then
                echo "  ✅ $file ($CURRENT_PERMS → $NEW_PERMS)"
            else
                echo "  ✓  $file (уже исполняемый)"
            fi
            PROCESSED=$((PROCESSED + 1))
        else
            log_error "❌ Не удалось установить права для $file"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "  ℹ️  $file (нет shebang, пропускаем)"
    fi
done < <(find scripts/ -name "*.py" -type f -print0 2>/dev/null || true)

# ============================================================================
# 🔍 Проверка основных скриптов в корне
# ============================================================================

log_info "Проверка основных скриптов в корне проекта..."

ROOT_SCRIPTS=(
    "run.py"
    "manage.py"
    "start.sh"
    "deploy.sh"
)

for script in "${ROOT_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        FOUND=$((FOUND + 1))
        
        # Проверка shebang
        if head -1 "$script" | grep -q "^#!/"; then
            CURRENT_PERMS=$(stat -c "%a" "$script")
            
            if chmod 755 "$script" 2>/dev/null; then
                NEW_PERMS=$(stat -c "%a" "$script")
                if [ "$CURRENT_PERMS" != "$NEW_PERMS" ]; then
                    echo "  ✅ $script ($CURRENT_PERMS → $NEW_PERMS)"
                else
                    echo "  ✓  $script (уже исполняемый)"
                fi
                PROCESSED=$((PROCESSED + 1))
            else
                log_error "❌ Не удалось установить права для $script"
                ERRORS=$((ERRORS + 1))
            fi
        else
            echo "  ℹ️  $script (нет shebang, пропускаем)"
        fi
    fi
done

# ============================================================================
# 📝 Создание списка всех исполняемых файлов
# ============================================================================

log_info "Создание списка всех исполняемых файлов..."

EXECUTABLE_LIST="docs/EXECUTABLE_FILES.md"
mkdir -p docs

cat > "$EXECUTABLE_LIST" << 'EOF'
# 🔧 Исполняемые файлы проекта

Автоматически сгенерированный список всех исполняемых файлов в проекте.

## 📂 Скрипты развертывания (scripts/deploy/)

EOF

# Добавление deploy скриптов
find scripts/deploy/ -name "*.sh" -type f -executable 2>/dev/null | sort | while read file; do
    echo "- \`$file\` - $(head -3 "$file" | grep '^#' | tail -1 | sed 's/^# *//' | sed 's/^=//')" >> "$EXECUTABLE_LIST"
done

cat >> "$EXECUTABLE_LIST" << 'EOF'

## 🏗️ Скрипты инфраструктуры (scripts/infrastructure/)

EOF

# Добавление infrastructure скриптов
find scripts/infrastructure/ -name "*.sh" -type f -executable 2>/dev/null | sort | while read file; do
    echo "- \`$file\` - $(head -3 "$file" | grep '^#' | tail -1 | sed 's/^# *//' | sed 's/^=//')" >> "$EXECUTABLE_LIST"
done

cat >> "$EXECUTABLE_LIST" << 'EOF'

## 🛠️ Утилиты (scripts/utils/)

EOF

# Добавление utils скриптов
find scripts/utils/ -name "*.sh" -type f -executable 2>/dev/null | sort | while read file; do
    echo "- \`$file\` - $(head -3 "$file" | grep '^#' | tail -1 | sed 's/^# *//' | sed 's/^=//')" >> "$EXECUTABLE_LIST"
done

cat >> "$EXECUTABLE_LIST" << 'EOF'

## 🔧 Скрипты обслуживания (scripts/maintenance/)

EOF

# Добавление maintenance скриптов
find scripts/maintenance/ -name "*.py" -type f -executable 2>/dev/null | sort | while read file; do
    echo "- \`$file\` - $(head -5 "$file" | grep '^#' | grep -v '#!/' | head -1 | sed 's/^# *//')" >> "$EXECUTABLE_LIST"
done

cat >> "$EXECUTABLE_LIST" << 'EOF'

## 📋 Основные файлы

EOF

# Добавление основных файлов
for script in run.py manage.py start.sh deploy.sh; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo "- \`$script\` - $(head -5 "$script" | grep '^#' | grep -v '#!/' | head -1 | sed 's/^# *//')" >> "$EXECUTABLE_LIST"
    fi
done

cat >> "$EXECUTABLE_LIST" << 'EOF'

---
*Файл сгенерирован автоматически скриптом `scripts/utils/make-executable.sh`*
EOF

# ============================================================================
# 📊 Финальный отчет
# ============================================================================

echo ""
echo -e "${GREEN}🎉 Обработка завершена!${NC}"
echo ""
echo "📊 Статистика:"
echo "  • Найдено файлов:     $FOUND"
echo "  • Обработано:         $PROCESSED"
echo "  • Ошибок:             $ERRORS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Все скрипты готовы к использованию!${NC}"
else
    echo -e "${YELLOW}⚠️ Есть ошибки, проверьте права доступа${NC}"
fi

echo ""
echo "📝 Список исполняемых файлов сохранен в: $EXECUTABLE_LIST"
echo ""
echo "🔧 Основные команды:"
echo "  ./scripts/deploy/webhook-complete.sh      # Полное развертывание"
echo "  ./scripts/infrastructure/production-setup.sh  # Настройка сервера"
echo "  ./scripts/utils/health-check.sh           # Проверка системы"

log_info "Готово! 🚀" 