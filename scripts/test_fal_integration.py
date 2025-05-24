#!/usr/bin/env python3
"""
Скрипт тестирования FAL AI интеграции
"""
import asyncio
import sys
import os
from pathlib import Path
from uuid import uuid4, UUID
from datetime import datetime

# Добавляем путь к приложению
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.logger import get_logger
from app.core.database import get_session
from app.services.fal.client import FalAIClient
from app.services.avatar.training_service import AvatarTrainingService
from app.database.models import Avatar, AvatarStatus, AvatarType, AvatarGender

logger = get_logger(__name__)


async def test_fal_client():
    """Тестирует FAL AI клиент"""
    print("\n🧪 === ТЕСТИРОВАНИЕ FAL AI КЛИЕНТА ===")
    
    client = FalAIClient()
    
    # 1. Проверяем конфигурацию
    print(f"✅ Тестовый режим: {client.test_mode}")
    print(f"✅ API ключ установлен: {client.is_available()}")
    
    config = client.get_config_summary()
    print(f"📋 Конфигурация: {config}")
    
    # 2. Тестируем обучение аватара (в тестовом режиме)
    test_user_id = uuid4()
    test_avatar_id = uuid4()
    test_photo_urls = [
        "test/photo1.jpg",
        "test/photo2.jpg", 
        "test/photo3.jpg"
    ]
    
    print(f"\n🚀 Тестируем запуск обучения...")
    print(f"User ID: {test_user_id}")
    print(f"Avatar ID: {test_avatar_id}")
    print(f"Фотографий: {len(test_photo_urls)}")
    
    try:
        finetune_id = await client.train_avatar(
            user_id=test_user_id,
            avatar_id=test_avatar_id,
            name="Тестовый аватар",
            gender="male",
            photo_urls=test_photo_urls
        )
        
        print(f"✅ Обучение запущено! Finetune ID: {finetune_id}")
        
        # 3. Тестируем получение статуса
        print(f"\n📊 Тестируем получение статуса...")
        status = await client.get_training_status(finetune_id)
        print(f"Статус: {status}")
        
        # 4. Тестируем генерацию (мок)
        print(f"\n🎨 Тестируем генерацию изображения...")
        image_url = await client.generate_image(
            finetune_id=finetune_id,
            prompt="portrait of TOK person, professional photo"
        )
        print(f"Сгенерированное изображение: {image_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        logger.exception("Ошибка в test_fal_client")
        return False


async def test_training_service():
    """Тестирует сервис обучения аватаров"""
    print("\n🧪 === ТЕСТИРОВАНИЕ СЕРВИСА ОБУЧЕНИЯ ===")
    
    async with get_session() as session:
        training_service = AvatarTrainingService(session)
        
        # 1. Создаем тестовый аватар
        test_user_id = uuid4()
        test_avatar_id = uuid4()
        
        # Создаем аватар в БД (минимальная запись)
        test_avatar = Avatar(
            id=test_avatar_id,
            user_id=test_user_id,
            name="Тестовый аватар для обучения",
            avatar_type=AvatarType.CHARACTER,
            gender=AvatarGender.MALE,
            status=AvatarStatus.READY_FOR_TRAINING
        )
        
        session.add(test_avatar)
        await session.commit()
        print(f"✅ Создан тестовый аватар: {test_avatar_id}")
        
        try:
            # 2. Тестируем получение прогресса
            print(f"\n📊 Тестируем получение прогресса...")
            progress = await training_service.get_training_progress(test_avatar_id)
            print(f"Прогресс: {progress}")
            
            # 3. Тестируем обработку webhook
            print(f"\n📨 Тестируем обработку webhook...")
            webhook_data = {
                "finetune_id": "test_finetune_123",
                "status": "completed",
                "progress": 100,
                "message": "Training completed successfully"
            }
            
            # Сначала обновляем аватар с finetune_id
            await training_service._save_training_info(
                test_avatar_id, 
                "test_finetune_123"
            )
            
            webhook_result = await training_service.handle_webhook(webhook_data)
            print(f"Webhook обработан: {webhook_result}")
            
            # 4. Проверяем обновленный статус
            updated_progress = await training_service.get_training_progress(test_avatar_id)
            print(f"Обновленный прогресс: {updated_progress}")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования сервиса: {e}")
            logger.exception("Ошибка в test_training_service")
            return False
        
        finally:
            # Очищаем тестовые данные
            await session.delete(test_avatar)
            await session.commit()
            print(f"🧹 Тестовый аватар удален")


async def test_webhook_simulation():
    """Симулирует работу webhook"""
    print("\n🧪 === СИМУЛЯЦИЯ WEBHOOK ===")
    
    # Тестовые данные webhook от FAL AI
    webhook_examples = [
        {
            "finetune_id": "test_webhook_1",
            "status": "queued",
            "progress": 0,
            "message": "Training queued"
        },
        {
            "finetune_id": "test_webhook_1", 
            "status": "in_progress",
            "progress": 30,
            "message": "Training in progress"
        },
        {
            "finetune_id": "test_webhook_1",
            "status": "in_progress", 
            "progress": 75,
            "message": "Training almost complete"
        },
        {
            "finetune_id": "test_webhook_1",
            "status": "completed",
            "progress": 100,
            "message": "Training completed successfully"
        }
    ]
    
    async with get_session() as session:
        training_service = AvatarTrainingService(session)
        
        # Создаем тестовый аватар для webhook
        test_user_id = uuid4()
        test_avatar_id = uuid4()
        
        test_avatar = Avatar(
            id=test_avatar_id,
            user_id=test_user_id,
            name="Webhook тест аватар",
            avatar_type=AvatarType.CHARACTER,
            gender=AvatarGender.FEMALE,
            status=AvatarStatus.TRAINING,
            finetune_id="test_webhook_1"
        )
        
        session.add(test_avatar)
        await session.commit()
        print(f"✅ Создан тестовый аватар для webhook: {test_avatar_id}")
        
        try:
            # Обрабатываем каждый webhook
            for i, webhook_data in enumerate(webhook_examples, 1):
                print(f"\n📨 Webhook {i}/4: {webhook_data['status']} ({webhook_data['progress']}%)")
                
                result = await training_service.handle_webhook(webhook_data)
                print(f"   Результат: {result}")
                
                # Показываем обновленный прогресс
                progress = await training_service.get_training_progress(test_avatar_id)
                print(f"   Статус аватара: {progress['status']}, прогресс: {progress['progress']}%")
                
                await asyncio.sleep(0.5)  # Имитация интервала между webhook
            
            print(f"\n✅ Все webhook обработаны успешно!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка симуляции webhook: {e}")
            logger.exception("Ошибка в test_webhook_simulation")
            return False
            
        finally:
            # Очищаем тестовые данные
            await session.delete(test_avatar)
            await session.commit()
            print(f"🧹 Тестовый аватар удален")


async def main():
    """Основная функция тестирования"""
    print("🎯 === ТЕСТИРОВАНИЕ FAL AI ИНТЕГРАЦИИ ===")
    print(f"Режим: {'TEST MODE ✅' if settings.AVATAR_TEST_MODE else 'PRODUCTION ⚠️'}")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 1. Тест FAL клиента
    try:
        result1 = await test_fal_client()
        results.append(("FAL Client", result1))
    except Exception as e:
        print(f"❌ Критическая ошибка в тесте FAL клиента: {e}")
        results.append(("FAL Client", False))
    
    # 2. Тест сервиса обучения
    try:
        result2 = await test_training_service()
        results.append(("Training Service", result2))
    except Exception as e:
        print(f"❌ Критическая ошибка в тесте сервиса обучения: {e}")
        results.append(("Training Service", False))
    
    # 3. Тест webhook симуляции
    try:
        result3 = await test_webhook_simulation()
        results.append(("Webhook Simulation", result3))
    except Exception as e:
        print(f"❌ Критическая ошибка в тесте webhook: {e}")
        results.append(("Webhook Simulation", False))
    
    # Итоговый отчет
    print(f"\n🏁 === ИТОГОВЫЙ ОТЧЕТ ===")
    all_passed = True
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print(f"\n{'🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!' if all_passed else '⚠️ ЕСТЬ ПРОБЛЕМЫ В ТЕСТАХ'}")
    
    if all_passed:
        print("\n🚀 FAL AI интеграция готова к использованию!")
        print("📋 Следующие шаги:")
        print("   1. Настроить webhook URL в настройках FAL AI")
        print("   2. Протестировать с реальными пользователями")
        print("   3. Мониторить логи при первых запусках")
    else:
        print("\n🔧 Необходимо исправить ошибки перед продакшеном")
    
    return all_passed


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        logger.exception("Критическая ошибка в main")
        sys.exit(1) 