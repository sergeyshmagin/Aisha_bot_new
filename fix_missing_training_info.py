#!/usr/bin/env python3
"""
Скрипт для восстановления информации об обучении аватара
Исправляет ситуацию когда обучение запущено в FAL AI, но не сохранено в БД
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

async def fix_avatar_training_info(avatar_id_str: str, fal_request_id: str):
    """
    Восстанавливает информацию об обучении аватара
    
    Args:
        avatar_id_str: ID аватара
        fal_request_id: Request ID от FAL AI из логов
    """
    try:
        avatar_id = UUID(avatar_id_str)
        print(f"🔧 Восстановление информации об обучении аватара: {avatar_id}")
        print(f"📋 FAL Request ID: {fal_request_id}")
        
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
            print(f"   FAL Request ID: {avatar.fal_request_id}")
            
            # Обновляем информацию об обучении
            print(f"\n💾 Обновление информации об обучении...")
            
            update_stmt = update(Avatar).where(Avatar.id == avatar_id).values(
                fal_request_id=fal_request_id,
                status=AvatarStatus.TRAINING_IN_PROGRESS,
                training_progress=10  # Начальный прогресс
            )
            
            await session.execute(update_stmt)
            await session.commit()
            
            print(f"✅ Информация об обучении восстановлена")
            
            # Теперь проверяем статус в FAL AI
            print(f"\n🔄 Проверка статуса в FAL AI...")
            
            fal_service = FALTrainingService()
            
            # Определяем тип обучения (из имени аватара видно что это Style)
            training_type = "style" if "style" in avatar.name.lower() else "portrait"
            print(f"   Тип обучения: {training_type}")
            
            try:
                # Проверяем статус
                status_result = await fal_service.check_training_status(
                    fal_request_id, 
                    training_type
                )
                
                print(f"✅ Статус от FAL AI:")
                print(f"   Status: {status_result.get('status', 'unknown')}")
                print(f"   Logs: {len(status_result.get('logs', []))} записей")
                
                # Обновляем статус в зависимости от результата
                if status_result.get('status') == 'completed':
                    print(f"\n🎉 Обучение завершено! Получение результата...")
                    
                    result = await fal_service.get_training_result(
                        fal_request_id,
                        training_type
                    )
                    
                    print(f"📦 Результат обучения:")
                    if 'diffusers_lora_file' in result:
                        print(f"   LoRA файл: {result['diffusers_lora_file']['url']}")
                    if 'config_file' in result:
                        print(f"   Конфиг: {result['config_file']['url']}")
                    
                    # Обновляем статус в БД через webhook
                    print(f"\n💾 Обновление статуса в БД...")
                    training_service = AvatarTrainingService(session)
                    
                    # Создаем webhook данные для обработки
                    webhook_data = {
                        "request_id": fal_request_id,
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
                    
                    # Обновляем прогресс
                    progress = 50  # Примерный прогресс для in_progress
                    update_stmt = update(Avatar).where(Avatar.id == avatar_id).values(
                        training_progress=progress
                    )
                    await session.execute(update_stmt)
                    await session.commit()
                    print(f"📊 Прогресс обновлен: {progress}%")
                    
                elif status_result.get('status') == 'failed':
                    print(f"❌ Обучение завершилось с ошибкой")
                    if 'error' in status_result:
                        print(f"   Ошибка: {status_result['error']}")
                    
                    # Обновляем статус на ошибку
                    update_stmt = update(Avatar).where(Avatar.id == avatar_id).values(
                        status=AvatarStatus.ERROR,
                        training_progress=0
                    )
                    await session.execute(update_stmt)
                    await session.commit()
                    print(f"💾 Статус обновлен на ERROR")
                
                return True
                
            except Exception as e:
                print(f"❌ Ошибка при проверке статуса в FAL AI: {e}")
                return False
        
    except ValueError:
        print(f"❌ Неверный формат UUID: {avatar_id_str}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_fal_request_directly(fal_request_id: str, training_type: str = "style"):
    """
    Проверяет статус запроса напрямую в FAL AI без привязки к аватару
    
    Args:
        fal_request_id: Request ID от FAL AI
        training_type: Тип обучения (style или portrait)
    """
    print(f"🔍 Прямая проверка статуса в FAL AI")
    print(f"📋 Request ID: {fal_request_id}")
    print(f"📋 Тип обучения: {training_type}")
    
    try:
        fal_service = FALTrainingService()
        
        # Проверяем статус
        status_result = await fal_service.check_training_status(
            fal_request_id, 
            training_type
        )
        
        print(f"\n✅ Статус от FAL AI:")
        print(f"   Status: {status_result.get('status', 'unknown')}")
        print(f"   Logs: {len(status_result.get('logs', []))} записей")
        
        # Показываем логи если есть
        if 'logs' in status_result and status_result['logs']:
            print(f"\n📝 Последние логи:")
            for log in status_result['logs'][-5:]:  # Последние 5 записей
                print(f"   {log}")
        
        # Если завершено, получаем результат
        if status_result.get('status') == 'completed':
            print(f"\n🎉 Обучение завершено! Получение результата...")
            
            result = await fal_service.get_training_result(
                fal_request_id,
                training_type
            )
            
            print(f"📦 Результат обучения:")
            for key, value in result.items():
                if isinstance(value, dict) and 'url' in value:
                    print(f"   {key}: {value['url']}")
                else:
                    print(f"   {key}: {value}")
        
        return status_result
        
    except Exception as e:
        print(f"❌ Ошибка при проверке статуса в FAL AI: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Основная функция"""
    if len(sys.argv) == 3:
        # Восстановление информации об обучении
        avatar_id = sys.argv[1]
        fal_request_id = sys.argv[2]
        print(f"🔧 Восстановление информации об обучении")
        asyncio.run(fix_avatar_training_info(avatar_id, fal_request_id))
    elif len(sys.argv) == 2:
        # Прямая проверка статуса в FAL AI
        fal_request_id = sys.argv[1]
        print(f"🔍 Прямая проверка статуса в FAL AI")
        asyncio.run(check_fal_request_directly(fal_request_id))
    else:
        print(f"❌ Неверные параметры")
        print(f"📝 Использование:")
        print(f"   python fix_missing_training_info.py <fal_request_id>                    # Прямая проверка")
        print(f"   python fix_missing_training_info.py <avatar_id> <fal_request_id>        # Восстановление")

if __name__ == "__main__":
    print(f"🚀 Скрипт восстановления информации об обучении")
    print(f"")
    
    main() 