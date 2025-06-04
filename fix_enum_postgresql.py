#!/usr/bin/env python3
"""
Скрипт для исправления enum типов в PostgreSQL
1. Обновляет enum определения, добавляя uppercase значения
2. Мигрирует данные на uppercase
3. Удаляет старые lowercase значения
"""
import asyncio
import asyncpg

# Настройки БД
DB_CONFIG = {
    'host': '192.168.0.4',
    'port': 5432,
    'user': 'aisha_user',
    'password': 'KbZZGJHX09KSH7r9ev4m',
    'database': 'aisha'
}


async def fix_postgresql_enums():
    """Исправление enum типов в PostgreSQL"""
    print("🔧 Начинаем исправление PostgreSQL enum типов...")
    
    conn = await asyncpg.connect(**DB_CONFIG)
    
    try:
        # 1. AVATARGENDER enum
        print("\n📝 Исправляем avatargender enum...")
        
        # Проверяем текущие значения enum
        result = await conn.fetch("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'avatargender')
            ORDER BY enumsortorder
        """)
        current_values = [row['enumlabel'] for row in result]
        print("Текущие значения avatargender:", current_values)
        
        # Добавляем uppercase значения если их нет
        if 'MALE' not in current_values:
            await conn.execute("ALTER TYPE avatargender ADD VALUE 'MALE'")
            print("✅ Добавлено значение 'MALE'")
            
        if 'FEMALE' not in current_values:
            await conn.execute("ALTER TYPE avatargender ADD VALUE 'FEMALE'")
            print("✅ Добавлено значение 'FEMALE'")
        
        # Мигрируем данные
        updated_male = await conn.execute("UPDATE avatars SET gender = 'MALE' WHERE gender = 'male'")
        print(f"✅ Мигрировано 'male' -> 'MALE': {updated_male}")
        
        updated_female = await conn.execute("UPDATE avatars SET gender = 'FEMALE' WHERE gender = 'female'")
        print(f"✅ Мигрировано 'female' -> 'FEMALE': {updated_female}")
        
        # 2. AVATARSTATUS enum
        print("\n📝 Исправляем avatarstatus enum...")
        
        result = await conn.fetch("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'avatarstatus')
            ORDER BY enumsortorder
        """)
        current_statuses = [row['enumlabel'] for row in result]
        print("Текущие значения avatarstatus:", current_statuses)
        
        # Мапинг статусов
        status_pairs = [
            ('draft', 'DRAFT'),
            ('photos_uploading', 'PHOTOS_UPLOADING'),
            ('ready_for_training', 'READY_FOR_TRAINING'),
            ('training', 'TRAINING'),
            ('completed', 'COMPLETED'),
            ('error', 'ERROR'),
            ('cancelled', 'CANCELLED')
        ]
        
        # Добавляем uppercase значения
        for lowercase, uppercase in status_pairs:
            if uppercase not in current_statuses:
                await conn.execute(f"ALTER TYPE avatarstatus ADD VALUE '{uppercase}'")
                print(f"✅ Добавлено значение '{uppercase}'")
        
        # Мигрируем данные
        for lowercase, uppercase in status_pairs:
            if lowercase in current_statuses:
                updated = await conn.execute(f"UPDATE avatars SET status = '{uppercase}' WHERE status = '{lowercase}'")
                if updated != "UPDATE 0":
                    print(f"✅ Мигрировано '{lowercase}' -> '{uppercase}': {updated}")
        
        # 3. GENERATIONSTATUS enum
        print("\n📝 Исправляем generationstatus enum...")
        
        result = await conn.fetch("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'generationstatus')
            ORDER BY enumsortorder
        """)
        current_gen_statuses = [row['enumlabel'] for row in result]
        print("Текущие значения generationstatus:", current_gen_statuses)
        
        # Мапинг статусов генерации
        gen_status_pairs = [
            ('pending', 'PENDING'),
            ('processing', 'PROCESSING'),
            ('completed', 'COMPLETED'),
            ('failed', 'FAILED')
        ]
        
        # Добавляем uppercase значения
        for lowercase, uppercase in gen_status_pairs:
            if uppercase not in current_gen_statuses:
                await conn.execute(f"ALTER TYPE generationstatus ADD VALUE '{uppercase}'")
                print(f"✅ Добавлено значение '{uppercase}'")
        
        # Мигрируем данные
        for lowercase, uppercase in gen_status_pairs:
            if lowercase in current_gen_statuses:
                updated = await conn.execute(f"UPDATE image_generations SET status = '{uppercase}' WHERE status = '{lowercase}'")
                if updated != "UPDATE 0":
                    print(f"✅ Мигрировано '{lowercase}' -> '{uppercase}': {updated}")
        
        # 4. Проверяем финальное состояние
        print("\n🔍 Проверяем финальное состояние...")
        
        # Данные в таблицах
        avatar_genders = await conn.fetch("SELECT DISTINCT gender FROM avatars ORDER BY gender")
        avatar_statuses = await conn.fetch("SELECT DISTINCT status FROM avatars ORDER BY status")
        gen_statuses = await conn.fetch("SELECT DISTINCT status FROM image_generations ORDER BY status")
        
        print("Финальные gender в данных:", [row['gender'] for row in avatar_genders])
        print("Финальные avatar status в данных:", [row['status'] for row in avatar_statuses])
        print("Финальные generation status в данных:", [row['status'] for row in gen_statuses])
        
        # Enum определения
        avatar_gender_enum = await conn.fetch("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'avatargender')
            ORDER BY enumsortorder
        """)
        print("Финальные значения avatargender enum:", [row['enumlabel'] for row in avatar_gender_enum])
        
        print("\n✅ Исправление PostgreSQL enum завершено!")
        print("🔄 Перезапустите приложение для обновления кеша SQLAlchemy")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(fix_postgresql_enums()) 