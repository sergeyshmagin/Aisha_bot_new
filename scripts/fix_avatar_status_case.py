#!/usr/bin/env python3
"""
Скрипт для исправления регистра статусов аватаров

Конвертирует UPPERCASE статусы в lowercase для соответствия коду.

Использование:
    python scripts/fix_avatar_status_case.py --check    # Только проверка
    python scripts/fix_avatar_status_case.py --fix     # Исправление
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_session
from app.core.config import settings
from sqlalchemy import text

async def check_avatar_statuses():
    """Проверяет текущие статусы аватаров"""
    
    print("🔍 Проверка статусов аватаров...")
    
    async with get_session() as session:
        # Получаем статистику по статусам
        query = text("""
            SELECT status, COUNT(*) as count
            FROM avatars
            GROUP BY status
            ORDER BY count DESC
        """)
        
        result = await session.execute(query)
        status_counts = result.fetchall()
        
        print("📊 Текущие статусы:")
        for row in status_counts:
            case_type = "UPPERCASE" if row.status.isupper() else "lowercase"
            print(f"  {row.status} ({case_type}): {row.count} аватаров")
        
        # Проверяем проблемные аватары
        uppercase_query = text("""
            SELECT id, name, status 
            FROM avatars 
            WHERE status != LOWER(status)
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        result = await session.execute(uppercase_query)
        problematic_avatars = result.fetchall()
        
        if problematic_avatars:
            print(f"\n⚠️  Найдено {len(problematic_avatars)} аватаров с UPPERCASE статусами:")
            for avatar in problematic_avatars:
                print(f"  ID: {avatar.id}, Имя: {avatar.name}, Статус: {avatar.status}")
        else:
            print("\n✅ Все статусы в правильном регистре!")
        
        return len(problematic_avatars)

async def fix_avatar_statuses():
    """Исправляет регистр статусов аватаров"""
    
    print("🔧 Исправление регистра статусов...")
    
    async with get_session() as session:
        # Конвертируем все UPPERCASE статусы в lowercase
        query = text("""
            UPDATE avatars 
            SET status = LOWER(status)
            WHERE status != LOWER(status)
        """)
        
        result = await session.execute(query)
        updated_count = result.rowcount
        await session.commit()
        
        print(f"✅ Обновлено {updated_count} аватаров")
        
        return updated_count

async def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Исправление регистра статусов аватаров')
    parser.add_argument('--check', action='store_true', help='Только проверить статусы')
    parser.add_argument('--fix', action='store_true', help='Исправить проблемные статусы')
    
    args = parser.parse_args()
    
    if not args.check and not args.fix:
        parser.print_help()
        return
    
    try:
        if args.check:
            problematic_count = await check_avatar_statuses()
            if problematic_count > 0:
                print(f"\n💡 Для исправления запустите: python scripts/fix_avatar_status_case.py --fix")
        
        elif args.fix:
            problematic_count = await check_avatar_statuses()
            if problematic_count > 0:
                print()
                updated_count = await fix_avatar_statuses()
                print()
                await check_avatar_statuses()
            else:
                print("\n✅ Исправления не требуются!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 