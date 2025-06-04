#!/usr/bin/env python3
"""
Скрипт для детальной проверки аватаров пользователя
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_session
from sqlalchemy import text

async def check_avatars():
    """Проверяет аватары в БД"""
    
    async with get_session() as session:
        # Получаем информацию об аватарах
        result = await session.execute(text("""
            SELECT 
                id,
                name,
                status,
                training_type,
                created_at,
                training_started_at,
                training_completed_at,
                finetune_id,
                fal_request_id,
                diffusers_lora_file_url,
                trigger_phrase
            FROM avatars 
            ORDER BY created_at DESC
        """))
        
        avatars = result.fetchall()
        
        if not avatars:
            print('❌ Аватары не найдены')
            return
        
        print(f'📊 Найдено {len(avatars)} аватаров:')
        print()
        
        for i, avatar in enumerate(avatars, 1):
            print(f'🎭 Аватар #{i}:')
            print(f'   ID: {avatar.id}')
            print(f'   Имя: {avatar.name}')
            print(f'   Статус: {avatar.status}')
            print(f'   Тип: {avatar.training_type}')
            print(f'   Создан: {avatar.created_at}')
            
            if avatar.training_started_at:
                print(f'   Обучение начато: {avatar.training_started_at}')
            
            if avatar.training_completed_at:
                print(f'   Обучение завершено: {avatar.training_completed_at}')
            
            if avatar.finetune_id:
                print(f'   Finetune ID: {avatar.finetune_id}')
            
            if avatar.fal_request_id:
                print(f'   FAL Request ID: {avatar.fal_request_id}')
            
            if avatar.diffusers_lora_file_url:
                print(f'   LoRA URL: {avatar.diffusers_lora_file_url[:50]}...')
            
            if avatar.trigger_phrase:
                print(f'   Trigger Phrase: {avatar.trigger_phrase}')
            
            print()
        
        # Статистика по статусам
        completed_count = len([a for a in avatars if a.status == 'completed'])
        ready_count = len([a for a in avatars if a.status == 'ready_for_training'])
        training_count = len([a for a in avatars if a.status == 'training'])
        
        print(f'📈 Статистика:')
        print(f'   Завершённые: {completed_count}')
        print(f'   Готовы к обучению: {ready_count}')
        print(f'   В процессе обучения: {training_count}')

if __name__ == "__main__":
    asyncio.run(check_avatars()) 