#!/usr/bin/env python3
"""
Скрипт для исправления поля avatar_id в таблице image_generations
Делает поле nullable для поддержки Imagen 4
"""

import asyncio
import sys
import os

# Добавляем корневой каталог в sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import async_engine
from app.core.logger import get_logger

logger = get_logger(__name__)

async def check_and_fix_avatar_id():
    """Проверяет и исправляет поле avatar_id"""
    
    try:
        async with async_engine.begin() as conn:
            # Проверяем текущую структуру
            result = await conn.execute(text("""
                SELECT column_name, is_nullable, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'image_generations' AND column_name = 'avatar_id'
            """))
            
            row = result.first()
            if row:
                print(f"✅ Текущее состояние поля avatar_id:")
                print(f"   Тип: {row.data_type}")
                print(f"   Nullable: {row.is_nullable}")
                
                if row.is_nullable == 'NO':
                    print("🔧 Исправляем поле avatar_id...")
                    
                    # Делаем поле nullable
                    await conn.execute(text("""
                        ALTER TABLE image_generations 
                        ALTER COLUMN avatar_id DROP NOT NULL
                    """))
                    
                    print("✅ Поле avatar_id теперь nullable!")
                    return True
                else:
                    print("✅ Поле avatar_id уже nullable")
                    return True
            else:
                print("❌ Поле avatar_id не найдено!")
                return False
                
    except Exception as e:
        logger.exception(f"❌ Ошибка при исправлении поля avatar_id: {e}")
        return False

async def test_insert():
    """Тестируем вставку записи с NULL avatar_id"""
    
    try:
        async with async_engine.begin() as conn:
            # Пробуем вставить тестовую запись
            await conn.execute(text("""
                INSERT INTO image_generations (
                    id, user_id, avatar_id, generation_type, source_model,
                    original_prompt, final_prompt, quality_preset, aspect_ratio,
                    num_images, status, result_urls, prompt_metadata,
                    is_favorite, is_saved, created_at
                ) VALUES (
                    gen_random_uuid(), '550e8400-e29b-41d4-a716-446655440000'::uuid, 
                    NULL, 'imagen4', 'imagen4',
                    'тест', 'тест', 'standard', '1:1',
                    1, 'PENDING', '[]'::json, '{}'::json,
                    false, true, NOW()
                )
            """))
            
            print("✅ Тестовая вставка с NULL avatar_id прошла успешно!")
            
            # Удаляем тестовую запись
            await conn.execute(text("""
                DELETE FROM image_generations 
                WHERE original_prompt = 'тест' AND generation_type = 'imagen4'
            """))
            
            return True
            
    except Exception as e:
        logger.exception(f"❌ Ошибка при тестовой вставке: {e}")
        return False

async def main():
    """Основная функция"""
    
    print("🔧 Исправление поля avatar_id для поддержки Imagen 4...")
    
    # Проверяем и исправляем поле
    if await check_and_fix_avatar_id():
        print("✅ Структура БД исправлена")
        
        # Тестируем
        if await test_insert():
            print("🎉 Imagen 4 готов к работе!")
            return True
        else:
            print("❌ Тест не прошел")
            return False
    else:
        print("❌ Не удалось исправить структуру БД")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1) 