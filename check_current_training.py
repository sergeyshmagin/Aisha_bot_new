#!/usr/bin/env python3
"""
Скрипт для тестирования нового Status Checker
"""
import asyncio
import sys
import os
from datetime import datetime
from uuid import UUID

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_status_checker():
    """Тестирует новый status checker"""
    
    print(f"🧪 Тестирование Status Checker")
    print(f"   Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Импортируем status checker
        from app.services.avatar.fal_training_service.status_checker import status_checker
        
        # Тестовые данные
        test_avatar_id = UUID("7dec7e16-9b8f-4f74-9100-e4d6df417a14")  # ID аватара Sergey
        test_request_id = "12012296-af62-4ff8-861c-5cc837281aad"  # Текущее обучение
        test_training_type = "style"
        
        print(f"🔍 Запуск мониторинга статуса...")
        print(f"   Avatar ID: {test_avatar_id}")
        print(f"   Request ID: {test_request_id}")
        print(f"   Training Type: {test_training_type}")
        print()
        
        # Запускаем мониторинг
        await status_checker.start_status_monitoring(
            test_avatar_id, 
            test_request_id, 
            test_training_type
        )
        
        print("✅ Status Checker запущен успешно!")
        print("🔄 Мониторинг работает в фоне...")
        print()
        print("💡 Для остановки нажмите Ctrl+C")
        
        # Ждём некоторое время чтобы увидеть работу
        await asyncio.sleep(120)  # 2 минуты
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

async def check_fal_status_directly():
    """Прямая проверка статуса в FAL AI"""
    
    print(f"🔍 Прямая проверка статуса в FAL AI")
    print("=" * 60)
    
    try:
        from app.services.avatar.fal_training_service.status_checker import status_checker
        
        # Тестовые данные
        test_request_id = "12012296-af62-4ff8-861c-5cc837281aad"
        test_training_type = "style"
        
        # Определяем endpoint
        if test_training_type == "portrait":
            endpoint = "fal-ai/flux-lora-portrait-trainer"
        else:  # style
            endpoint = "fal-ai/flux-pro-trainer"
        
        status_url = f"https://queue.fal.run/{endpoint}/requests/{test_request_id}/status"
        
        print(f"📊 Проверка статуса...")
        print(f"   Request ID: {test_request_id}")
        print(f"   Endpoint: {endpoint}")
        print(f"   URL: {status_url}")
        print()
        
        # Проверяем статус
        status_data = await status_checker._check_fal_status(status_url)
        
        if status_data:
            print(f"✅ Статус получен:")
            print(f"   Status: {status_data.get('status')}")
            print(f"   Queue Position: {status_data.get('queue_position', 'N/A')}")
            
            # Если завершено, получаем результат
            if status_data.get("status") == "COMPLETED":
                print("\n🎉 Обучение завершено! Получаем результат...")
                
                result_data = await status_checker._get_training_result(test_request_id, test_training_type)
                
                if result_data:
                    print(f"✅ Результат получен:")
                    response_data = result_data.get("response", {})
                    
                    if test_training_type == "style":
                        finetune_id = response_data.get("finetune_id")
                        config_file = response_data.get("config_file", {})
                        
                        print(f"   Finetune ID: {finetune_id}")
                        print(f"   Config File URL: {config_file.get('url', 'N/A')}")
                    
                    print(f"\n📋 Полный результат:")
                    import json
                    print(json.dumps(response_data, indent=2))
        else:
            print("❌ Не удалось получить статус")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Главная функция"""
    print("🚀 Тестирование Status Checker")
    print()
    
    # Сначала проверяем статус напрямую
    await check_fal_status_directly()
    
    print("\n" + "="*60 + "\n")
    
    # Затем тестируем полный мониторинг
    await test_status_checker()

if __name__ == "__main__":
    asyncio.run(main()) 