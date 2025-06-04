#!/usr/bin/env python3
"""
Скрипт для обновления ENUM avatarstatus в PostgreSQL

Добавляет недостающие значения в enum avatarstatus:
- completed
- photos_uploading  
- ready_for_training
- cancelled

Использование:
    python scripts/update_avatar_status_enum.py
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_session
from app.core.config import settings
from sqlalchemy import text

async def update_avatar_status_enum():
    """Обновляет ENUM avatarstatus в PostgreSQL"""
    
    print("🔧 Обновление ENUM avatarstatus в PostgreSQL...")
    
    async with get_session() as session:
        # Список новых значений для добавления
        new_values = [
            'completed',
            'photos_uploading',
            'ready_for_training', 
            'cancelled'
        ]
        
        for value in new_values:
            try:
                # Пытаемся добавить новое значение в ENUM
                query = text(f"ALTER TYPE avatarstatus ADD VALUE IF NOT EXISTS '{value}'")
                await session.execute(query)
                await session.commit()
                print(f"✅ Добавлено значение '{value}' в ENUM avatarstatus")
                
            except Exception as e:
                print(f"⚠️  Ошибка добавления '{value}': {e}")
                await session.rollback()
        
        # Проверяем текущие значения ENUM
        print("\n🔍 Текущие значения ENUM avatarstatus:")
        query = text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'avatarstatus')
            ORDER BY enumlabel
        """)
        
        result = await session.execute(query)
        enum_values = result.fetchall()
        
        for row in enum_values:
            print(f"  • {row.enumlabel}")
        
        print(f"\n📊 Всего значений в ENUM: {len(enum_values)}")

async def check_avatar_statuses():
    """Проверяет текущие статусы аватаров в БД"""
    
    print("\n📊 Проверка текущих статусов аватаров...")
    
    async with get_session() as session:
        query = text("""
            SELECT status, COUNT(*) as count
            FROM avatars
            GROUP BY status
            ORDER BY count DESC
        """)
        
        result = await session.execute(query)
        status_counts = result.fetchall()
        
        if status_counts:
            print("Статистика по статусам:")
            for row in status_counts:
                print(f"  {row.status}: {row.count} аватаров")
        else:
            print("  Аватары не найдены в БД")

async def main():
    """Главная функция"""
    try:
        await update_avatar_status_enum()
        await check_avatar_statuses()
        print("\n✅ Обновление ENUM завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 