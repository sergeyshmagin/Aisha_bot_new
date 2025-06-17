#!/usr/bin/env python3
"""
Создание тестовых изображений для галереи
"""
import sys
import asyncio
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.append(str(Path(__file__).parent.parent.parent))

async def create_test_images():
    """Создает несколько тестовых изображений для галереи"""
    from app.core.database import get_session
    from app.database.models import ImageGeneration, GenerationStatus
    from app.services.generation.imagen4.imagen4_service import Imagen4Service
    from app.services.generation.imagen4.models import Imagen4Request, AspectRatio
    from app.services.generation.storage.image_storage import ImageStorage
    
    print("🎨 Создание тестовых изображений для галереи\n")
    print("=" * 60)
    
    # Список промптов для тестирования
    test_prompts = [
        ("Красивый закат над горами", "Beautiful sunset over mountains"),
        ("Кот играет с мячом", "Cat playing with a ball"),
        ("Космический пейзаж", "Space landscape"),
        ("Цветущий сад весной", "Blooming garden in spring"),
        ("Старинный замок", "Ancient castle"),
    ]
    
    aspect_ratios = [AspectRatio.SQUARE, AspectRatio.PORTRAIT_3_4, AspectRatio.LANDSCAPE_16_9]
    
    # Инициализируем сервисы
    try:
        service = Imagen4Service()
        storage = ImageStorage()
        
        if not service.is_available():
            print("❌ Сервис Imagen4 недоступен")
            return
            
        print(f"✅ Сервис готов, создаем {len(test_prompts)} изображений...\n")
        
        created_count = 0
        
        for i, (ru_prompt, en_prompt) in enumerate(test_prompts, 1):
            print(f"{i}. Создание: '{ru_prompt}'...")
            
            try:
                async with get_session() as session:
                    # Создаем запись в БД
                    generation = ImageGeneration(
                        user_id="2a293064-10d8-4103-9525-02335ab93f00",
                        generation_type="imagen4",
                        original_prompt=ru_prompt,
                        final_prompt=en_prompt,
                        aspect_ratio=aspect_ratios[i % len(aspect_ratios)].value,
                        status=GenerationStatus.PENDING
                    )
                    
                    session.add(generation)
                    await session.commit()
                    await session.refresh(generation)
                    
                    # Генерируем изображение
                    request = Imagen4Request(
                        prompt=en_prompt,
                        aspect_ratio=aspect_ratios[i % len(aspect_ratios)],
                        num_images=1
                    )
                    
                    result = await service.generate_image(request)
                    
                    if result.status.value == "completed":
                        # Сохраняем результат
                        image_urls = [img.url for img in result.response.images]
                        
                        generation.status = GenerationStatus.COMPLETED
                        generation.result_urls = image_urls
                        generation.metadata = {
                            "generation_time": result.generation_time,
                            "cost_credits": result.cost_credits,
                            "images_count": len(result.response.images)
                        }
                        
                        await session.commit()
                        
                        # Сохраняем в MinIO
                        try:
                            minio_urls = await storage.save_images_to_minio(generation, image_urls)
                            if minio_urls:
                                generation.result_urls = minio_urls
                                await session.commit()
                        except Exception as storage_error:
                            print(f"   ⚠️ Ошибка MinIO: {storage_error}")
                        
                        created_count += 1
                        print(f"   ✅ Создано успешно! ID: {generation.id}")
                        
                    else:
                        print(f"   ❌ Ошибка генерации: {result.error_message}")
                        generation.status = GenerationStatus.FAILED
                        generation.error_message = result.error_message
                        await session.commit()
                        
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
                
            # Небольшая пауза между запросами
            await asyncio.sleep(2)
        
        print(f"\n🎉 Создание завершено!")
        print(f"   ✅ Успешно создано: {created_count}/{len(test_prompts)} изображений")
        print(f"   📱 Теперь галерея должна содержать изображения")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_images()) 