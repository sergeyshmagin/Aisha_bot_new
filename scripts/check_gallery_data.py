#!/usr/bin/env python3
"""
Скрипт для проверки данных галереи
"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import get_session
from app.database.models import ImageGeneration, GenerationStatus
from sqlalchemy import select, func


async def check_gallery_data():
    """Проверяет данные галереи"""
    
    try:
        async with get_session() as session:
            # Общее количество изображений
            total_stmt = select(func.count(ImageGeneration.id)).where(
                ImageGeneration.status == GenerationStatus.COMPLETED,
                ImageGeneration.result_urls.isnot(None)
            )
            total_result = await session.execute(total_stmt)
            total_count = total_result.scalar()
            
            # Изображения с аватарами
            avatar_stmt = select(func.count(ImageGeneration.id)).where(
                ImageGeneration.status == GenerationStatus.COMPLETED,
                ImageGeneration.result_urls.isnot(None),
                ImageGeneration.avatar_id.isnot(None)
            )
            avatar_result = await session.execute(avatar_stmt)
            avatar_count = avatar_result.scalar()
            
            # Изображения без аватаров (Imagen4)
            imagen4_stmt = select(func.count(ImageGeneration.id)).where(
                ImageGeneration.status == GenerationStatus.COMPLETED,
                ImageGeneration.result_urls.isnot(None),
                ImageGeneration.avatar_id.is_(None)
            )
            imagen4_result = await session.execute(imagen4_stmt)
            imagen4_count = imagen4_result.scalar()
            
            print("📊 Статистика изображений в галерее:")
            print(f"   Всего завершенных: {total_count}")
            print(f"   С аватарами (фото со мной): {avatar_count}")
            print(f"   Imagen4 (изображения): {imagen4_count}")
            
            if total_count == 0:
                print("\n⚠️  В базе нет завершенных изображений для тестирования фильтров")
            else:
                print(f"\n✅ Данные для тестирования фильтров готовы!")
                
    except Exception as e:
        print(f"❌ Ошибка при проверке данных: {e}")


if __name__ == "__main__":
    asyncio.run(check_gallery_data()) 