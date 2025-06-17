#!/usr/bin/env python3
"""
Проверка изображений пользователя в базе данных
"""
import sys
import asyncio
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.append(str(Path(__file__).parent.parent.parent))

async def check_user_images():
    """Проверяет изображения пользователя в базе данных"""
    from app.core.database import get_session
    from app.database.models import ImageGeneration
    from sqlalchemy import select, and_, func
    
    async with get_session() as session:
        # Проверяем общую статистику
        total_stmt = select(func.count(ImageGeneration.id)).where(
            ImageGeneration.user_id == '2a293064-10d8-4103-9525-02335ab93f00'
        )
        total_result = await session.execute(total_stmt)
        total_count = total_result.scalar()
        
        # Проверяем по типам
        imagen4_stmt = select(func.count(ImageGeneration.id)).where(
            and_(
                ImageGeneration.user_id == '2a293064-10d8-4103-9525-02335ab93f00',
                ImageGeneration.generation_type == 'imagen4'
            )
        )
        imagen4_result = await session.execute(imagen4_stmt)
        imagen4_count = imagen4_result.scalar()
        
        # Проверяем avatar
        avatar_stmt = select(func.count(ImageGeneration.id)).where(
            and_(
                ImageGeneration.user_id == '2a293064-10d8-4103-9525-02335ab93f00',
                ImageGeneration.generation_type == 'avatar'
            )
        )
        avatar_result = await session.execute(avatar_stmt)
        avatar_count = avatar_result.scalar()
        
        print(f"📊 СТАТИСТИКА ИЗОБРАЖЕНИЙ ПОЛЬЗОВАТЕЛЯ:")
        print(f"   📝 Всего: {total_count}")
        print(f"   🎨 Imagen4: {imagen4_count}")
        print(f"   👤 Avatar: {avatar_count}")
        print()
        
        # Проверяем последние изображения каждого типа
        print("🖼️  ПОСЛЕДНИЕ IMAGEN4 ИЗОБРАЖЕНИЯ:")
        imagen4_images_stmt = select(ImageGeneration).where(
            and_(
                ImageGeneration.user_id == '2a293064-10d8-4103-9525-02335ab93f00',
                ImageGeneration.generation_type == 'imagen4',
                ImageGeneration.result_urls.isnot(None)
            )
        ).order_by(ImageGeneration.created_at.desc()).limit(5)
        
        result = await session.execute(imagen4_images_stmt)
        imagen4_images = result.scalars().all()
        
        if not imagen4_images:
            print("   ❌ Imagen4 изображения не найдены")
        else:
            for i, img in enumerate(imagen4_images, 1):
                print(f"   {i}. ID: {img.id}")
                print(f"      📅 Дата: {img.created_at}")
                print(f"      📝 Промпт: {img.original_prompt[:50]}...")
                print(f"      🔗 URL: {img.result_urls[:100] if img.result_urls else 'Нет'}...")
                print(f"      📊 Статус: {img.status}")
                print()
        
        # Проверяем проблемные записи
        print("🔍 ПРОБЛЕМНЫЕ ЗАПИСИ:")
        problem_stmt = select(ImageGeneration).where(
            and_(
                ImageGeneration.user_id == '2a293064-10d8-4103-9525-02335ab93f00',
                ImageGeneration.generation_type == 'imagen4'
            )
        ).order_by(ImageGeneration.created_at.desc())
        
        result = await session.execute(problem_stmt)
        all_imagen4 = result.scalars().all()
        
        for img in all_imagen4:
            if not img.result_urls or 'example.com' in str(img.result_urls):
                print(f"   ❌ Проблема с {img.id}:")
                print(f"      📅 Дата: {img.created_at}")
                print(f"      📊 Статус: {img.status}")
                print(f"      🔗 URLs: {img.result_urls}")
                print()

if __name__ == "__main__":
    asyncio.run(check_user_images()) 