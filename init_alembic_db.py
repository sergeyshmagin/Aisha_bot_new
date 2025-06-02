#!/usr/bin/env python3
"""
Скрипт для принудительной инициализации Alembic в базе данных
"""
import asyncio
import asyncpg
import sys
import os

# Добавляем корневую папку проекта в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

async def init_alembic():
    """Инициализирует Alembic в базе данных"""
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL.replace('+asyncpg', ''))
        
        # Создаем таблицу alembic_version если её нет
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        
        # Устанавливаем текущую версию
        await conn.execute("""
            INSERT INTO alembic_version (version_num) 
            VALUES ('1f70882932cf')
            ON CONFLICT (version_num) DO NOTHING
        """)
        
        print("✅ Alembic инициализирован в базе данных")
        
        # Проверяем что получилось
        version = await conn.fetchval("SELECT version_num FROM alembic_version")
        print(f"🔧 Текущая версия: {version}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка инициализации Alembic: {e}")

if __name__ == "__main__":
    asyncio.run(init_alembic())
