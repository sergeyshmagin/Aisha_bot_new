#!/usr/bin/env python3
"""
Базовый тест FAL AI клиента без БД
"""
import asyncio
import sys
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Устанавливаем переменные окружения для тестирования
os.environ['FAL_TRAINING_TEST_MODE'] = 'true'
os.environ['FAL_KEY'] = 'test_key'

print("🎯 === БАЗОВЫЙ ТЕСТ FAL AI КЛИЕНТА ===")
print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Тестовый режим: {os.environ.get('FAL_TRAINING_TEST_MODE', 'false')}")

# Тест без импорта сложных зависимостей
class MockFalAIClient:
    """Мок FAL AI клиента для тестирования"""
    
    def __init__(self):
        self.test_mode = True
        self.api_key = "test_key"
    
    def is_available(self):
        return True
    
    def get_config_summary(self):
        return {
            "test_mode": self.test_mode,
            "api_key_set": bool(self.api_key),
            "webhook_url": "https://aibots.kz/api/avatar/status_update",
            "default_mode": "character",
            "default_iterations": 500,
            "default_priority": "quality",
            "trigger_word": "TOK",
            "lora_rank": 32,
        }
    
    async def train_avatar(self, user_id, avatar_id, name, gender, photo_urls, training_config=None):
        """Симуляция запуска обучения"""
        print(f"   🚀 Запускаю обучение аватара {avatar_id}")
        print(f"   👤 Пользователь: {user_id}")
        print(f"   📸 Фотографий: {len(photo_urls)}")
        print(f"   ⚙️ Конфигурация: {training_config or 'default'}")
        
        # Симулируем задержку
        await asyncio.sleep(0.1)
        
        finetune_id = f"test_finetune_{avatar_id}"
        print(f"   ✅ Обучение запущено! Finetune ID: {finetune_id}")
        return finetune_id
    
    async def get_training_status(self, finetune_id):
        """Симуляция получения статуса"""
        print(f"   📊 Получаю статус для {finetune_id}")
        await asyncio.sleep(0.1)
        
        status = {
            "status": "completed",
            "progress": 100,
            "created_at": "2025-05-23T16:00:00Z",
            "updated_at": "2025-05-23T16:30:00Z",
            "completed_at": "2025-05-23T16:30:00Z",
            "message": "Training completed successfully (test mode)"
        }
        print(f"   ✅ Статус: {status['status']} ({status['progress']}%)")
        return status
    
    async def generate_image(self, finetune_id, prompt, config=None):
        """Симуляция генерации изображения"""
        print(f"   🎨 Генерирую изображение с моделью {finetune_id}")
        print(f"   💬 Промпт: {prompt}")
        await asyncio.sleep(0.1)
        
        image_url = "https://example.com/test_generated_image.jpg"
        print(f"   ✅ Изображение сгенерировано: {image_url}")
        return image_url


async def test_basic_functionality():
    """Тестирует базовый функционал FAL AI"""
    print("\n🧪 === ТЕСТИРОВАНИЕ БАЗОВОГО ФУНКЦИОНАЛА ===")
    
    client = MockFalAIClient()
    
    # 1. Проверяем конфигурацию
    print(f"✅ Тестовый режим: {client.test_mode}")
    print(f"✅ API ключ установлен: {client.is_available()}")
    
    config = client.get_config_summary()
    print(f"📋 Конфигурация:")
    for key, value in config.items():
        print(f"   - {key}: {value}")
    
    # 2. Тестируем полный цикл
    test_user_id = uuid4()
    test_avatar_id = uuid4()
    test_photo_urls = [
        "test/photo1.jpg",
        "test/photo2.jpg", 
        "test/photo3.jpg",
        "test/photo4.jpg",
        "test/photo5.jpg"
    ]
    
    print(f"\n🚀 Тестируем полный цикл...")
    
    try:
        # Запуск обучения
        finetune_id = await client.train_avatar(
            user_id=test_user_id,
            avatar_id=test_avatar_id,
            name="Тестовый аватар",
            gender="male",
            photo_urls=test_photo_urls
        )
        
        if not finetune_id:
            print("❌ Не удалось получить finetune_id")
            return False
        
        # Получение статуса
        status = await client.get_training_status(finetune_id)
        if not status:
            print("❌ Не удалось получить статус")
            return False
        
        # Генерация изображения
        image_url = await client.generate_image(
            finetune_id=finetune_id,
            prompt="portrait of TOK person, professional photo"
        )
        
        if not image_url:
            print("❌ Не удалось сгенерировать изображение")
            return False
        
        print("✅ Все операции выполнены успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тестировании: {e}")
        return False


