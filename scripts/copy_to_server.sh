#!/bin/bash

# Скрипт для копирования файлов исправления на сервер aibots.kz
# Использование: ./copy_to_server.sh

set -e

SERVER="aibots.kz"
USER="aisha"
TARGET_DIR="/opt/aisha-backend"

echo "🚀 Копирование файлов на сервер $SERVER..."

# Проверяем что файлы существуют локально
if [[ ! -f "fix_import_issue.sh" ]]; then
    echo "❌ Файл fix_import_issue.sh не найден"
    exit 1
fi

if [[ ! -f "PYTHON_IMPORT_FIX.md" ]]; then
    echo "❌ Файл PYTHON_IMPORT_FIX.md не найден"
    exit 1
fi

# Копируем файлы на сервер
echo "📁 Копирование fix_import_issue.sh..."
scp fix_import_issue.sh $USER@$SERVER:$TARGET_DIR/

echo "📁 Копирование PYTHON_IMPORT_FIX.md..."
scp PYTHON_IMPORT_FIX.md $USER@$SERVER:$TARGET_DIR/

echo "✅ Файлы скопированы успешно!"

echo "🔧 Теперь подключитесь к серверу и запустите:"
echo "ssh $USER@$SERVER"
echo "cd $TARGET_DIR"
echo "chmod +x fix_import_issue.sh"
echo "./fix_import_issue.sh" 