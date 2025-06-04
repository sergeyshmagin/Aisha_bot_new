#!/usr/bin/env python3
"""
Скрипт для проверки завершённых аватаров и их готовности к генерации
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_session
from sqlalchemy import text

async def check_completed_avatars():
    """Проверяет завершённые аватары на готовность к генерации"""
    
    async with get_session() as session:
        # Получаем завершённые аватары
        result = await session.execute(text("""
            SELECT 
                id,
                name,
                status,
                training_type,
                diffusers_lora_file_url,
                finetune_id,
                trigger_phrase,
                trigger_word,
                created_at,
                training_completed_at
            FROM avatars 
            WHERE status = 'completed'
            ORDER BY created_at DESC
        """))
        
        avatars = result.fetchall()
        
        if not avatars:
            print('❌ Нет завершённых аватаров')
            return
        
        print(f'📊 Найдено {len(avatars)} завершённых аватаров:')
        print()
        
        for i, avatar in enumerate(avatars, 1):
            print(f'🎭 Аватар #{i}: {avatar.name}')
            print(f'   ID: {avatar.id}')
            print(f'   Статус: {avatar.status}')
            print(f'   Тип: {avatar.training_type}')
            print(f'   Создан: {avatar.created_at}')
            if avatar.training_completed_at:
                print(f'   Обучение завершено: {avatar.training_completed_at}')
            
            # Проверяем данные для генерации
            ready_for_generation = True
            issues = []
            
            if avatar.training_type == 'PORTRAIT':
                if not avatar.diffusers_lora_file_url:
                    ready_for_generation = False
                    issues.append("Отсутствует LoRA файл")
                else:
                    print(f'   ✅ LoRA файл: {avatar.diffusers_lora_file_url[:50]}...')
                
                if not avatar.trigger_phrase:
                    ready_for_generation = False
                    issues.append("Отсутствует trigger_phrase")
                else:
                    print(f'   ✅ Trigger phrase: {avatar.trigger_phrase}')
                    
            elif avatar.training_type == 'STYLE':
                if not avatar.finetune_id:
                    ready_for_generation = False
                    issues.append("Отсутствует finetune_id")
                else:
                    print(f'   ✅ Finetune ID: {avatar.finetune_id}')
                
                if not avatar.trigger_word:
                    ready_for_generation = False
                    issues.append("Отсутствует trigger_word")
                else:
                    print(f'   ✅ Trigger word: {avatar.trigger_word}')
            
            # Итоговая оценка
            if ready_for_generation:
                print(f'   🟢 ГОТОВ К ГЕНЕРАЦИИ')
            else:
                print(f'   🔴 НЕ ГОТОВ К ГЕНЕРАЦИИ')
                for issue in issues:
                    print(f'      - {issue}')
            
            print()

if __name__ == "__main__":
    asyncio.run(check_completed_avatars()) 