#!/usr/bin/env python3
"""
Скрипт для проверки статуса API сервера
"""
import asyncio
import aiohttp
import sys

async def check_api_server():
    """Проверяет доступность API сервера"""
    
    urls_to_check = [
        "https://aibots.kz:8443/health",
        "https://aibots.kz:8443/api/v1/avatar/test_webhook",
        "https://aibots.kz:8443/docs",
    ]
    
    print("🔍 Проверка API сервера...")
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False)
    ) as session:
        
        for url in urls_to_check:
            try:
                print(f"\n📡 Проверяем: {url}")
                
                async with session.get(url, timeout=10) as response:
                    print(f"   Статус: {response.status}")
                    print(f"   Headers: {dict(response.headers)}")
                    
                    if response.status == 200:
                        text = await response.text()
                        print(f"   Ответ: {text[:200]}...")
                        print(f"   ✅ OK")
                    else:
                        print(f"   ❌ Ошибка")
                        
            except Exception as e:
                print(f"   ❌ Ошибка подключения: {e}")
        
        # Проверяем POST webhook
        print(f"\n📡 Проверяем POST webhook...")
        webhook_url = "https://aibots.kz:8443/api/v1/avatar/status_update?training_type=style"
        
        test_data = {
            "request_id": "test-request-id",
            "status": "completed"
        }
        
        try:
            async with session.post(
                webhook_url, 
                json=test_data,
                timeout=10
            ) as response:
                print(f"   Статус: {response.status}")
                text = await response.text()
                print(f"   Ответ: {text}")
                
                if response.status == 200:
                    print(f"   ✅ Webhook работает!")
                else:
                    print(f"   ❌ Webhook не работает")
                    
        except Exception as e:
            print(f"   ❌ Ошибка webhook: {e}")

if __name__ == "__main__":
    print("🚀 Проверка API сервера")
    asyncio.run(check_api_server()) 