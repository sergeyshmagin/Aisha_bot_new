#!/usr/bin/env python3
"""
Скрипт для проверки статусов в БД и enum
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_session
from sqlalchemy import text

async def check_statuses():
    """Проверяет статусы в БД и enum"""
    
    async with get_session() as session:
        # Проверяем что есть в таблице avatars
        result = await session.execute(text('SELECT DISTINCT status FROM avatars ORDER BY status'))
        db_statuses = [row[0] for row in result]
        print('📊 Статусы в таблице avatars:', db_statuses)
        
        # Проверяем enum в PostgreSQL
        result2 = await session.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'avatarstatus') 
            ORDER BY enumlabel
        """))
        enum_values = [row[0] for row in result2]
        print('🔍 Значения enum avatarstatus:', enum_values)
        
        # Проверяем несоответствия
        db_set = set(db_statuses)
        enum_set = set(enum_values)
        
        if db_set == enum_set:
            print('✅ Все статусы соответствуют enum')
        else:
            print('❌ Есть несоответствия:')
            only_in_db = db_set - enum_set
            only_in_enum = enum_set - db_set
            
            if only_in_db:
                print(f'   Только в БД: {only_in_db}')
            if only_in_enum:
                print(f'   Только в enum: {only_in_enum}')

if __name__ == "__main__":
    asyncio.run(check_statuses()) 