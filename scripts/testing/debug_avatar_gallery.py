#!/usr/bin/env python3
"""
Скрипт для отладки галереи аватаров
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_session
from app.core.di import get_user_service, get_avatar_service
from sqlalchemy import text, select
from app.database.models import Avatar, User

async def debug_gallery():
    """Отлаживает логику галереи аватаров"""
    
    # Получаем первого пользователя (предполагаем что это тестовый)
    async with get_session() as session:
        user_query = select(User).limit(1)
        result = await session.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user:
            print('❌ Пользователи не найдены')
            return
        
        print(f'👤 Пользователь: {user.first_name} (ID: {user.id})')
        print(f'📱 Telegram ID: {user.telegram_id}')
        print()
        
        # Проверяем аватары через SQL
        avatars_query = text("""
            SELECT id, name, status, training_type, is_main
            FROM avatars 
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """)
        result = await session.execute(avatars_query, {"user_id": user.id})
        avatars_sql = result.fetchall()
        
        print(f'📊 Аватары через SQL (всего {len(avatars_sql)}):')
        for avatar in avatars_sql:
            print(f'   • {avatar.name} - {avatar.status} ({avatar.training_type})')
        print()
        
        # Проверяем аватары через сервис
        async with get_avatar_service() as avatar_service:
            avatars_service = await avatar_service.get_user_avatars_with_photos(user.id)
        
        print(f'📊 Аватары через сервис (всего {len(avatars_service)}):')
        for avatar in avatars_service:
            print(f'   • {avatar.name} - {avatar.status} ({avatar.training_type})')
            print(f'     Фотографий: {len(avatar.photos) if avatar.photos else 0}')
        print()
        
        # Проверяем фильтр != "DRAFT"
        non_draft = [a for a in avatars_sql if a.status != 'draft']
        print(f'📊 Не-черновики (должны показываться в галерее): {len(non_draft)}')
        for avatar in non_draft:
            print(f'   • {avatar.name} - {avatar.status}')
        print()
        
        # Проверяем только completed
        completed_only = [a for a in avatars_sql if a.status == 'completed']
        print(f'📊 Только завершенные: {len(completed_only)}')
        for avatar in completed_only:
            print(f'   • {avatar.name} - {avatar.status}')

if __name__ == "__main__":
    asyncio.run(debug_gallery()) 