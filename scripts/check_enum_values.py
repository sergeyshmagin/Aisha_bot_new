#!/usr/bin/env python3
"""
Скрипт для проверки значений enum AvatarStatus
"""

import sys
from pathlib import Path

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.models import AvatarStatus

def check_enum_values():
    """Проверяет значения enum"""
    
    print("🔍 Проверка значений AvatarStatus enum:")
    print()
    
    for status in AvatarStatus:
        print(f"   {status.name} = '{status.value}'")
    
    print()
    print(f"✅ AvatarStatus.COMPLETED = '{AvatarStatus.COMPLETED}'")
    print(f"✅ AvatarStatus.COMPLETED.value = '{AvatarStatus.COMPLETED.value}'")
    
    # Тестируем сравнения
    test_status = "completed"
    print()
    print(f"🧪 Тестирование сравнений с '{test_status}':")
    print(f"   '{test_status}' == AvatarStatus.COMPLETED: {test_status == AvatarStatus.COMPLETED}")
    print(f"   '{test_status}' == AvatarStatus.COMPLETED.value: {test_status == AvatarStatus.COMPLETED.value}")

if __name__ == "__main__":
    check_enum_values() 