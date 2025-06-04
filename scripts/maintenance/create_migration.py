"""
Скрипт для создания миграции с автоматическим определением изменений
"""
import os
import sys
import asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine

# Добавляем корневую директорию в sys.path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# Импортируем настройки и модели
from app.core.config import settings
from app.database.models import Base

def create_migration():
    # Создаем конфигурацию Alembic
    alembic_cfg = Config(os.path.join(base_dir, "alembic.ini"))
    
    # Используем аргументы командной строки или значение по умолчанию
    message = "auto-generated migration"
    if len(sys.argv) > 1:
        message = sys.argv[1]
    
    # Создаем миграцию с автоматическим определением изменений
    command.revision(alembic_cfg, autogenerate=True, message=message)
    
    print("Миграция успешно создана")

if __name__ == "__main__":
    create_migration()
