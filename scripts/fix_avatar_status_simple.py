#!/usr/bin/env python3
"""
Скрипт для исправления статусов аватаров

Заменяет UPPERCASE статусы на lowercase эквиваленты.

Использование:
    python scripts/fix_avatar_status_simple.py
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

async def fix_avatar_statuses():
    """Исправляет статусы аватаров"""
    
    print("🔧 Исправление статусов аватаров...")
    
    # Маппинг UPPERCASE -> lowercase
    status_mapping = {
        'COMPLETED': 'completed',
        'READY_FOR_TRAINING': 'ready_for_training',
        'PHOTOS_UPLOADING': 'photos_uploading',
        'TRAINING': 'training',
        'DRAFT': 'draft',
        'ERROR': 'error',
        'CANCELLED': 'cancelled'
    }
    
    async with get_session() as session:
        # Проверяем текущие статусы
        print("📊 Текущие статусы:")
        query = text("SELECT status, COUNT(*) as count FROM avatars GROUP BY status ORDER BY count DESC")
        result = await session.execute(query)
        status_counts = result.fetchall()
        
        for row in status_counts:
            print(f"  {row.status}: {row.count} аватаров")
        
        print("\n🔧 Исправление...")
        
        total_updated = 0
        
        # Исправляем каждый статус отдельно
        for old_status, new_status in status_mapping.items():
            query = text(f"UPDATE avatars SET status = '{new_status}' WHERE status = '{old_status}'")
            result = await session.execute(query)
            updated_count = result.rowcount
            
            if updated_count > 0:
                print(f"  ✅ {old_status} → {new_status}: {updated_count} аватаров")
                total_updated += updated_count
        
        await session.commit()
        
        print(f"\n📊 Всего обновлено: {total_updated} аватаров")
        
        # Проверяем результат
        print("\n🔍 Статусы после исправления:")
        result = await session.execute(query)
        status_counts = result.fetchall()
        
        for row in status_counts:
            print(f"  {row.status}: {row.count} аватаров")

async def main():
    """Главная функция"""
    try:
        await fix_avatar_statuses()
        print("\n✅ Исправление завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 