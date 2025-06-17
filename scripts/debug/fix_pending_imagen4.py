#!/usr/bin/env python3
"""
Исправление PENDING генераций Imagen4
"""
import sys
import asyncio
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.append(str(Path(__file__).parent.parent.parent))

async def fix_pending_imagen4():
    """Исправляет PENDING генерации Imagen4"""
    from app.core.database import get_session
    from app.database.models import ImageGeneration, GenerationStatus
    from sqlalchemy import select, and_
    from datetime import datetime, timezone
    
    async with get_session() as session:
        # Ищем PENDING Imagen4 генерации
        stmt = select(ImageGeneration).where(
            and_(
                ImageGeneration.generation_type == 'imagen4',
                ImageGeneration.status == GenerationStatus.PENDING
            )
        ).order_by(ImageGeneration.created_at.desc())
        
        result = await session.execute(stmt)
        pending_generations = result.scalars().all()
        
        print(f"🔍 Найдено PENDING генераций Imagen4: {len(pending_generations)}")
        
        if not pending_generations:
            print("✅ Все генерации Imagen4 в порядке")
            return
        
        for generation in pending_generations:
            print(f"\n📋 Генерация {generation.id}:")
            print(f"   📅 Создана: {generation.created_at}")
            print(f"   📝 Промпт: {generation.original_prompt[:50]}...")
            print(f"   📊 Статус: {generation.status}")
            print(f"   🔗 URLs: {generation.result_urls}")
            
            # Проверяем возраст генерации
            if generation.created_at:
                age = datetime.now() - generation.created_at.replace(tzinfo=None)
                age_minutes = age.total_seconds() / 60
                
                print(f"   ⏱  Возраст: {age_minutes:.1f} минут")
                
                # Если генерация старше 30 минут, считаем её зависшей
                if age_minutes > 30:
                    print(f"   ❌ Генерация зависла - удаляем")
                    await session.delete(generation)
                elif age_minutes > 10:
                    print(f"   ⚠️  Генерация долго обрабатывается")
                else:
                    print(f"   ⏳ Генерация в процессе")
        
        # Подтверждение
        choice = input(f"\n❓ Удалить {len([g for g in pending_generations if (datetime.now() - g.created_at.replace(tzinfo=None)).total_seconds() / 60 > 30])} зависших генераций? (y/N): ").strip().lower()
        
        if choice in ['y', 'yes', 'да', 'д']:
            await session.commit()
            print("✅ Зависшие генерации удалены")
        else:
            await session.rollback()
            print("❌ Операция отменена")

async def check_imagen4_buckets():
    """Проверяет конфигурацию bucket'ов для Imagen4"""
    from app.core.config import settings
    from app.services.storage.minio import MinioStorage
    
    print(f"\n🗄️  ПРОВЕРКА КОНФИГУРАЦИИ MINIO:")
    print(f"   🌐 Endpoint: {settings.MINIO_ENDPOINT}")
    print(f"   🔑 Access Key: {settings.MINIO_ACCESS_KEY[:5]}...")
    print(f"   📦 Imagen4 Bucket: {getattr(settings, 'MINIO_BUCKET_IMAGEN4', 'НЕ УСТАНОВЛЕНО')}")
    print(f"   📦 Photos Bucket: {getattr(settings, 'MINIO_BUCKET_PHOTOS', 'НЕ УСТАНОВЛЕНО')}")
    
    try:
        storage = MinioStorage()
        
        # Проверяем доступность bucket'ов
        buckets_to_check = ['imagen4', 'generated']
        
        for bucket in buckets_to_check:
            try:
                # Пробуем создать тестовый файл
                test_data = b"test"
                test_path = f"test/{bucket}_test.txt"
                
                await storage.upload_file(bucket, test_path, test_data, "text/plain")
                
                # Удаляем тестовый файл
                await storage.delete_file(bucket, test_path)
                
                print(f"   ✅ Bucket '{bucket}' доступен")
                
            except Exception as e:
                print(f"   ❌ Bucket '{bucket}' недоступен: {e}")
                
    except Exception as e:
        print(f"   ❌ Ошибка подключения к MinIO: {e}")

if __name__ == "__main__":
    print("🔧 Исправление PENDING генераций Imagen4\n")
    print("=" * 60)
    
    asyncio.run(fix_pending_imagen4())
    asyncio.run(check_imagen4_buckets())
    
    print("\n" + "=" * 60)
    print("🎉 Проверка завершена!") 