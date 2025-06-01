"""
Исправление отсутствующего finetune_id для SERGEY-STYLE-150-ST
"""
import asyncio
from uuid import UUID
from sqlalchemy import select, update
from app.core.database import get_session
from app.database.models import Avatar, AvatarTrainingType, AvatarStatus
from app.services.avatar.finetune_updater_service import FinetuneUpdaterService

async def check_sergey_style_150_st():
    """Проверяет текущее состояние SERGEY-STYLE-150-ST"""
    print("🔍 Проверка состояния SERGEY-STYLE-150-ST...")
    
    async with get_session() as session:
        query = select(Avatar).where(Avatar.name == "SERGEY-STYLE-150-ST")
        result = await session.execute(query)
        avatar = result.scalar_one_or_none()
        
        if avatar:
            print(f"✅ Аватар найден:")
            print(f"   ID: {avatar.id}")
            print(f"   Имя: {avatar.name}")
            print(f"   Статус: {avatar.status.value}")
            print(f"   Тип: {avatar.training_type.value}")
            print(f"   finetune_id: {avatar.finetune_id}")
            print(f"   fal_request_id: {avatar.fal_request_id}")
            print(f"   LoRA URL: {avatar.diffusers_lora_file_url}")
            print(f"   Config URL: {avatar.config_file_url}")
            print(f"   Trigger word: {avatar.trigger_word}")
            return avatar
        else:
            print("❌ Аватар SERGEY-STYLE-150-ST не найден")
            return None

async def get_real_finetune_id_from_fal(fal_request_id: str):
    """Получает реальный finetune_id из FAL AI API"""
    print(f"\n🌐 Запрос к FAL AI для получения finetune_id...")
    print(f"   fal_request_id: {fal_request_id}")
    
    try:
        from app.core.config import settings
        import aiohttp
        import json
        
        fal_api_key = settings.effective_fal_api_key
        if not fal_api_key:
            print(f"❌ FAL API ключ не найден")
            return None
        
        # URL для Style аватаров
        endpoint = "fal-ai/flux-pro-trainer"
        result_url = f"https://queue.fal.run/{endpoint}/requests/{fal_request_id}"
        
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
                        
                        # Извлекаем finetune_id
                        finetune_id = result_data.get("finetune_id")
                        
                        if finetune_id:
                            print(f"✅ finetune_id найден: {finetune_id}")
                            return finetune_id
                        else:
                            print(f"❌ finetune_id не найден в ответе")
                            return None
                        
                    except Exception as json_error:
                        text = await response.text()
                        print(f"   Text ответ: {text[:500]}...")
                        print(f"   JSON ошибка: {json_error}")
                        return None
                else:
                    text = await response.text()
                    print(f"   Ошибка HTTP {response.status}: {text}")
                    return None
        
    except Exception as e:
        print(f"❌ Ошибка FAL API вызова: {e}")
        return None

async def update_finetune_id_manually(avatar_id: UUID, finetune_id: str):
    """Обновляет finetune_id вручную через FinetuneUpdaterService"""
    print(f"\n🔧 Обновление finetune_id через FinetuneUpdaterService...")
    
    async with get_session() as session:
        updater = FinetuneUpdaterService(session)
        
        success = await updater.update_finetune_id_by_id(
            avatar_id=avatar_id,
            new_finetune_id=finetune_id,
            reason="Восстановление отсутствующего finetune_id из FAL AI",
            updated_by="manual_fix_script"
        )
        
        if success:
            print(f"✅ finetune_id успешно обновлен!")
        else:
            print(f"❌ Ошибка обновления finetune_id")
        
        return success

