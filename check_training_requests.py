#!/usr/bin/env python3
"""
Скрипт для проверки активных запросов обучения аватаров в БД
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к приложению
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(app_dir))

# Устанавливаем переменные окружения если нужно
if not os.getenv('PYTHONPATH'):
    os.environ['PYTHONPATH'] = str(current_dir)

try:
    from app.database.connection import get_async_session
    from app.database.models import Avatar, AvatarStatus
    from sqlalchemy import select, and_
    from sqlalchemy.orm import selectinload
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("🔧 Попробуйте запустить из директории проекта:")
    print("   cd /opt/aisha-backend")
    print("   python check_training_requests.py")
    sys.exit(1)

async def check_training_requests():
    """Проверяет активные запросы обучения в БД"""
    
    print("🔍 ПРОВЕРКА АКТИВНЫХ ЗАПРОСОВ ОБУЧЕНИЯ")
    print("=" * 50)
    
    try:
        async for session in get_async_session():
            try:
                # Ищем аватары в статусе обучения
                query = (
                    select(Avatar)
                    .where(
                        and_(
                            Avatar.status == AvatarStatus.TRAINING,
                            Avatar.finetune_id.isnot(None)
                        )
                    )
                    .options(selectinload(Avatar.photos))
                )
                
                result = await session.execute(query)
                training_avatars = result.scalars().all()
                
                if not training_avatars:
                    print("📭 Нет активных запросов обучения")
                    
                    # Проверим завершенные аватары
                    completed_query = (
                        select(Avatar)
                        .where(Avatar.status == AvatarStatus.COMPLETED)
                        .order_by(Avatar.training_completed_at.desc())
                        .limit(5)
                    )
                    
                    completed_result = await session.execute(completed_query)
                    completed_avatars = completed_result.scalars().all()
                    
                    if completed_avatars:
                        print("\n✅ Последние завершенные аватары:")
                        for avatar in completed_avatars:
                            print(f"   🎭 {avatar.name} (ID: {avatar.id})")
                            print(f"      Request ID: {avatar.finetune_id}")
                            print(f"      Завершен: {avatar.training_completed_at}")
                            print()
                    
                    return
                
                print(f"🎯 Найдено {len(training_avatars)} активных запросов:")
                print()
                
                for i, avatar in enumerate(training_avatars, 1):
                    print(f"{i}. 🎭 **{avatar.name}**")
                    print(f"   ID аватара: {avatar.id}")
                    print(f"   Request ID: {avatar.finetune_id}")
                    print(f"   Статус: {avatar.status.value}")
                    print(f"   Прогресс: {avatar.training_progress}%")
                    print(f"   Начато: {avatar.training_started_at}")
                    print(f"   Фотографий: {len(avatar.photos) if avatar.photos else 0}")
                    print(f"   Пользователь: {avatar.user_id}")
                    print()
                
                # Предлагаем выбрать request_id для тестирования
                print("🧪 Для тестирования webhook'а используйте один из Request ID выше")
                print("💡 Скопируйте Request ID и запустите: python test_local_webhook.py")
                
                break
                
            except Exception as e:
                print(f"❌ Ошибка запроса к БД: {e}")
                await session.rollback()
                raise
            finally:
                await session.close()
                
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")

async def check_recent_avatars():
    """Проверяет недавно созданные аватары"""
    
    print("\n📅 НЕДАВНО СОЗДАННЫЕ АВАТАРЫ")
    print("=" * 30)
    
    try:
        async for session in get_async_session():
            try:
                # Ищем последние 10 аватаров
                query = (
                    select(Avatar)
                    .order_by(Avatar.created_at.desc())
                    .limit(10)
                )
                
                result = await session.execute(query)
                recent_avatars = result.scalars().all()
                
                for i, avatar in enumerate(recent_avatars, 1):
                    status_emoji = {
                        AvatarStatus.DRAFT: "📝",
                        AvatarStatus.TRAINING: "🔄",
                        AvatarStatus.COMPLETED: "✅",
                        AvatarStatus.ERROR: "❌"
                    }.get(avatar.status, "❓")
                    
                    print(f"{i:2d}. {status_emoji} {avatar.name}")
                    print(f"     ID: {avatar.id}")
                    print(f"     Request ID: {avatar.finetune_id or 'Нет'}")
                    print(f"     Статус: {avatar.status.value}")
                    print(f"     Создан: {avatar.created_at}")
                    print()
                
                break
                
            except Exception as e:
                print(f"❌ Ошибка запроса к БД: {e}")
                await session.rollback()
                raise
            finally:
                await session.close()
                
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")

async def main():
    """Основная функция"""
    await check_training_requests()
    await check_recent_avatars()
    
    print("\n🔧 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Сначала протестируйте локальный API: python test_local_webhook.py")
    print("2. Если локальный API работает, проверьте Nginx конфигурацию")
    print("3. Скопируйте Request ID из списка выше для тестирования")

if __name__ == "__main__":
    asyncio.run(main()) 