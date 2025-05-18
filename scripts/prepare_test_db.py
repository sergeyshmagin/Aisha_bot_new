"""
Скрипт для подготовки тестовой базы данных.
Использует только переменные окружения из .env.test:
POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
"""

import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv
import subprocess

# Добавляем корень проекта в PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

async def prepare_test_db():
    """Подготовка тестовой базы данных."""
    load_dotenv(".env.test")
    
    # Получаем параметры подключения из окружения (ошибка, если не заданы)
    host = os.environ["POSTGRES_HOST"]
    port = int(os.environ["POSTGRES_PORT"])
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    db_name = os.environ["POSTGRES_DB"]
    
    # Подключаемся к postgres для создания/удаления БД
    sys_conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database="postgres"
    )
    
    # Удаляем БД если существует
    await sys_conn.execute(f"DROP DATABASE IF EXISTS {db_name}")
    # Создаем новую БД
    await sys_conn.execute(f"CREATE DATABASE {db_name}")
    await sys_conn.close()
    
    # Применяем миграции через subprocess (CLI alembic)
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    print("Тестовая база данных подготовлена успешно!")

if __name__ == "__main__":
    asyncio.run(prepare_test_db()) 