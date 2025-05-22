"""
Скрипт для создания тестовой базы данных
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from aisha_v2.app.core.config import settings


def create_test_database():
    """Создает тестовую базу данных"""
    # Подключаемся к базе данных postgres для создания новой БД
    engine = create_engine(
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/postgres"
    )
    
    test_db_name = f"{settings.POSTGRES_DB}_test"
    
    with engine.connect() as conn:
        # Отключаем активные подключения к тестовой БД
        conn.execute(text(
            f"SELECT pg_terminate_backend(pid) "
            f"FROM pg_stat_activity "
            f"WHERE datname = '{test_db_name}'"
        ))
        conn.execute(text("commit"))
        
        # Удаляем БД если она существует
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
        conn.execute(text("commit"))
        
        # Создаем новую тестовую БД
        conn.execute(text(f"CREATE DATABASE {test_db_name}"))
        conn.execute(text("commit"))
    
    print(f"Test database '{test_db_name}' created successfully!")


if __name__ == "__main__":
    create_test_database()
