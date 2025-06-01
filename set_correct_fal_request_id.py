"""
Установка правильного fal_request_id для SERGEY-STYLE-150-ST из скриншота FAL AI
"""
import asyncio
from uuid import UUID
from sqlalchemy import select, update
from app.core.database import get_session
from app.database.models import Avatar

async def set_fal_request_id_from_screenshot():
    """Устанавливает fal_request_id из скриншота FAL AI"""
    print("🔧 Установка fal_request_id из скриншота FAL AI...")
    
    # Из скриншота видно: e82db8dd-99e2-46cc-9bc5-6727f0911790
    correct_fal_request_id = "e82db8dd-99e2-46cc-9bc5-6727f0911790"
    
    print(f"🎯 fal_request_id из скриншота: {correct_fal_request_id}")
    
    async with get_session() as session:
        # Находим аватар
        query = select(Avatar).where(Avatar.name == "SERGEY-STYLE-150-ST")
        result = await session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            print("❌ Аватар SERGEY-STYLE-150-ST не найден")
            return False
        
        print(f"✅ Аватар найден: {avatar.id}")
        print(f"   Текущий fal_request_id: {avatar.fal_request_id}")
        
        # Обновляем fal_request_id
        stmt = update(Avatar).where(Avatar.id == avatar.id).values(
            fal_request_id=correct_fal_request_id
        )
        await session.execute(stmt)
        await session.commit()
        
        print(f"✅ fal_request_id обновлен: {correct_fal_request_id}")
        return True

async def test_fal_api_with_correct_id():
    """Тестирует FAL AI с правильным request_id"""
    print(f"\n🌐 Тестирование FAL AI с правильным request_id...")
    
    request_id = "e82db8dd-99e2-46cc-9bc5-6727f0911790"
    
    try:
        from app.core.config import settings
        import aiohttp
        import json
        
        fal_api_key = settings.effective_fal_api_key
        if not fal_api_key:
            print(f"❌ FAL API ключ не найден")
            return None
        
        endpoint = "fal-ai/flux-pro-trainer"
        result_url = f"https://queue.fal.run/{endpoint}/requests/{request_id}"
        
        headers = {
            "Authorization": f"Key {fal_api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"📡 Запрос к: {result_url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(result_url, headers=headers) as response:
                print(f"   HTTP код: {response.status}")
                
                if response.status == 200:
                    try:
                        result_data = await response.json()
                        print(f"   JSON ответ:")
                        print(f"      {json.dumps(result_data, indent=2, ensure_ascii=False)}")
                        
                        finetune_id = result_data.get("finetune_id")
                        if finetune_id:
                            print(f"✅ finetune_id найден: {finetune_id}")
                            
                            # Проверяем соответствие ожидаемому из скриншота
                            expected_finetune_id = "df9f2a81-f27b-4621-9a25-bf50474bf0dd"
                            if finetune_id == expected_finetune_id:
                                print(f"✅ finetune_id соответствует скриншоту!")
                            else:
                                print(f"⚠️ finetune_id отличается от скриншота:")
                                print(f"   Получен: {finetune_id}")
                                print(f"   Ожидался: {expected_finetune_id}")
                            
                            return finetune_id
                        else:
                            print(f"❌ finetune_id не найден в ответе")
                            return None
                    except Exception as e:
                        text = await response.text()
                        print(f"   Text ответ: {text[:500]}...")
                        print(f"   JSON ошибка: {e}")
                        return None
                else:
                    text = await response.text()
                    print(f"   Ошибка HTTP {response.status}: {text}")
                    return None
        
    except Exception as e:
        print(f"❌ Ошибка FAL API: {e}")
        return None

async def main():
    """Основная функция"""
    print("🔧 УСТАНОВКА ПРАВИЛЬНОГО FAL_REQUEST_ID")
    print("=" * 50)
    
    # 1. Устанавливаем правильный fal_request_id
    success = await set_fal_request_id_from_screenshot()
    
    if success:
        # 2. Тестируем FAL API с правильным ID
        finetune_id = await test_fal_api_with_correct_id()
        
        if finetune_id:
            print(f"\n🎉 УСПЕХ! Получен finetune_id: {finetune_id}")
            print(f"💡 Теперь можно запустить полное тестирование мониторинга")
        else:
            print(f"\n❌ Не удалось получить finetune_id")
    
    print("\n🎉 Настройка завершена!")

if __name__ == "__main__":
    asyncio.run(main()) 