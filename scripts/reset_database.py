#!/usr/bin/env python3
"""
Скрипт для полной очистки и пересоздания базы данных
ВНИМАНИЕ: ВСЕ ДАННЫЕ БУДУТ ПОТЕРЯНЫ!
"""
import asyncio
import asyncpg
from app.core.config import settings
from app.database.models import Base
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError


async def reset_database():
    """Полная очистка и пересоздание БД"""
    print("🔥 Начинаю сброс базы данных...")
    
    # Подключение к БД
    try:
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB
        )
        print("✅ Подключение к БД установлено")
        
        # Получаем список всех таблиц
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename != 'pg_stat_statements'
        """)
        
        print(f"📋 Найдено таблиц: {len(tables)}")
        for table in tables:
            print(f"  - {table['tablename']}")
        
        # Удаляем все таблицы
        for table in tables:
            table_name = table['tablename']
            await conn.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
            print(f"🗑️  Удалена таблица: {table_name}")
        
        await conn.close()
        print("✅ Все таблицы удалены")
        
        # Создаем таблицы заново через SQLAlchemy
        print("🏗️  Создаю таблицы заново...")
        engine = create_engine(
            settings.DATABASE_URL.replace("+asyncpg", ""),
            echo=True
        )
        
        Base.metadata.create_all(engine)
        print("✅ Все таблицы созданы заново")
        
        engine.dispose()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(reset_database()) 