async def verify_update(avatar_id: UUID, expected_finetune_id: str):
    """Проверяет что обновление прошло успешно"""
    print(f"\n✅ Проверка результата обновления...")
    
    async with get_session() as session:
        avatar = await session.get(Avatar, avatar_id)
        if not avatar:
            print(f"❌ Аватар {avatar_id} не найден")
            return False
        
        print(f"📊 После обновления:")
        print(f"   finetune_id: {avatar.finetune_id}")
        print(f"   diffusers_lora_file_url: {avatar.diffusers_lora_file_url}")
        print(f"   config_file_url: {avatar.config_file_url}")
        print(f"   trigger_word: {avatar.trigger_word}")
        
        # Проверяем соответствие правилам
        print(f"\n🔍 Соответствие правилам Style аватара:")
        has_finetune = bool(avatar.finetune_id)
        no_lora = avatar.diffusers_lora_file_url is None
        has_trigger = bool(avatar.trigger_word)
        
        print(f"   finetune_id установлен: {'✅' if has_finetune else '❌'}")
        print(f"   LoRA очищен: {'✅' if no_lora else '❌'}")
        print(f"   trigger_word установлен: {'✅' if has_trigger else '❌'}")
        
        # Проверяем что finetune_id правильный
        if avatar.finetune_id == expected_finetune_id:
            print(f"✅ finetune_id соответствует ожидаемому!")
            return True
        else:
            print(f"❌ finetune_id не соответствует ожидаемому:")
            print(f"   Получен: {avatar.finetune_id}")
            print(f"   Ожидался: {expected_finetune_id}")
            return False

async def check_update_history(avatar_id: UUID):
    """Проверяет историю обновлений finetune_id"""
    print(f"\n📋 История обновлений finetune_id...")
    
    async with get_session() as session:
        updater = FinetuneUpdaterService(session)
        history = await updater.get_update_history(avatar_id)
        
        if history:
            print(f"📊 Найдено {len(history)} записей в истории:")
            for i, record in enumerate(history, 1):
                print(f"   {i}. {record.get('timestamp', 'N/A')}")
                print(f"      Старый: {record.get('old_finetune_id', 'N/A')}")
                print(f"      Новый: {record.get('new_finetune_id', 'N/A')}")
                print(f"      Причина: {record.get('reason', 'N/A')}")
                print(f"      Кем: {record.get('updated_by', 'N/A')}")
                print("")
        else:
            print(f"📊 История обновлений пуста")

async def main():
    """Основная функция исправления"""
    print("🔧 ИСПРАВЛЕНИЕ ОТСУТСТВУЮЩЕГО FINETUNE_ID")
    print("=" * 60)
    
    # Ожидаемый finetune_id из скриншота FAL AI
    expected_finetune_id = "df9f2a81-f27b-4621-9a25-bf50474bf0dd"
    print(f"🎯 Ожидаемый finetune_id: {expected_finetune_id}")
    
    # 1. Проверяем текущее состояние
    avatar = await check_sergey_style_150_st()
    if not avatar:
        return
    
    avatar_id = avatar.id
    fal_request_id = avatar.fal_request_id
    
    print(f"\n💡 Проблема: finetune_id отсутствует, но должен быть {expected_finetune_id}")
    
    # 2. Получаем реальный finetune_id из FAL AI
    real_finetune_id = await get_real_finetune_id_from_fal(fal_request_id)
    
    if real_finetune_id:
        print(f"\n✅ Получен finetune_id из FAL AI: {real_finetune_id}")
        
        # Проверяем что он соответствует ожидаемому
        if real_finetune_id == expected_finetune_id:
            print(f"✅ finetune_id соответствует ожидаемому из скриншота!")
        else:
            print(f"⚠️ finetune_id отличается от ожидаемого:")
            print(f"   Из FAL AI: {real_finetune_id}")
            print(f"   Ожидался: {expected_finetune_id}")
        
        # 3. Обновляем finetune_id в базе данных
        success = await update_finetune_id_manually(avatar_id, real_finetune_id)
        
        if success:
            # 4. Проверяем результат
            await verify_update(avatar_id, real_finetune_id)
            
            # 5. Смотрим историю обновлений
            await check_update_history(avatar_id)
        
    else:
        print(f"\n❌ Не удалось получить finetune_id из FAL AI")
        print(f"💡 Попробуем обновить с ожидаемым значением из скриншота...")
        
        # Обновляем с ожидаемым значением
        success = await update_finetune_id_manually(avatar_id, expected_finetune_id)
        
        if success:
            await verify_update(avatar_id, expected_finetune_id)
            await check_update_history(avatar_id)
    
    print("\n🎉 Исправление завершено!")

if __name__ == "__main__":
    asyncio.run(main()) 