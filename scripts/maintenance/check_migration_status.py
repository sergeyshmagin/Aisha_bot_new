#!/usr/bin/env python3
"""Скрипт для проверки состояния миграций"""
import asyncio
import asyncpg
from app.core.config import settings


async def check_migration_status():
    """Проверка текущего состояния миграций"""
    try:
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB
        )
        
        # Проверяем существует ли таблица alembic_version
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'alembic_version'
            )
        """)
        
        if exists:
            version = await conn.fetchval('SELECT version_num FROM alembic_version')
            print(f"✅ Текущая версия миграции: {version}")
        else:
            print("❌ Таблица alembic_version не существует")
        
        # Проверяем существование таблицы avatars и её структуру
        avatar_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'avatars'
            )
        """)
        
        if avatar_exists:
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'avatars' 
                ORDER BY ordinal_position
            """)
            print(f"\n📋 Структура таблицы avatars ({len(columns)} колонок):")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']}")
            
            # Проверяем специально avatar_type
            has_avatar_type = any(col['column_name'] == 'avatar_type' for col in columns)
            if has_avatar_type:
                print("\n✅ Колонка avatar_type присутствует!")
            else:
                print("\n❌ Колонка avatar_type отсутствует!")
        else:
            print("❌ Таблица avatars не существует")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(check_migration_status()) 