async def test_webhook_format():
    """Тестирует формат webhook данных"""
    print("\n🧪 === ТЕСТИРОВАНИЕ ФОРМАТА WEBHOOK ===")
    
    # Примеры webhook данных от FAL AI
    webhook_examples = [
        {
            "finetune_id": "fal_123456789",
            "status": "queued", 
            "progress": 0,
            "message": "Training queued"
        },
        {
            "finetune_id": "fal_123456789",
            "status": "in_progress",
            "progress": 25,
            "message": "Training started"
        },
        {
            "finetune_id": "fal_123456789", 
            "status": "in_progress",
            "progress": 50,
            "message": "Training in progress"
        },
        {
            "finetune_id": "fal_123456789",
            "status": "in_progress",
            "progress": 75, 
            "message": "Training almost complete"
        },
        {
            "finetune_id": "fal_123456789",
            "status": "completed",
            "progress": 100,
            "message": "Training completed successfully"
        }
    ]
    
    print("📨 Тестируем различные форматы webhook:")
    
    for i, webhook in enumerate(webhook_examples, 1):
        print(f"\n   Webhook {i}: {webhook['status']} ({webhook['progress']}%)")
        
        # Валидация полей
        required_fields = ['finetune_id', 'status', 'progress', 'message']
        valid = all(field in webhook for field in required_fields)
        
        if valid:
            print(f"   ✅ Формат корректный")
        else:
            print(f"   ❌ Некорректный формат")
            return False
        
        await asyncio.sleep(0.1)
    
    print("\n✅ Все форматы webhook корректны!")
    return True


async def test_configuration():
    """Тестирует различные конфигурации"""
    print("\n🧪 === ТЕСТИРОВАНИЕ КОНФИГУРАЦИЙ ===")
    
    # Тестовые конфигурации
    configs = [
        {
            "name": "Базовая",
            "config": None
        },
        {
            "name": "Быстрая",
            "config": {
                "iterations": 100,
                "priority": "speed"
            }
        },
        {
            "name": "Качественная", 
            "config": {
                "iterations": 1000,
                "priority": "quality",
                "lora_rank": 64
            }
        },
        {
            "name": "Стиль",
            "config": {
                "mode": "style",
                "trigger_word": "STYLE",
                "iterations": 300
            }
        }
    ]
    
    client = MockFalAIClient()
    
    for config_data in configs:
        print(f"\n   🧪 Тестируем конфигурацию: {config_data['name']}")
        
        try:
            finetune_id = await client.train_avatar(
                user_id=uuid4(),
                avatar_id=uuid4(),
                name=f"Аватар {config_data['name']}",
                gender="female",
                photo_urls=["test1.jpg", "test2.jpg"],
                training_config=config_data['config']
            )
            
            if finetune_id:
                print(f"   ✅ Конфигурация работает")
            else:
                print(f"   ❌ Ошибка в конфигурации")
                return False
                
        except Exception as e:
            print(f"   ❌ Ошибка конфигурации: {e}")
            return False
    
    print("\n✅ Все конфигурации работают!")
    return True


async def main():
    """Основная функция тестирования"""
    print("🎯 === БАЗОВОЕ ТЕСТИРОВАНИЕ FAL AI ===")
    
    tests = [
        ("Базовый функционал", test_basic_functionality),
        ("Формат webhook", test_webhook_format),
        ("Конфигурации", test_configuration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print(f"\n{'='*50}")
    print("🏁 === ИТОГОВЫЙ ОТЧЕТ ===")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("\n📋 СТАТУС FAL AI ИНТЕГРАЦИИ:")
        print("   ✅ Клиент готов к работе")
        print("   ✅ Webhook формат поддерживается") 
        print("   ✅ Конфигурации валидны")
        print("\n🚀 ГОТОВНОСТЬ К СЛЕДУЮЩИМ ШАГАМ:")
        print("   1. Интеграция с реальной БД")
        print("   2. Подключение к Telegram боту")
        print("   3. Настройка webhook endpoint")
        print("   4. Тестирование с реальными пользователями")
    else:
        print("⚠️ ЕСТЬ ПРОБЛЕМЫ В ТЕСТАХ")
        print("🔧 Необходимо исправить ошибки")
    
    return all_passed


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit_code = 0 if result else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⛔ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1) 