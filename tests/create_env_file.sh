#!/bin/bash
# Скрипт для создания .env файла с правильными настройками БД

echo "🔧 Создание .env файла с настройками БД..."

# Создаем .env файл
cat > .env << 'EOF'
# PostgreSQL настройки
POSTGRES_HOST=192.168.0.4
POSTGRES_PORT=5432
POSTGRES_DB=aisha
POSTGRES_USER=aisha_user
POSTGRES_PASSWORD=KbZZGJHX09KSH7r9ev4m

# Автоматически собранный DATABASE_URL
DATABASE_URL=postgresql+asyncpg://aisha_user:KbZZGJHX09KSH7r9ev4m@192.168.0.4:5432/aisha

# API Server настройки (Nginx проксирует 8443 -> 8000)
API_HOST=0.0.0.0
API_PORT=8000
SSL_ENABLED=false

# FAL AI настройки
FAL_WEBHOOK_URL=https://aibots.kz:8443/api/v1/avatar/status_update

# MinIO настройки
MINIO_ENDPOINT=192.168.0.4:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_BUCKET_AVATARS=avatars

# Режимы работы
FAL_TRAINING_TEST_MODE=false
AVATAR_TEST_MODE=false
EOF

echo "✅ .env файл создан"
echo "📋 Содержимое:"
cat .env

echo ""
echo "🔧 Архитектура:"
echo "   FAL AI -> https://aibots.kz:8443 (Nginx SSL)"
echo "   Nginx -> http://127.0.0.1:8000 (API сервер)"
echo ""
echo "🔧 Теперь проверьте переменные:"
echo "   source .env"
echo "   echo \$DATABASE_URL"
echo ""
echo "🔧 И перезапустите API сервер:"
echo "   sudo systemctl restart aisha-api.service" 