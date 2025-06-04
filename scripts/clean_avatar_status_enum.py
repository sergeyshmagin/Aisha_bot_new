#!/usr/bin/env python3
"""
Скрипт для очистки ENUM avatarstatus от дублированных значений

Сначала обновляет все UPPERCASE статусы на lowercase,
затем удаляет дублированные UPPERCASE значения из enum.

Использование:
    python scripts/clean_avatar_status_enum.py
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_session
from sqlalchemy import text

async def update_avatar_statuses():
    """Обновляет статусы аватаров с UPPERCASE на lowercase"""
    
    print("🔧 Обновление статусов аватаров...")
    
    # Маппинг UPPERCASE -> lowercase
    status_mapping = {
        'DRAFT': 'draft',
        'PHOTOS_UPLOADING': 'photos_uploading', 
        'READY_FOR_TRAINING': 'ready_for_training',
        'TRAINING': 'training',
        'COMPLETED': 'completed',
        'ERROR': 'error',
        'CANCELLED': 'cancelled'
    }
    
    async with get_session() as session:
        total_updated = 0
        
        for old_status, new_status in status_mapping.items():
            try:
                # Обновляем аватары с UPPERCASE статусом
                query = text("""
                    UPDATE avatars 
                    SET status = :new_status 
                    WHERE status = :old_status
                """)
                
                result = await session.execute(
                    query, 
                    {"old_status": old_status, "new_status": new_status}
                )
                
                updated_count = result.rowcount
                if updated_count > 0:
                    print(f"✅ Обновлено {updated_count} аватаров: {old_status} -> {new_status}")
                    total_updated += updated_count
                
            except Exception as e:
                print(f"⚠️  Ошибка обновления {old_status}: {e}")
                await session.rollback()
                return False
        
        await session.commit()
        print(f"📊 Всего обновлено статусов: {total_updated}")
        return True

async def clean_enum_values():
    """
    ОСТОРОЖНО: Удаляет UPPERCASE значения из enum.
    Работает только если все записи в БД уже используют lowercase значения.
    """
    
    print("\n🧹 Очистка ENUM от дублированных значений...")
    
    # Значения для удаления
    values_to_remove = [
        'DRAFT', 'PHOTOS_UPLOADING', 'READY_FOR_TRAINING', 
        'TRAINING', 'COMPLETED', 'ERROR', 'CANCELLED'
    ]
    
    async with get_session() as session:
        try:
            # Проверяем, что нет записей с UPPERCASE статусами
            for value in values_to_remove:
                check_query = text("SELECT COUNT(*) FROM avatars WHERE status = :status")
                result = await session.execute(check_query, {"status": value})
                count = result.scalar()
                
                if count > 0:
                    print(f"❌ НЕЛЬЗЯ удалить {value} - {count} записей еще используют это значение!")
                    return False
            
            print("✅ Все UPPERCASE значения можно безопасно удалить")
            
            # Удаляем UPPERCASE значения (PostgreSQL не поддерживает DROP VALUE напрямую)
            # Придется пересоздать enum
            
            # 1. Создаем новый временный enum
            await session.execute(text("""
                CREATE TYPE avatarstatus_new AS ENUM (
                    'draft', 'photos_uploading', 'ready_for_training',
                    'training', 'completed', 'error', 'cancelled'
                )
            """))
            
            # 2. Обновляем колонку на новый тип
            await session.execute(text("""
                ALTER TABLE avatars 
                ALTER COLUMN status TYPE avatarstatus_new 
                USING status::text::avatarstatus_new
            """))
            
            # 3. Удаляем старый enum
            await session.execute(text("DROP TYPE avatarstatus"))
            
            # 4. Переименовываем новый enum
            await session.execute(text("ALTER TYPE avatarstatus_new RENAME TO avatarstatus"))
            
            await session.commit()
            print("✅ ENUM очищен от дублированных значений")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка очистки ENUM: {e}")
            await session.rollback()
            return False

async def check_final_state():
    """Проверяет финальное состояние enum и данных"""
    
    print("\n📊 Финальная проверка...")
    
    async with get_session() as session:
        # Проверяем значения enum
        query = text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'avatarstatus')
            ORDER BY enumlabel
        """)
        
        result = await session.execute(query)
        enum_values = result.fetchall()
        
        print("🔍 Значения ENUM avatarstatus:")
        for row in enum_values:
            print(f"  • {row.enumlabel}")
        
        # Проверяем статусы в БД
        query = text("""
            SELECT status, COUNT(*) as count
            FROM avatars
            GROUP BY status
            ORDER BY count DESC
        """)
        
        result = await session.execute(query)
        status_counts = result.fetchall()
        
        print("\n📊 Статистика по статусам:")
        for row in status_counts:
            print(f"  {row.status}: {row.count} аватаров")

async def main():
    """Главная функция"""
    try:
        print("🚀 Очистка ENUM avatarstatus от дублированных значений")
        print("=" * 60)
        
        # 1. Обновляем статусы в БД
        success = await update_avatar_statuses()
        if not success:
            print("❌ Ошибка обновления статусов")
            return
        
        # 2. Очищаем enum
        success = await clean_enum_values()
        if not success:
            print("❌ Ошибка очистки ENUM")
            return
        
        # 3. Проверяем результат
        await check_final_state()
        
        print("\n✅ Очистка ENUM завершена успешно!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 