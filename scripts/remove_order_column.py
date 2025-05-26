#!/usr/bin/env python3
"""
Скрипт для удаления колонки order из таблицы avatar_photos
"""
import asyncio
from sqlalchemy import text
from app.core.database import async_engine

async def remove_order_column():
    """Удаляет колонку order из таблицы avatar_photos"""
    try:
        async with async_engine.begin() as conn:
            # Проверяем существование колонки
            check_sql = """
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'avatar_photos' 
                AND column_name = 'order'
            );
            """
            result = await conn.execute(text(check_sql))
            column_exists = result.scalar()
            
            if column_exists:
                # Удаляем колонку
                await conn.execute(text('ALTER TABLE avatar_photos DROP COLUMN "order";'))
                print('✅ Колонка "order" успешно удалена из таблицы avatar_photos')
            else:
                print('ℹ️ Колонка "order" не найдена в таблице avatar_photos')
                
    except Exception as e:
        print(f'❌ Ошибка при удалении колонки order: {e}')
        raise

if __name__ == "__main__":
    asyncio.run(remove_order_column()) 