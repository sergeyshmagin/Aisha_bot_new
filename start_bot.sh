#!/bin/bash
# 🤖 Скрипт запуска Aisha Bot v2 для локальной разработки
# Использование: ./start_bot.sh

echo "🏠 Запуск Aisha Bot v2 (локальная разработка)"
echo "📡 API сервер: aibots.kz:8443"  
echo "🗄️  PostgreSQL: 192.168.0.4:5432"
echo "🔴 Redis: 192.168.0.3:6379"
echo "📦 MinIO: 192.168.0.4:9000"
echo "🔄 Режим: polling (локальная разработка)"
echo ""

# Проверка виртуального окружения
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Виртуальное окружение не активировано!"
    echo "💡 Выполните: source .venv/Scripts/activate"
    exit 1
fi

# Запуск бота через Python из виртуального окружения
echo "🚀 Запуск бота..."
.venv/Scripts/python.exe -m app.main 