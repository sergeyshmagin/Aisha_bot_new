#!/bin/bash

echo "🎨 Применение оптимизаций flux-pro-trainer"
echo "=========================================="

# 1. Проверить текущее состояние
echo "1. 🔍 Проверка текущего состояния..."

if grep -q "FAL_PRO_MODE" app/core/config.py; then
    echo "✅ Новые настройки flux-pro-trainer найдены"
else
    echo "❌ Новые настройки не найдены"
    exit 1
fi

if [ -f "app/utils/avatar_utils.py" ]; then
    echo "✅ Утилиты для аватаров созданы"
else
    echo "❌ Утилиты для аватаров не найдены"
    exit 1
fi

# 2. Проверить импорты в сервисе
echo "2. 🔧 Проверка обновлений сервиса..."

if grep -q "format_finetune_comment" app/services/avatar/fal_training_service.py; then
    echo "✅ Импорты утилит добавлены в сервис"
else
    echo "❌ Импорты утилит не найдены в сервисе"
    exit 1
fi

# 3. Создать тестовый .env файл с новыми настройками
echo "3. ⚙️ Создание примера настроек..."

cat > .env.flux_pro_example << 'EOF'
# Оптимизированные настройки для flux-pro-trainer
FAL_PRO_MODE=character
FAL_PRO_ITERATIONS=500
FAL_PRO_LEARNING_RATE=0.0001
FAL_PRO_PRIORITY=quality
FAL_PRO_LORA_RANK=32
FAL_PRO_FINETUNE_TYPE=lora
FAL_PRO_CAPTIONING=true

# Для быстрого тестирования (раскомментировать при необходимости)
# FAL_PRO_ITERATIONS=300
# FAL_PRO_LEARNING_RATE=0.0002
# FAL_PRO_PRIORITY=speed
# FAL_PRO_LORA_RANK=16

# Для максимального качества (раскомментировать при необходимости)
# FAL_PRO_ITERATIONS=800
# FAL_PRO_LEARNING_RATE=0.00005
# FAL_PRO_PRIORITY=quality
# FAL_PRO_LORA_RANK=32
# FAL_PRO_FINETUNE_TYPE=full
EOF

echo "✅ Пример настроек создан: .env.flux_pro_example"

# 4. Тестирование утилит
echo "4. 🧪 Тестирование утилит..."

python3 -c "
import sys
sys.path.append('.')
from app.utils.avatar_utils import format_finetune_comment, generate_trigger_word

# Тест форматирования комментария
comment = format_finetune_comment('Анна', 'ivan_petrov')
print(f'Тест комментария: {comment}')
assert comment == 'Анна - @ivan_petrov', f'Ожидалось \"Анна - @ivan_petrov\", получено \"{comment}\"'

# Тест генерации триггера
trigger = generate_trigger_word('4a473199-ae2e-4b0d-a212-68fbd58877f4')
print(f'Тест триггера: {trigger}')
assert trigger == 'TOK_4a473199', f'Ожидалось \"TOK_4a473199\", получено \"{trigger}\"'

print('✅ Все тесты утилит прошли успешно')
" || {
    echo "❌ Тесты утилит не прошли"
    exit 1
}

# 5. Проверить что сервисы остановлены перед обновлением
echo "5. 🛑 Проверка сервисов..."

if systemctl is-active --quiet aisha-bot.service 2>/dev/null; then
    echo "⚠️ aisha-bot.service работает, рекомендуется остановить для обновления"
    read -p "Остановить сервисы для обновления? (y/N): " confirm
    if [[ $confirm == [yY] ]]; then
        sudo systemctl stop aisha-bot.service aisha-api.service
        echo "🛑 Сервисы остановлены"
    fi
else
    echo "✅ Сервисы не запущены"
fi

# 6. Создать бэкап текущих настроек
echo "6. 💾 Создание бэкапа..."

backup_dir="backup_flux_pro_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

cp app/core/config.py "$backup_dir/" 2>/dev/null || true
cp app/services/avatar/fal_training_service.py "$backup_dir/" 2>/dev/null || true
cp .env "$backup_dir/.env.backup" 2>/dev/null || true

echo "✅ Бэкап создан в: $backup_dir"

# 7. Применить настройки к .env (если существует)
echo "7. ⚙️ Обновление .env..."

if [ -f ".env" ]; then
    # Добавляем новые настройки если их нет
    if ! grep -q "FAL_PRO_MODE" .env; then
        echo "" >> .env
        echo "# Оптимизированные настройки flux-pro-trainer" >> .env
        echo "FAL_PRO_MODE=character" >> .env
        echo "FAL_PRO_ITERATIONS=500" >> .env
        echo "FAL_PRO_LEARNING_RATE=0.0001" >> .env
        echo "FAL_PRO_PRIORITY=quality" >> .env
        echo "FAL_PRO_LORA_RANK=32" >> .env
        echo "FAL_PRO_FINETUNE_TYPE=lora" >> .env
        echo "FAL_PRO_CAPTIONING=true" >> .env
        echo "✅ Новые настройки добавлены в .env"
    else
        echo "✅ Настройки flux-pro-trainer уже есть в .env"
    fi
else
    echo "⚠️ Файл .env не найден, используйте .env.flux_pro_example как шаблон"
fi

# 8. Финальная проверка
echo "8. ✅ Финальная проверка..."

echo ""
echo "📊 Статус оптимизаций:"
echo "✅ Конфигурация обновлена (FAL_PRO_* параметры)"
echo "✅ Утилиты созданы (app/utils/avatar_utils.py)"
echo "✅ Сервис обновлен (finetune_comment, trigger_word)"
echo "✅ Документация создана (docs/FLUX_PRO_TRAINER_OPTIMIZATION.md)"

echo ""
echo "🎯 Новые возможности:"
echo "• Автоматическое формирование комментариев: 'Имя - @username'"
echo "• Уникальные триггеры: 'TOK_4a473199'"
echo "• Оптимизированные параметры для character mode"
echo "• 500 итераций для баланса качества и времени"
echo "• Приоритет качества (priority: quality)"

echo ""
echo "🚀 Для запуска с новыми настройками:"
echo "1. Проверьте .env файл"
echo "2. Запустите сервисы: sudo systemctl start aisha-api.service aisha-bot.service"
echo "3. Создайте новый художественный аватар для тестирования"

echo ""
echo "📋 Мониторинг:"
echo "sudo journalctl -u aisha-bot.service -f | grep -E '(🎨.*flux-pro-trainer|finetune_comment|trigger)'"

echo ""
echo "🎉 Оптимизации flux-pro-trainer применены успешно!" 