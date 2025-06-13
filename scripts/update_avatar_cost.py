#!/usr/bin/env python3
"""
Скрипт для обновления стоимости создания аватара в .env файле
"""
import os
import re
from pathlib import Path

def update_avatar_cost():
    """Обновляет стоимость создания аватара в .env файле"""
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ Файл .env не найден")
        return False
    
    # Читаем содержимое файла
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем значение AVATAR_CREATION_COST
    old_pattern = r'AVATAR_CREATION_COST=\d+'
    new_value = 'AVATAR_CREATION_COST=150'
    
    if re.search(old_pattern, content):
        new_content = re.sub(old_pattern, new_value, content)
        
        # Записываем обновленное содержимое
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Стоимость создания аватара обновлена с 10 на 150 кредитов")
        return True
    else:
        # Если переменная не найдена, добавляем её
        content += f"\n{new_value}\n"
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Добавлена переменная AVATAR_CREATION_COST=150")
        return True

if __name__ == "__main__":
    print("🔧 Обновление стоимости создания аватара...")
    
    if update_avatar_cost():
        print("\n💰 Новые стоимости:")
        print("🎭 Создание аватара: 150 кредитов")
        print("🖼️ Генерация изображений: 5 кредитов") 
        print("🎨 Imagen4 генерация: 5 кредитов")
        print("🎤 Транскрибация/мин: 10 кредитов")
        
        print("\n📊 Экономика пакетов:")
        packages = {
            "small": {"coins": 250, "price": 490},
            "medium": {"coins": 500, "price": 870}, 
            "large": {"coins": 1000, "price": 1540}
        }
        
        for name, pkg in packages.items():
            cost_per_avatar = (pkg["price"] / pkg["coins"]) * 150
            avatars_per_package = pkg["coins"] // 150
            print(f"📦 {name.capitalize()}: {avatars_per_package} аватар(ов) за {pkg['price']}₽ (~{cost_per_avatar:.1f}₽ за аватар)")
    else:
        print("❌ Не удалось обновить стоимость") 