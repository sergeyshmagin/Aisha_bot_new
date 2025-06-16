#!/usr/bin/env python3
"""
Очистка тестовых записей Imagen4 из базы данных
"""
import sys
import asyncio
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import get_session
from app.database.models import ImageGeneration, User, GenerationStatus
from sqlalchemy import select, delete
from app.core.logger import get_logger

logger = get_logger(__name__)

async def cleanup_test_imagen4():
    """Удаляет тестовые записи Imagen4 из базы данных"""
    
    print("🧹 ОЧИСТКА ТЕСТОВЫХ ЗАПИСЕЙ IMAGEN4")
    print("=" * 50)
    
    try:
        async with get_session() as session:
            # Находим пользователя Sergey
            sergey_stmt = select(User).where(User.telegram_id == "174171680")
            sergey_result = await session.execute(sergey_stmt)
            sergey = sergey_result.scalar_one_or_none()
            
            if not sergey:
                print("❌ Пользователь Sergey не найден")
                return
            
            print(f"👤 Пользователь: {sergey.first_name} (ID: {sergey.id})")
            
            # Находим все изображения Imagen4 пользователя
            all_imagen4_stmt = select(ImageGeneration).where(
                ImageGeneration.user_id == sergey.id,
                ImageGeneration.generation_type == 'imagen4'
            ).order_by(ImageGeneration.created_at.desc())
            
            all_result = await session.execute(all_imagen4_stmt)
            all_images = all_result.scalars().all()
            
            print(f"\n📊 НАЙДЕНО {len(all_images)} ИЗОБРАЖЕНИЙ IMAGEN4:")
            print("-" * 60)
            
            # Разделяем на категории
            test_images = []  # Тестовые изображения для удаления
            real_images = []  # Реальные изображения для сохранения
            
            for i, img in enumerate(all_images, 1):
                print(f"{i:2d}. 📝 {img.original_prompt[:40] if img.original_prompt else 'Без промпта'}...")
                print(f"    🆔 ID: {img.id}")
                print(f"    📅 Создано: {img.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"    📊 Статус: {img.status}")
                print(f"    🌐 URL: {img.result_urls}")
                
                # Определяем тестовые изображения по характеристикам
                is_test = False
                
                # Тестовые признаки:
                # 1. Содержат fal-cdn URL (наши замененные тестовые)
                if img.result_urls and any('fal-cdn.batuhan-941.workers.dev' in url for url in img.result_urls):
                    is_test = True
                    print(f"    🔍 ТЕСТОВЫЙ: содержит fal-cdn URL")
                
                # 2. Промпты на английском (старые тестовые)
                elif img.original_prompt and img.original_prompt.lower().startswith(('beautiful', 'futuristic', 'peaceful', 'abstract', 'vintage')):
                    is_test = True
                    print(f"    🔍 ТЕСТОВЫЙ: английский промпт")
                
                # 3. Отсутствует время генерации (тестовые не имеют реального времени)
                elif not img.generation_time:
                    is_test = True
                    print(f"    🔍 ТЕСТОВЫЙ: нет времени генерации")
                
                if is_test:
                    test_images.append(img)
                    print(f"    ❌ ПОМЕЧЕН ДЛЯ УДАЛЕНИЯ")
                else:
                    real_images.append(img)
                    print(f"    ✅ СОХРАНИТЬ")
                
                print()
            
            print(f"📈 ИТОГОВАЯ СТАТИСТИКА:")
            print(f"   ✅ Реальные изображения: {len(real_images)}")
            print(f"   ❌ Тестовые для удаления: {len(test_images)}")
            
            if not test_images:
                print(f"\n🎉 Тестовых изображений не найдено!")
                return
            
            print(f"\n📋 ИЗОБРАЖЕНИЯ ДЛЯ УДАЛЕНИЯ:")
            for i, img in enumerate(test_images, 1):
                print(f"   {i}. {img.original_prompt[:50] if img.original_prompt else 'Без промпта'}...")
                print(f"      ID: {img.id}")
                print(f"      Создано: {img.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Запрашиваем подтверждение
            print(f"\n⚠️  ВНИМАНИЕ!")
            print(f"   Будет удалено {len(test_images)} тестовых изображений Imagen4")
            print(f"   Останется {len(real_images)} реальных изображений")
            print(f"   Операция необратима!")
            
            confirm = input(f"\n❓ Продолжить удаление? (yes/NO): ").strip()
            
            if confirm.lower() not in ['yes', 'да']:
                print(f"❌ Операция отменена")
                return
            
            # Удаляем тестовые изображения
            deleted_count = 0
            for img in test_images:
                try:
                    await session.delete(img)
                    deleted_count += 1
                    print(f"🗑️  Удалено: {img.original_prompt[:40]}... (ID: {img.id})")
                except Exception as e:
                    print(f"❌ Ошибка удаления ID {img.id}: {e}")
            
            # Сохраняем изменения
            await session.commit()
            
            print(f"\n🎉 ОЧИСТКА ЗАВЕРШЕНА!")
            print(f"   ✅ Удалено тестовых изображений: {deleted_count}")
            print(f"   🔄 Осталось реальных изображений: {len(real_images)}")
            
            # Проверяем финальное состояние
            final_stmt = select(ImageGeneration).where(
                ImageGeneration.user_id == sergey.id,
                ImageGeneration.generation_type == 'imagen4'
            )
            final_result = await session.execute(final_stmt)
            final_images = final_result.scalars().all()
            
            print(f"   📊 Всего изображений Imagen4 в базе: {len(final_images)}")
            
            if len(final_images) == 0:
                print(f"   💡 Теперь можете создавать новые изображения Imagen4!")
            else:
                print(f"   💡 Оставшиеся изображения:")
                for img in final_images:
                    print(f"      - {img.original_prompt[:40]}... ({img.created_at.strftime('%Y-%m-%d')})")
                
    except Exception as e:
        logger.exception(f"Ошибка очистки: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(cleanup_test_imagen4()) 