#!/bin/bash

echo "🚀 Проверка статуса обучения аватара"
echo "📋 Request ID из логов: 2adc5f75-bc37-4e44-b0e9-49577b26d816"
echo ""

# Сначала проверяем статус напрямую в FAL AI
echo "1️⃣ Прямая проверка статуса в FAL AI..."
python fix_missing_training_info.py 2adc5f75-bc37-4e44-b0e9-49577b26d816

echo ""
echo "2️⃣ Восстановление информации в БД и полная проверка..."
python fix_missing_training_info.py 165fab7d-3168-4a84-bc02-fec49f03b070 2adc5f75-bc37-4e44-b0e9-49577b26d816

echo ""
echo "3️⃣ Проверка через основной скрипт..."
python check_training_status.py 165fab7d-3168-4a84-bc02-fec49f03b070

echo ""
echo "✅ Проверка завершена!" 