#!/usr/bin/env python3
"""
Проверка конфигурации Imagen4 сервиса
"""
import sys
import asyncio
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)

async def check_imagen4_config():
    """Проверяет конфигурацию Imagen4"""
    
    print("🔧 ПРОВЕРКА КОНФИГУРАЦИИ IMAGEN4")
    print("=" * 50)
    
    try:
        # Проверяем настройки
        print(f"⚙️  НАСТРОЙКИ:")
        print(f"   📊 Imagen4 включен: {getattr(settings, 'IMAGEN4_ENABLED', 'НЕ УСТАНОВЛЕНО')}")
        print(f"   🔑 FAL API KEY: {'✅ Установлен' if getattr(settings, 'FAL_API_KEY', None) else '❌ НЕ УСТАНОВЛЕН'}")
        print(f"   💰 Стоимость генерации: {getattr(settings, 'IMAGEN4_GENERATION_COST', 'НЕ УСТАНОВЛЕНО')}")
        print(f"   📐 Базовое соотношение: {getattr(settings, 'IMAGEN4_DEFAULT_ASPECT_RATIO', 'НЕ УСТАНОВЛЕНО')}")
        print(f"   🔢 Максимум изображений: {getattr(settings, 'IMAGEN4_MAX_IMAGES', 'НЕ УСТАНОВЛЕНО')}")
        print(f"   ⏱️  Таймаут: {getattr(settings, 'IMAGEN4_TIMEOUT', 'НЕ УСТАНОВЛЕНО')}s")
        
        # Проверяем импорты
        print(f"\n📦 ИМПОРТЫ:")
        try:
            import fal_client
            print(f"   ✅ fal_client: {fal_client.__version__ if hasattr(fal_client, '__version__') else 'OK'}")
        except ImportError as e:
            print(f"   ❌ fal_client: НЕ УСТАНОВЛЕН ({e})")
        
        # Проверяем Imagen4 сервис
        print(f"\n🧪 IMAGEN4 СЕРВИС:")
        try:
            from app.services.generation.imagen4.imagen4_service import Imagen4Service
            service = Imagen4Service()
            print(f"   ✅ Imagen4Service создан")
            print(f"   📊 Доступен: {service.is_available()}")
            
            # Проверяем конфигурацию сервиса
            config = service.get_config()
            print(f"   🔑 API ключ в конфиге: {'✅' if config.api_key else '❌'}")
            print(f"   📊 Включен в конфиге: {config.enabled}")
            print(f"   💰 Стоимость: {config.generation_cost}")
            print(f"   🌐 API endpoint: {config.api_endpoint}")
            
        except Exception as e:
            print(f"   ❌ Ошибка создания сервиса: {e}")
        
        # Проверяем ImageStorage
        print(f"\n💾 IMAGE STORAGE:")
        try:
            from app.services.generation.storage.image_storage import ImageStorage
            storage = ImageStorage()
            print(f"   ✅ ImageStorage создан")
            
            # Проверяем MinIO конфигурацию
            print(f"   🗄️  MinIO endpoint: {getattr(settings, 'MINIO_ENDPOINT', 'НЕ УСТАНОВЛЕНО')}")
            print(f"   🔑 MinIO access key: {'✅' if getattr(settings, 'MINIO_ACCESS_KEY', None) else '❌'}")
            print(f"   📦 MinIO bucket: {getattr(settings, 'MINIO_BUCKET', 'НЕ УСТАНОВЛЕНО')}")
            
        except Exception as e:
            print(f"   ❌ Ошибка создания ImageStorage: {e}")
        
        # Предложения по исправлению
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        
        if not getattr(settings, 'FAL_API_KEY', None):
            print(f"   🔑 Установите FAL_API_KEY в переменных окружения")
        
        if not getattr(settings, 'IMAGEN4_ENABLED', True):
            print(f"   📊 Включите IMAGEN4_ENABLED=true")
        
        print(f"   🔄 Перезапустите бота после изменения конфигурации")
        
    except Exception as e:
        logger.exception(f"Ошибка проверки конфигурации: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(check_imagen4_config()) 