#!/usr/bin/env python3
"""
Скрипт для отладки поиска аватара в БД
"""
import asyncio
import sys
import os
from uuid import UUID

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_session
from app.database.models import Avatar
from sqlalchemy import select

async def debug_avatar_search():
    """Отладка поиска аватара"""
    
    avatar_id = "165fab7d-3168-4a84-bc02-fec49f03b070"
    request_id = "94cccb24-c21f-44ac-90f6-25c78453d357"
    
    print(f"🔍 Отладка поиска аватара")
    print(f"📋 Avatar ID: {avatar_id}")
    print(f"📋 Request ID: {request_id}")
    
    async with get_session() as session:
        
        # 1. Поиск по ID аватара
        print(f"\n1️⃣ Поиск по Avatar ID...")
        stmt = select(Avatar).where(Avatar.id == UUID(avatar_id))
        result = await session.execute(stmt)
        avatar = result.scalar_one_or_none()
        
        if avatar:
            print(f"✅ Аватар найден по ID:")
            print(f"   Имя: {avatar.name}")
            print(f"   Статус: {avatar.status}")
            print(f"   FAL Request ID: {avatar.fal_request_id}")
            print(f"   Finetune ID: {avatar.finetune_id}")
            print(f"   Model URL: {avatar.model_url}")
            print(f"   User ID: {avatar.user_id}")
        else:
            print(f"❌ Аватар НЕ найден по ID")
        
        # 2. Поиск по fal_request_id
        print(f"\n2️⃣ Поиск по FAL Request ID...")
        stmt = select(Avatar).where(Avatar.fal_request_id == request_id)
        result = await session.execute(stmt)
        avatar_by_request = result.scalar_one_or_none()
        
        if avatar_by_request:
            print(f"✅ Аватар найден по Request ID:")
            print(f"   ID: {avatar_by_request.id}")
            print(f"   Имя: {avatar_by_request.name}")
            print(f"   Статус: {avatar_by_request.status}")
        else:
            print(f"❌ Аватар НЕ найден по Request ID")
        
        # 3. Поиск всех аватаров пользователя
        if avatar:
            print(f"\n3️⃣ Все аватары пользователя...")
            stmt = select(Avatar).where(Avatar.user_id == avatar.user_id)
            result = await session.execute(stmt)
            user_avatars = result.scalars().all()
            
            print(f"📋 Найдено {len(user_avatars)} аватаров:")
            for i, av in enumerate(user_avatars, 1):
                print(f"   {i}. {av.name} (ID: {av.id})")
                print(f"      Статус: {av.status}")
                print(f"      FAL Request ID: {av.fal_request_id}")
                print(f"      Finetune ID: {av.finetune_id}")
                print(f"")
        
        # 4. Поиск по частичному совпадению request_id
        print(f"\n4️⃣ Поиск по частичному совпадению...")
        request_id_short = request_id[:8]  # Первые 8 символов
        stmt = select(Avatar).where(Avatar.fal_request_id.like(f"{request_id_short}%"))
        result = await session.execute(stmt)
        similar_avatars = result.scalars().all()
        
        if similar_avatars:
            print(f"✅ Найдены похожие аватары:")
            for av in similar_avatars:
                print(f"   {av.name}: {av.fal_request_id}")
        else:
            print(f"❌ Похожие аватары не найдены")
        
        # 5. Проверим метод поиска из сервиса
        print(f"\n5️⃣ Проверка метода из сервиса...")
        try:
            from app.services.avatar.training_service import AvatarTrainingService
            training_service = AvatarTrainingService(session)
            
            found_avatar = await training_service._find_avatar_by_request_id(request_id)
            if found_avatar:
                print(f"✅ Сервис нашел аватар: {found_avatar.name}")
            else:
                print(f"❌ Сервис НЕ нашел аватар")
                
        except Exception as e:
            print(f"❌ Ошибка в сервисе: {e}")

if __name__ == "__main__":
    print("🚀 Отладка поиска аватара в БД")
    asyncio.run(debug_avatar_search()) 