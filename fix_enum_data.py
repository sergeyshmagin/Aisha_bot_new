#!/usr/bin/env python3
"""
Скрипт для исправления enum значений в БД
Приводит все enum к uppercase для совместимости с SQLAlchemy
"""
import asyncio
import asyncpg
from typing import Dict, List

# Настройки БД
DB_CONFIG = {
    'host': '192.168.0.4',
    'port': 5432,
    'user': 'aisha_user',
    'password': 'KbZZGJHX09KSH7r9ev4m',
    'database': 'aisha'
}


async def fix_enum_data():
    """Исправление enum данных в БД"""
    print("🔧 Начинаем исправление enum данных...")
    
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # 1. Исправляем avatargender: male -> MALE, female -> FEMALE
        print("\n📝 Исправляем avatargender...")
        
        # Проверяем текущие значения
        result = await conn.fetch("SELECT DISTINCT gender FROM avatars ORDER BY gender")
        print("Текущие значения gender:", [row['gender'] for row in result])
        
        # Исправляем lowercase на uppercase
        updated_male = await conn.execute("""
            UPDATE avatars 
            SET gender = 'MALE' 
            WHERE gender = 'male'
        """)
        print(f"✅ Исправлено 'male' -> 'MALE': {updated_male}")
        
        updated_female = await conn.execute("""
            UPDATE avatars 
            SET gender = 'FEMALE' 
            WHERE gender = 'female'
        """)
        print(f"✅ Исправлено 'female' -> 'FEMALE': {updated_female}")
        
        # 2. Исправляем avatarstatus
        print("\n📝 Исправляем avatarstatus...")
        
        # Проверяем текущие значения
        result = await conn.fetch("SELECT DISTINCT status FROM avatars ORDER BY status")
        print("Текущие значения status:", [row['status'] for row in result])
        
        # Мапинг для статусов
        status_mapping = {
            'draft': 'DRAFT',
            'photos_uploading': 'PHOTOS_UPLOADING',
            'ready_for_training': 'READY_FOR_TRAINING', 
            'training': 'TRAINING',
            'completed': 'COMPLETED',
            'error': 'ERROR',
            'cancelled': 'CANCELLED'
        }
        
        for old_status, new_status in status_mapping.items():
            updated = await conn.execute(f"""
                UPDATE avatars 
                SET status = '{new_status}' 
                WHERE status = '{old_status}'
            """)
            if updated != "UPDATE 0":
                print(f"✅ Исправлено '{old_status}' -> '{new_status}': {updated}")
        
        # 3. Исправляем generationstatus
        print("\n📝 Исправляем generationstatus...")
        
        # Проверяем текущие значения
        result = await conn.fetch("SELECT DISTINCT status FROM image_generations ORDER BY status")
        print("Текущие значения generation status:", [row['status'] for row in result])
        
        # Мапинг для статусов генерации
        gen_status_mapping = {
            'pending': 'PENDING',
            'processing': 'PROCESSING',
            'completed': 'COMPLETED',
            'failed': 'FAILED'
        }
        
        for old_status, new_status in gen_status_mapping.items():
            updated = await conn.execute(f"""
                UPDATE image_generations 
                SET status = '{new_status}' 
                WHERE status = '{old_status}'
            """)
            if updated != "UPDATE 0":
                print(f"✅ Исправлено '{old_status}' -> '{new_status}': {updated}")
        
        # 4. Проверяем финальное состояние
        print("\n🔍 Проверяем финальное состояние...")
        
        # Аватары
        avatar_genders = await conn.fetch("SELECT DISTINCT gender FROM avatars ORDER BY gender")
        avatar_statuses = await conn.fetch("SELECT DISTINCT status FROM avatars ORDER BY status")
        
        print("Финальные gender:", [row['gender'] for row in avatar_genders])
        print("Финальные avatar status:", [row['status'] for row in avatar_statuses])
        
        # Генерации
        gen_statuses = await conn.fetch("SELECT DISTINCT status FROM image_generations ORDER BY status")
        print("Финальные generation status:", [row['status'] for row in gen_statuses])
        
        print("\n✅ Исправление enum данных завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(fix_enum_data()) 