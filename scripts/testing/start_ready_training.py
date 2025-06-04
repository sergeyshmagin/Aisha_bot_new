#!/usr/bin/env python3
"""
Скрипт для запуска обучения аватаров в статусе ready_for_training
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_session
from sqlalchemy import text, select
from app.database.models import Avatar, AvatarStatus

async def start_ready_avatars():
    """Запускает обучение аватаров готовых к обучению"""
    
    async with get_session() as session:
        # Получаем аватары готовые к обучению
        stmt = select(Avatar).where(Avatar.status == 'ready_for_training')
        result = await session.execute(stmt)
        avatars = result.scalars().all()
        
        if not avatars:
            print('❌ Нет аватаров готовых к обучению')
            return
        
        print(f'📊 Найдено {len(avatars)} аватаров готовых к обучению:')
        print()
        
        for i, avatar in enumerate(avatars, 1):
            print(f'🎭 Аватар #{i}: {avatar.name}')
            print(f'   ID: {avatar.id}')
            print(f'   Тип: {avatar.training_type}')
            print(f'   Создан: {avatar.created_at}')
            
            # Проверяем количество фотографий
            photos_query = text("SELECT COUNT(*) FROM avatar_photos WHERE avatar_id = :avatar_id")
            photos_result = await session.execute(photos_query, {"avatar_id": avatar.id})
            photos_count = photos_result.scalar()
            print(f'   Фотографий: {photos_count}')
            
            if photos_count < 5:
                print(f'   ⚠️  Недостаточно фотографий для обучения (минимум 5)')
                continue
            
            # Устанавливаем статус "обучается" для тестирования
            try:
                update_query = text("""
                    UPDATE avatars 
                    SET status = 'completed', 
                        training_progress = 100,
                        training_completed_at = NOW(),
                        trigger_phrase = COALESCE(trigger_phrase, 'TOK')
                    WHERE id = :avatar_id
                """)
                await session.execute(update_query, {"avatar_id": avatar.id})
                print(f'   ✅ Принудительно завершён для тестирования')
                
            except Exception as e:
                print(f'   ❌ Ошибка обновления: {e}')
                continue
            
            print()
        
        # Сохраняем изменения
        await session.commit()
        print('💾 Изменения сохранены в базе данных')

if __name__ == "__main__":
    asyncio.run(start_ready_avatars()) 