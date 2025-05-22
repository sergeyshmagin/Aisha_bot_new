#!/bin/bash

# Загружаем переменные окружения
source .env.test

# Создаем тестовую базу данных
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d postgres -c "DROP DATABASE IF EXISTS $POSTGRES_DB;"
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d postgres -c "CREATE DATABASE $POSTGRES_DB;"

# Применяем миграции
alembic upgrade head

echo "Тестовая база данных подготовлена успешно!" 