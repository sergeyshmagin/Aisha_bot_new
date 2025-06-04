#!/usr/bin/env python3
import asyncio
from app.core.database import get_session
from sqlalchemy import text

async def check():
    async with get_session() as session:
        print('🔍 PostgreSQL enum типы:')
        result = await session.execute(text("""
            SELECT t.typname, e.enumlabel 
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid 
            WHERE t.typname = 'avatarstatus'
            ORDER BY e.enumsortorder;
        """))
        enum_values = []
        for row in result.fetchall():
            enum_values.append(row[1])
            print(f'   {row[1]}')
        
        print('\n🗄️ Данные в таблице:')
        result = await session.execute(text('SELECT DISTINCT status FROM avatars LIMIT 5;'))
        data_values = []
        for row in result.fetchall():
            data_values.append(row[0])
            print(f'   {row[0]}')
        
        print(f'\n📊 Анализ:')
        print(f'   Enum определения: {enum_values}')
        print(f'   Данные в БД: {data_values}')
        
        # Проверим соответствие
        mismatch = []
        for data_val in data_values:
            if data_val not in enum_values:
                mismatch.append(data_val)
        
        if mismatch:
            print(f'❌ ПРОБЛЕМА: данные {mismatch} не соответствуют enum {enum_values}')
        else:
            print(f'✅ Данные соответствуют enum определениям')

if __name__ == "__main__":
    asyncio.run(check()) 