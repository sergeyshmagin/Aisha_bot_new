#!/usr/bin/env python3
"""
Скрипт для ручного обновления статуса завершенного обучения
Имитирует webhook от FAL AI для обновления статуса аватара
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
from app.database.models import Avatar, AvatarStatus
from sqlalchemy import select, update

async def manual_webhook_update(avatar_id_str: str, request_id: str, finetune_id: str):
    """
    Ручное обновление статуса аватара после завершения обучения
    
    Args:
        avatar_id_str: ID аватара
        request_id: Request ID от FAL AI
        finetune_id: Finetune ID результата обучения
    """
    try:
        avatar_id = UUID(avatar_id_str)
        print(f"🔧 Ручное обновление статуса аватара: {avatar_id}")
        print(f"📋 Request ID: {request_id}")
        print(f"📋 Finetune ID: {finetune_id}")
        
        # Получаем результат обучения из FAL AI
        print(f"\n🔄 Получение результата обучения из FAL AI...")
        
        fal_service = FALTrainingService()
        
        try:
            # Получаем результат обучения (style тип)
            result = await fal_service.get_training_result(request_id, "style")
            
            print(f"✅ Результат получен из FAL AI:")
            for key, value in result.items():
                if isinstance(value, dict) and 'url' in value:
                    print(f"   {key}: {value['url']}")
                else:
                    print(f"   {key}: {value}")
            
            # Создаем webhook данные для обработки
            webhook_data = {
                "request_id": request_id,
                "status": "completed",
                "finetune_id": finetune_id,
                **result
            }
            
            print(f"\n💾 Обновление статуса в БД через webhook обработчик...")
            
            async with get_session() as session:
                training_service = AvatarTrainingService(session)
                
                # Обрабатываем webhook
                success = await training_service.handle_webhook(webhook_data)
                
                if success:
                    print(f"✅ Статус успешно обновлен через webhook обработчик")
                    
                    # Проверяем обновленный статус
                    stmt = select(Avatar).where(Avatar.id == avatar_id)
                    result_check = await session.execute(stmt)
                    avatar = result_check.scalar_one_or_none()
                    
                    if avatar:
                        print(f"\n📋 Обновленная информация об аватаре:")
                        print(f"   Статус: {avatar.status}")
                        print(f"   Прогресс: {avatar.training_progress}%")
                        print(f"   Finetune ID: {avatar.finetune_id}")
                        print(f"   Model URL: {avatar.model_url}")
                        print(f"   Config URL: {avatar.config_url}")
                    
                else:
                    print(f"❌ Ошибка при обновлении статуса через webhook")
                    
                    # Попробуем прямое обновление
                    print(f"\n🔧 Попытка прямого обновления...")
                    
                    update_data = {
                        'status': AvatarStatus.READY,
                        'training_progress': 100,
                        'finetune_id': finetune_id
                    }
                    
                    # Добавляем URLs если есть
                    if 'diffusers_lora_file' in result and 'url' in result['diffusers_lora_file']:
                        update_data['model_url'] = result['diffusers_lora_file']['url']
                    
                    if 'config_file' in result and 'url' in result['config_file']:
                        update_data['config_url'] = result['config_file']['url']
                    
                    update_stmt = update(Avatar).where(Avatar.id == avatar_id).values(**update_data)
                    await session.execute(update_stmt)
                    await session.commit()
                    
                    print(f"✅ Статус обновлен напрямую")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при получении результата из FAL AI: {e}")
            
            # Попробуем обновить статус без результата
            print(f"\n🔧 Обновление статуса без результата FAL AI...")
            
            async with get_session() as session:
                update_stmt = update(Avatar).where(Avatar.id == avatar_id).values(
                    status=AvatarStatus.READY,
                    training_progress=100,
                    finetune_id=finetune_id
                )
                await session.execute(update_stmt)
                await session.commit()
                
                print(f"✅ Статус обновлен на READY")
            
            return True
        
    except ValueError:
        print(f"❌ Неверный формат UUID: {avatar_id_str}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_and_fix_avatar_status(avatar_id_str: str):
    """
    Проверяет статус аватара и исправляет если нужно
    
    Args:
        avatar_id_str: ID аватара
    """
    try:
        avatar_id = UUID(avatar_id_str)
        print(f"🔍 Проверка статуса аватара: {avatar_id}")
        
        async with get_session() as session:
            # Получаем аватар
            stmt = select(Avatar).where(Avatar.id == avatar_id)
            result = await session.execute(stmt)
            avatar = result.scalar_one_or_none()
            
            if not avatar:
                print(f"❌ Аватар {avatar_id} не найден в БД")
                return False
            
            print(f"📋 Текущая информация об аватаре:")
            print(f"   Имя: {avatar.name}")
            print(f"   Статус: {avatar.status}")
            print(f"   Прогресс: {avatar.training_progress}%")
            print(f"   Finetune ID: {avatar.finetune_id}")
            print(f"   FAL Request ID: {avatar.fal_request_id}")
            print(f"   Model URL: {avatar.model_url}")
            
            # Если есть request_id, проверяем статус в FAL AI
            if avatar.fal_request_id:
                print(f"\n🔄 Проверка статуса в FAL AI...")
                
                fal_service = FALTrainingService()
                
                try:
                    # Проверяем статус
                    status_result = await fal_service.check_training_status(
                        avatar.fal_request_id, 
                        "style"
                    )
                    
                    print(f"✅ Статус от FAL AI:")
                    print(f"   Status: {status_result.get('status', 'unknown')}")
                    
                    # Если обучение завершено, но статус в БД не обновлен
                    if (status_result.get('status') == 'completed' and 
                        avatar.status != AvatarStatus.READY):
                        
                        print(f"\n🔧 Обучение завершено, но статус не обновлен. Исправляем...")
                        
                        # Получаем результат
                        result = await fal_service.get_training_result(
                            avatar.fal_request_id,
                            "style"
                        )
                        
                        # Извлекаем finetune_id из результата
                        finetune_id = result.get('finetune_id', avatar.fal_request_id)
                        
                        # Обновляем статус
                        await manual_webhook_update(
                            avatar_id_str, 
                            avatar.fal_request_id, 
                            finetune_id
                        )
                        
                        return True
                    
                    elif avatar.status == AvatarStatus.READY:
                        print(f"✅ Статус уже корректный - аватар готов")
                        return True
                    
                    else:
                        print(f"⏳ Обучение еще в процессе")
                        return True
                
                except Exception as e:
                    print(f"❌ Ошибка при проверке статуса в FAL AI: {e}")
                    return False
            
            else:
                print(f"⚠️ FAL Request ID отсутствует")
                return False
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Основная функция"""
    if len(sys.argv) == 4:
        # Ручное обновление с параметрами
        avatar_id = sys.argv[1]
        request_id = sys.argv[2]
        finetune_id = sys.argv[3]
        print(f"🔧 Ручное обновление статуса")
        asyncio.run(manual_webhook_update(avatar_id, request_id, finetune_id))
    elif len(sys.argv) == 2:
        # Проверка и автоисправление
        avatar_id = sys.argv[1]
        print(f"🔍 Проверка и автоисправление статуса")
        asyncio.run(check_and_fix_avatar_status(avatar_id))
    else:
        print(f"❌ Неверные параметры")
        print(f"📝 Использование:")
        print(f"   python manual_webhook_fix.py <avatar_id>                                    # Автопроверка и исправление")
        print(f"   python manual_webhook_fix.py <avatar_id> <request_id> <finetune_id>         # Ручное обновление")

if __name__ == "__main__":
    print(f"🚀 Скрипт исправления статуса завершенного обучения")
    print(f"")
    
    main() 