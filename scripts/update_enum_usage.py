#!/usr/bin/env python3
"""
Скрипт для обновления использований AvatarStatus ENUM в коде

Заменяет UPPERCASE значения на lowercase в Python файлах.

Использование:
    python scripts/update_enum_usage.py
"""

import os
import re
from pathlib import Path

def update_enum_usage():
    """Обновляет использования AvatarStatus в коде"""
    
    # Маппинг старых значений на новые
    replacements = {
        'AvatarStatus.DRAFT': 'AvatarStatus.draft',
        'AvatarStatus.UPLOADING': 'AvatarStatus.uploading',
        'AvatarStatus.PHOTOS_UPLOADING': 'AvatarStatus.photos_uploading',
        'AvatarStatus.READY': 'AvatarStatus.ready',
        'AvatarStatus.READY_FOR_TRAINING': 'AvatarStatus.ready_for_training',
        'AvatarStatus.TRAINING': 'AvatarStatus.training',
        'AvatarStatus.COMPLETED': 'AvatarStatus.completed',
        'AvatarStatus.ERROR': 'AvatarStatus.error',
        'AvatarStatus.CANCELLED': 'AvatarStatus.cancelled',
    }
    
    # Получаем корень проекта
    project_root = Path(__file__).parent.parent
    
    # Паттерн для поиска Python файлов
    python_files = []
    for directory in ['app', 'tests']:
        dir_path = project_root / directory
        if dir_path.exists():
            python_files.extend(dir_path.rglob('*.py'))
    
    updated_files = []
    total_replacements = 0
    
    for file_path in python_files:
        try:
            # Читаем файл
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_replacements = 0
            
            # Применяем замены
            for old_value, new_value in replacements.items():
                count = content.count(old_value)
                if count > 0:
                    content = content.replace(old_value, new_value)
                    file_replacements += count
                    print(f"  {old_value} → {new_value}: {count} замен")
            
            # Если были изменения, сохраняем файл
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                updated_files.append(str(file_path.relative_to(project_root)))
                total_replacements += file_replacements
                print(f"✅ Обновлен файл: {file_path.relative_to(project_root)} ({file_replacements} замен)")
        
        except Exception as e:
            print(f"❌ Ошибка обработки файла {file_path}: {e}")
    
    print(f"\n📊 Результаты:")
    print(f"  • Обновлено файлов: {len(updated_files)}")
    print(f"  • Всего замен: {total_replacements}")
    
    if updated_files:
        print(f"\n📝 Обновлённые файлы:")
        for file_path in updated_files:
            print(f"  • {file_path}")
    
    return len(updated_files), total_replacements

if __name__ == "__main__":
    print("🔄 Обновление использований AvatarStatus...")
    print("=" * 50)
    
    updated_count, replacements_count = update_enum_usage()
    
    if updated_count > 0:
        print(f"\n✅ Обновление завершено! Обновлено {updated_count} файлов, сделано {replacements_count} замен.")
        print("🚀 Перезапустите приложение для применения изменений.")
    else:
        print("\n✅ Все файлы уже используют правильные значения ENUM.") 