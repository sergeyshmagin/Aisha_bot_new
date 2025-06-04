#!/usr/bin/env python3
"""
Скрипт для проверки enum значений в БД
"""
import asyncio
from app.core.database import get_session
from sqlalchemy import text

async def check_enum_values():
    async with get_session() as session:
        print('🔍 Проверяем текущие enum значения в БД...')
        
        # Проверяем статусы аватаров
        result = await session.execute(text('SELECT DISTINCT status FROM avatars;'))
        avatar_statuses = [row[0] for row in result.fetchall()]
        print(f'📊 Статусы аватаров в БД: {avatar_statuses}')
        
        # Проверяем пол аватаров
        result = await session.execute(text('SELECT DISTINCT gender FROM avatars;'))
        genders = [row[0] for row in result.fetchall()]
        print(f'👤 Пол аватаров в БД: {genders}')
        
        # Проверяем типы аватаров
        result = await session.execute(text('SELECT DISTINCT avatar_type FROM avatars;'))
        avatar_types = [row[0] for row in result.fetchall()]
        print(f'🎭 Типы аватаров в БД: {avatar_types}')
        
        # Проверяем типы обучения
        result = await session.execute(text('SELECT DISTINCT training_type FROM avatars;'))
        training_types = [row[0] for row in result.fetchall()]
        print(f'🧠 Типы обучения в БД: {training_types}')
        
        # Проверяем enum типы в PostgreSQL
        print('\n🗄️ Проверяем enum типы в PostgreSQL...')
        result = await session.execute(text("""
            SELECT t.typname, e.enumlabel 
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid 
            WHERE t.typname IN ('avatarstatus', 'avatargender', 'avatartype', 'avatartrainingtype')
            ORDER BY t.typname, e.enumsortorder;
        """))
        
        enum_values = {}
        for row in result.fetchall():
            enum_type, enum_value = row
            if enum_type not in enum_values:
                enum_values[enum_type] = []
            enum_values[enum_type].append(enum_value)
        
        for enum_type, values in enum_values.items():
            print(f'🔧 {enum_type}: {values}')

if __name__ == "__main__":
    asyncio.run(check_enum_values()) 