#!/usr/bin/env python3
"""
Тест системы обучения аватаров с автовыбором API и webhook
"""
import asyncio
import uuid
from uuid import UUID

from app.core.config import settings
from app.services.avatar.fal_training_service import FALTrainingService
from app.core.logger import get_logger

logger = get_logger(__name__)

async def test_avatar_training_system():
    """
    Тестирует полный цикл обучения аватара:
    1. Выбор API в зависимости от типа
    2. Запуск обучения (тестовый режим)
    3. Проверка статуса
    4. Получение результата
    """
    
    print("🧪 Тестирование системы обучения аватаров")
    print(f"📋 Тестовый режим: {settings.AVATAR_TEST_MODE}")
    print(f"🔗 Webhook URL: {settings.FAL_WEBHOOK_URL}")
    print()
    
    # Создаем сервис
    fal_service = FALTrainingService()
    
    # Тестовые данные
    test_avatar_id = UUID("12345678-1234-5678-9012-123456789abc")
    test_training_url = "https://example.com/test_photos.zip"
    
    # Тест 1: Портретное обучение
    print("🎭 Тест 1: Портретное обучение")
    try:
        request_id_portrait = await fal_service.start_avatar_training(
            avatar_id=test_avatar_id,
            training_type="portrait",
            training_data_url=test_training_url,
            user_preferences={"quality": "balanced"}
        )
        
        print(f"✅ Портретное обучение запущено: {request_id_portrait}")
        
        # Проверяем информацию о типе обучения
        info = fal_service.get_training_type_info("portrait")
        print(f"📊 Информация: {info['name']} - {info['description']}")
        print(f"⚡ Скорость: {info['speed']}")
        print(f"🔧 Технология: {info['technology']}")
        
    except Exception as e:
        print(f"❌ Ошибка портретного обучения: {e}")
    
    print()
    
    # Тест 2: Художественное обучение
    print("🎨 Тест 2: Художественное обучение")
    try:
        request_id_style = await fal_service.start_avatar_training(
            avatar_id=test_avatar_id,
            training_type="style",
            training_data_url=test_training_url,
            user_preferences={"quality": "fast"}
        )
        
        print(f"✅ Художественное обучение запущено: {request_id_style}")
        
        # Проверяем информацию о типе обучения
        info = fal_service.get_training_type_info("style")
        print(f"📊 Информация: {info['name']} - {info['description']}")
        print(f"⚡ Скорость: {info['speed']}")
        print(f"🔧 Технология: {info['technology']}")
        
    except Exception as e:
        print(f"❌ Ошибка художественного обучения: {e}")
    
    print()
    
    # Тест 3: Проверка статуса
    print("📊 Тест 3: Проверка статуса обучения")
    try:
        if 'request_id_portrait' in locals():
            status = await fal_service.check_training_status(
                request_id_portrait, 
                "portrait"
            )
            print(f"🎭 Статус портретного: {status.get('status', 'unknown')}")
            print(f"📈 Прогресс: {status.get('progress', 0)}%")
            
            if status.get('logs'):
                print(f"📝 Логи: {status['logs'][-1]}")
        
        if 'request_id_style' in locals():
            status = await fal_service.check_training_status(
                request_id_style, 
                "style"
            )
            print(f"🎨 Статус художественного: {status.get('status', 'unknown')}")
            print(f"📈 Прогресс: {status.get('progress', 0)}%")
            
    except Exception as e:
        print(f"❌ Ошибка проверки статуса: {e}")
    
    print()
    
    # Тест 4: Получение результата (тестовый режим)
    print("🎯 Тест 4: Получение результата")
    try:
        if 'request_id_portrait' in locals():
            result = await fal_service.get_training_result(
                request_id_portrait,
                "portrait"
            )
            print(f"🎭 Результат портретного:")
            print(f"   📁 Файл модели: {result.get('diffusers_lora_file', {}).get('file_name', 'N/A')}")
            print(f"   🔗 URL: {result.get('mock_model_url', 'N/A')}")
            print(f"   🧪 Тестовый режим: {result.get('test_mode', False)}")
            
    except Exception as e:
        print(f"❌ Ошибка получения результата: {e}")
    
    print()
    
    # Тест 5: Конфигурация сервиса
    print("⚙️ Тест 5: Конфигурация сервиса")
    config = fal_service.get_config_summary()
    print(f"🧪 Тестовый режим: {config['test_mode']}")
    print(f"🔗 Webhook URL: {config['webhook_url']}")
    print(f"🔑 API ключ настроен: {config['api_key_configured']}")
    print(f"📦 FAL клиент доступен: {config['fal_client_available']}")
    print(f"🎯 Поддерживаемые типы: {', '.join(config['supported_training_types'])}")
    print(f"⚡ Пресеты качества: {', '.join(config['quality_presets'])}")
    
    print()
    print("✅ Тестирование завершено!")

async def test_webhook_simulation():
    """
    Тестирует симуляцию webhook в тестовом режиме
    """
    print("📡 Тестирование webhook симуляции")
    
    if not settings.AVATAR_TEST_MODE:
        print("⚠️ Тест webhook симуляции работает только в тестовом режиме")
        return
    
    if not getattr(settings, 'FAL_ENABLE_WEBHOOK_SIMULATION', False):
        print("⚠️ Webhook симуляция отключена в настройках")
        return
    
    fal_service = FALTrainingService()
    test_avatar_id = UUID("87654321-4321-8765-2109-987654321cba")
    
    print(f"🚀 Запуск обучения с webhook симуляцией...")
    
    try:
        request_id = await fal_service.start_avatar_training(
            avatar_id=test_avatar_id,
            training_type="portrait",
            training_data_url="https://example.com/test.zip"
        )
        
        print(f"✅ Обучение запущено: {request_id}")
        print(f"⏱️ Ожидание webhook через {getattr(settings, 'FAL_MOCK_TRAINING_DURATION', 30)} секунд...")
        
        # Ждем немного больше чем длительность симуляции
        await asyncio.sleep(getattr(settings, 'FAL_MOCK_TRAINING_DURATION', 30) + 5)
        
        print("📡 Webhook симуляция должна была завершиться")
        
    except Exception as e:
        print(f"❌ Ошибка webhook симуляции: {e}")

if __name__ == "__main__":
    print("🎭 Запуск тестов системы обучения аватаров")
    print("=" * 50)
    
    # Основные тесты
    asyncio.run(test_avatar_training_system())
    
    print("\n" + "=" * 50)
    
    # Тест webhook симуляции
    asyncio.run(test_webhook_simulation())
    
    print("\n🎉 Все тесты завершены!") 