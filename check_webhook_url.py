#!/usr/bin/env python3
"""
Проверка webhook URL в конфигурации
"""
import os
import sys
from pathlib import Path

# Добавляем путь к приложению
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from app.core.config import settings
    
    print("🔧 КОНФИГУРАЦИЯ WEBHOOK")
    print("=" * 40)
    
    print(f"FAL_WEBHOOK_URL: {settings.FAL_WEBHOOK_URL}")
    print(f"FAL_API_KEY установлен: {'Да' if settings.effective_fal_api_key else 'Нет'}")
    print(f"AVATAR_TEST_MODE: {settings.AVATAR_TEST_MODE}")
    
    # Проверяем переменные окружения
    print(f"\n🌍 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    webhook_env = os.getenv('FAL_WEBHOOK_URL')
    print(f"FAL_WEBHOOK_URL (env): {webhook_env or 'Не установлена'}")
    
    api_key_env = os.getenv('FAL_API_KEY') or os.getenv('FAL_KEY')
    print(f"FAL_API_KEY (env): {'Установлен' if api_key_env else 'Не установлен'}")
    
    test_mode_env = os.getenv('AVATAR_TEST_MODE')
    print(f"AVATAR_TEST_MODE (env): {test_mode_env or 'Не установлена'}")
    
    print(f"\n📡 ПРОБЛЕМА:")
    if settings.AVATAR_TEST_MODE:
        print("⚠️  Бот работает в ТЕСТОВОМ РЕЖИМЕ!")
        print("   В тестовом режиме webhook'и не отправляются в FAL AI")
        print("   Для продакшена установите: AVATAR_TEST_MODE=false")
    else:
        print("✅ Бот работает в продакшн режиме")
        
    if not settings.effective_fal_api_key:
        print("❌ FAL_API_KEY не установлен!")
        print("   Без API ключа обучение не будет работать")
    else:
        print("✅ FAL_API_KEY установлен")
        
    print(f"\n🔗 WEBHOOK URL: {settings.FAL_WEBHOOK_URL}")
    print("   Этот URL должен быть доступен из интернета для FAL AI")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("🔧 Запустите из директории проекта: cd /opt/aisha-backend")
except Exception as e:
    print(f"💥 Ошибка: {e}") 