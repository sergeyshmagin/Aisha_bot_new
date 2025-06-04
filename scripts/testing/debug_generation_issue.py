#!/usr/bin/env python3
"""
Скрипт для отладки проблемы "Аватар не найден" при генерации
"""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_session
from app.core.di import get_user_service, get_avatar_service
from sqlalchemy import select
from app.database.models import Avatar, User

async def debug_generation_issue():
    """Отлаживает проблему с генерацией"""
    
    print("🔍 Отладка проблемы 'Аватар не найден' при генерации...")
    print()
    
    # Получаем пользователя
    async with get_session() as session:
        user_query = select(User).limit(1)
        result = await session.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user:
            print('❌ Пользователи не найдены')
            return
            
        print(f"👤 Пользователь: {user.telegram_id}")
    
    # Получаем основной аватар
    async with get_avatar_service() as avatar_service:
        print("🔍 Проверяем get_main_avatar()...")
        main_avatar = await avatar_service.get_main_avatar(user.id)
        
        if main_avatar:
            print(f"✅ Основной аватар найден: {main_avatar.name} (ID: {main_avatar.id})")
            print(f"   Статус: {main_avatar.status}")
            print(f"   is_main: {main_avatar.is_main}")
            
            # Проверяем сравнение статуса
            print(f"   Сравнение статуса == 'completed': {main_avatar.status == 'completed'}")
        else:
            print("❌ Основной аватар НЕ НАЙДЕН!")
            
            # Проверим все аватары пользователя
            print("\n🔍 Все аватары пользователя:")
            avatars = await avatar_service.get_user_avatars_with_photos(user.id)
            for i, avatar in enumerate(avatars):
                print(f"   {i+1}. {avatar.name} - статус: {avatar.status}, is_main: {avatar.is_main}")
                
            # Устанавливаем первый завершенный аватар как основной
            completed_avatars = [a for a in avatars if a.status == "completed"]
            if completed_avatars:
                print(f"\n🔧 Устанавливаем {completed_avatars[0].name} как основной...")
                success = await avatar_service.set_main_avatar(user.id, completed_avatars[0].id)
                print(f"   Результат: {'✅ Успешно' if success else '❌ Ошибка'}")
                
                # Проверяем снова
                main_avatar = await avatar_service.get_main_avatar(user.id)
                if main_avatar:
                    print(f"✅ Теперь основной аватар: {main_avatar.name}")
        
        print()
        print("🎯 Тестируем получение аватара по ID...")
        
        # Получаем все завершенные аватары
        avatars = await avatar_service.get_user_avatars_with_photos(user.id)
        completed_avatars = [a for a in avatars if a.status == "completed"]
        
        if completed_avatars:
            test_avatar = completed_avatars[0]
            print(f"🧪 Тестовый аватар: {test_avatar.name} (ID: {test_avatar.id})")
            
            # Тестируем get_avatar по ID
            avatar_by_id = await avatar_service.get_avatar(test_avatar.id)
            if avatar_by_id:
                print(f"✅ get_avatar({test_avatar.id}) работает")
                print(f"   Владелец совпадает: {avatar_by_id.user_id == user.id}")
                print(f"   Статус: {avatar_by_id.status}")
            else:
                print(f"❌ get_avatar({test_avatar.id}) вернул None!")
        
        print()
        print("🎉 Отладка завершена!")

if __name__ == "__main__":
    asyncio.run(debug_generation_issue()) 