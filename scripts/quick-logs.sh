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
