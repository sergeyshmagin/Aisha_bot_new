"""
Скрипт для применения миграции
"""
import os
import sys
from alembic import command
from alembic.config import Config

# Получаем корневую директорию проекта
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Добавляем корневую директорию в sys.path
sys.path.insert(0, base_dir)

# Создаем конфигурацию Alembic
alembic_cfg = Config(os.path.join(base_dir, "alembic.ini"))

# Применяем миграцию
command.upgrade(alembic_cfg, "head")

print("Миграция успешно применена")
