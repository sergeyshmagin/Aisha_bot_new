#!/usr/bin/env python3
"""
Скрипт для замены импортов после реструктуризации проекта
Заменяет все импорты вида aisha_v2.app.* на app.*
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path: Path):
    """Исправляет импорты в одном файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем импорты
        original_content = content
        content = re.sub(r'from aisha_v2\.app\.', 'from app.', content)
        content = re.sub(r'import aisha_v2\.app\.', 'import app.', content)
        
        # Если были изменения, записываем файл
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Исправлен: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ Ошибка в {file_path}: {e}")
        return False

def fix_all_imports():
    """Исправляет импорты во всех Python файлах"""
    current_dir = Path('.')
    fixed_count = 0
    
    # Ищем все Python файлы
    python_files = list(current_dir.rglob('*.py'))
    
    print(f"Найдено {len(python_files)} Python файлов")
    
    for file_path in python_files:
        # Пропускаем файлы в .venv и __pycache__
        if '.venv' in str(file_path) or '__pycache__' in str(file_path) or 'archive' in str(file_path):
            continue
            
        if fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Исправлено {fixed_count} файлов")

if __name__ == "__main__":
    fix_all_imports() 