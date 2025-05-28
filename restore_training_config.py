#!/usr/bin/env python3
"""
Скрипт для восстановления оригинальных настроек обучения после тестирования
"""

def restore_config():
    """Восстанавливает оригинальные настройки обучения"""
    
    config_file = "app/core/config.py"
    
    # Читаем файл
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Восстанавливаем оригинальные значения
    replacements = [
        # Portrait Trainer Settings
        ('FAL_PORTRAIT_STEPS: int = Field(1, env="FAL_PORTRAIT_STEPS")', 
         'FAL_PORTRAIT_STEPS: int = Field(1000, env="FAL_PORTRAIT_STEPS")'),
        
        # Pro Trainer Settings
        ('FAL_PRO_ITERATIONS: int = Field(1, env="FAL_PRO_ITERATIONS")', 
         'FAL_PRO_ITERATIONS: int = Field(500, env="FAL_PRO_ITERATIONS")'),
        
        # Quality Presets - Fast
        ('"portrait": {"steps": 1, "learning_rate": 0.0003}',
         '"portrait": {"steps": 500, "learning_rate": 0.0003}'),
        ('"general": {"iterations": 1, "learning_rate": 2e-4, "priority": "speed"}',
         '"general": {"iterations": 200, "learning_rate": 2e-4, "priority": "speed"}'),
        
        # Quality Presets - Balanced
        ('"portrait": {"steps": 1, "learning_rate": 0.0002}',
         '"portrait": {"steps": 1000, "learning_rate": 0.0002}'),
        ('"general": {"iterations": 1, "learning_rate": 1e-4, "priority": "quality"}',
         '"general": {"iterations": 500, "learning_rate": 1e-4, "priority": "quality"}'),
        
        # Quality Presets - Quality
        ('"portrait": {"steps": 1, "learning_rate": 0.0001}',
         '"portrait": {"steps": 2500, "learning_rate": 0.0001}'),
        ('"general": {"iterations": 1, "learning_rate": 5e-5, "priority": "quality"}',
         '"general": {"iterations": 1000, "learning_rate": 5e-5, "priority": "quality"}'),
        
        # Комментарии
        ('# FAL AI - Portrait Trainer Settings (ВРЕМЕННО: 1 шаг для тестирования)',
         '# FAL AI - Portrait Trainer Settings'),
        ('# FAL AI - Pro Trainer Settings (flux-pro-trainer) - ВРЕМЕННО: 1 итерация для тестирования',
         '# FAL AI - Pro Trainer Settings (flux-pro-trainer)'),
        ('# FAL AI - Quality Presets (ВРЕМЕННО: минимальные значения для тестирования webhook)',
         '# FAL AI - Quality Presets'),
    ]
    
    # Применяем замены
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Записываем обратно
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Оригинальные настройки обучения восстановлены!")
    print("📝 Восстановленные значения:")
    print("   - Portrait steps: 1000")
    print("   - Pro iterations: 500") 
    print("   - Fast preset: portrait=500 steps, general=200 iterations")
    print("   - Balanced preset: portrait=1000 steps, general=500 iterations")
    print("   - Quality preset: portrait=2500 steps, general=1000 iterations")

if __name__ == "__main__":
    restore_config() 