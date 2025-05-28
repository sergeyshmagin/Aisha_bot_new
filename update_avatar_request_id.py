#!/usr/bin/env python3
"""
Скрипт для обновления FAL Request ID в аватаре
"""
import asyncio
import sys
import os
from uuid import UUID

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_session
from app.database.models import Avatar
from sqlalchemy import select, update

async def update_avatar_request_id():
    """Обновляет FAL Request ID в аватаре"""
    
    avatar_id = "165fab7d-3168-4a84-bc02-fec49f03b070"
    request_id = "94cccb24-c21f-44ac-90f6-25c78453d357"
    
    print(f"🔧 Обновление FAL Request ID в аватаре")
    print(f"📋 Avatar ID: {avatar_id}")
    print(f"📋 Request ID: {request_id}")
    
    async with get_session() as session:
        
        # Проверяем текущее состояние
        stmt = select(Avatar).where(Avatar.id == UUID(avatar_id))
        result = await session.execute(stmt)
        avatar = result.scalar_one_or_none()
        
        if not avatar:
            print(f"❌ Аватар не найден")
            return
        
        print(f"\n📋 Текущее состояние:")
        print(f"   Имя: {avatar.name}")
        print(f"   Статус: {avatar.status}")
        print(f"   FAL Request ID: {avatar.fal_request_id}")
        
        # Обновляем Request ID
        print(f"\n🔧 Обновляем FAL Request ID...")
        
        update_stmt = update(Avatar).where(Avatar.id == UUID(avatar_id)).values(
            fal_request_id=request_id
        )
        
        await session.execute(update_stmt)
        await session.commit()
        
        print(f"✅ FAL Request ID обновлен")
        
        # Проверяем результат
        await session.refresh(avatar)
        print(f"\n📋 Новое состояние:")
        print(f"   FAL Request ID: {avatar.fal_request_id}")
        
        # Теперь проверим поиск
        print(f"\n🔍 Проверка поиска по Request ID...")
        stmt = select(Avatar).where(Avatar.fal_request_id == request_id)
        result = await session.execute(stmt)
        found_avatar = result.scalar_one_or_none()
        
        if found_avatar:
            print(f"✅ Аватар теперь найден по Request ID: {found_avatar.name}")
        else:
            print(f"❌ Аватар все еще не найден по Request ID")

if __name__ == "__main__":
    print("🚀 Обновление FAL Request ID")
    asyncio.run(update_avatar_request_id()) 