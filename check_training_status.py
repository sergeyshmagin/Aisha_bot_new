#!/usr/bin/env python3
"""
Скрипт для проверки статуса обучения аватара в FAL AI
"""
import asyncio
import sys
import os
from uuid import UUID

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_session
from app.services.avatar.fal_training_service import FALTrainingService
from app.services.avatar.training_service import AvatarTrainingService
from app.core.di import get_avatar_service

async def check_avatar_training_status(avatar_id_str: str):
    """Проверяет статус обучения аватара"""
    try:
        avatar_id = UUID(avatar_id_str)
        print(f"🔍 Проверка статуса обучения аватара: {avatar_id}")
        
        # Получаем информацию об аватаре из БД
        async with get_avatar_service() as avatar_service:
            avatar = await avatar_service.get_avatar(avatar_id)
            
            if not avatar:
                print(f"❌ Аватар {avatar_id} не найден в БД")
                return
            
            print(f"📋 Информация об аватаре:")
            print(f"   Имя: {avatar.name}")
            print(f"   Статус: {avatar.status}")
            print(f"   Прогресс: {avatar.training_progress}%")
            print(f"   Finetune ID: {avatar.finetune_id}")
            print(f"   FAL Request ID: {avatar.fal_request_id}")
            
            # Если есть request_id, проверяем статус в FAL AI
            if avatar.fal_request_id:
                print(f"\n🔄 Проверка статуса в FAL AI...")
                
                fal_service = FALTrainingService()
                
                # Определяем тип обучения
                training_type = "style" if avatar.training_type and "style" in str(avatar.training_type).lower() else "portrait"
                print(f"   Тип обучения: {training_type}")
                
                try:
                    # Проверяем статус
                    status_result = await fal_service.check_training_status(
                        avatar.fal_request_id, 
                        training_type
                    )
                    
                    print(f"✅ Статус от FAL AI:")
                    print(f"   Status: {status_result.get('status', 'unknown')}")
                    print(f"   Logs: {len(status_result.get('logs', []))} записей")
                    
                    # Если обучение завершено, получаем результат
                    if status_result.get('status') == 'completed':
                        print(f"\n🎉 Обучение завершено! Получение результата...")
                        
                        result = await fal_service.get_training_result(
                            avatar.fal_request_id,
                            training_type
                        )
                        
                        print(f"📦 Результат обучения:")
                        if 'diffusers_lora_file' in result:
                            print(f"   LoRA файл: {result['diffusers_lora_file']['url']}")
                        if 'config_file' in result:
                            print(f"   Конфиг: {result['config_file']['url']}")
                        
                        # Обновляем статус в БД
                        print(f"\n💾 Обновление статуса в БД...")
                        async with get_session() as session:
                            training_service = AvatarTrainingService(session)
                            
                            # Создаем webhook данные для обработки
                            webhook_data = {
                                "request_id": avatar.fal_request_id,
                                "status": "completed",
                                **result
                            }
                            
                            success = await training_service.handle_webhook(webhook_data)
                            if success:
                                print(f"✅ Статус успешно обновлен в БД")
                            else:
                                print(f"❌ Ошибка обновления статуса в БД")
                    
                    elif status_result.get('status') == 'in_progress':
                        print(f"⏳ Обучение в процессе...")
                        
                    elif status_result.get('status') == 'failed':
                        print(f"❌ Обучение завершилось с ошибкой")
                        if 'error' in status_result:
                            print(f"   Ошибка: {status_result['error']}")
                    
                except Exception as e:
                    print(f"❌ Ошибка при проверке статуса в FAL AI: {e}")
            
            else:
                print(f"⚠️ FAL Request ID отсутствует - невозможно проверить статус в FAL AI")
        
    except ValueError:
        print(f"❌ Неверный формат UUID: {avatar_id_str}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

async def check_all_training_avatars():
    """Проверяет статус всех аватаров в процессе обучения"""
    print(f"🔍 Поиск всех аватаров в процессе обучения...")
    
    try:
        async with get_avatar_service() as avatar_service:
            # Получаем все аватары в статусе обучения
            from app.database.models import AvatarStatus
            from sqlalchemy import select
            
            async with get_session() as session:
                from app.database.models import Avatar
                
                # Ищем аватары в процессе обучения
                stmt = select(Avatar).where(
                    Avatar.status.in_([
                        AvatarStatus.TRAINING,
                        AvatarStatus.TRAINING_QUEUED,
                        AvatarStatus.TRAINING_IN_PROGRESS
                    ])
                )
                
                result = await session.execute(stmt)
                training_avatars = result.scalars().all()
                
                if not training_avatars:
                    print(f"📭 Нет аватаров в процессе обучения")
                    return
                
                print(f"📋 Найдено {len(training_avatars)} аватаров в процессе обучения:")
                
                for avatar in training_avatars:
                    print(f"\n{'='*50}")
                    await check_avatar_training_status(str(avatar.id))
    
    except Exception as e:
        print(f"❌ Ошибка при поиске аватаров: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Основная функция"""
    if len(sys.argv) > 1:
        # Проверка конкретного аватара
        avatar_id = sys.argv[1]
        print(f"🎯 Проверка статуса конкретного аватара: {avatar_id}")
        asyncio.run(check_avatar_training_status(avatar_id))
    else:
        # Проверка всех аватаров в обучении
        print(f"🔍 Проверка всех аватаров в процессе обучения")
        asyncio.run(check_all_training_avatars())

if __name__ == "__main__":
    print(f"🚀 Скрипт проверки статуса обучения аватаров")
    print(f"📝 Использование:")
    print(f"   python check_training_status.py                    # Все аватары в обучении")
    print(f"   python check_training_status.py <avatar_id>        # Конкретный аватар")
    print(f"")
    
    main() 