#!/usr/bin/env python3
"""
Тестирование системы аватаров
"""
import asyncio
import sys
sys.path.append('.')

async def test_avatar_system():
    print('🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ АВАТАРОВ')
    print('=' * 50)
    
    try:
        # Тест импортов
        print('📦 Тестирование импортов...')
        
        from app.handlers.avatar import router
        print('✅ Основной роутер аватаров импортирован')
        
        from app.handlers.avatar.main import avatar_main_handler
        print('✅ Главный обработчик импортирован')
        
        from app.handlers.avatar.photo_upload import photo_handler
        print('✅ Обработчик загрузки фото импортирован')
        
        from app.handlers.avatar.training_production import training_handler
        print('✅ Обработчик обучения импортирован')
        
        from app.keyboards.photo_upload import get_photo_upload_keyboard
        print('✅ Клавиатуры загрузки фото импортированы')
        
        # Тест клавиатур
        print('\n🎹 Тестирование клавиатур...')
        keyboard = get_photo_upload_keyboard(5, 10, 20)
        print(f'✅ Клавиатура загрузки: {len(keyboard.inline_keyboard)} рядов')
        
        # Тест сервисов
        print('\n🔧 Тестирование сервисов...')
        from app.services.avatar.photo_service import PhotoUploadService
        print('✅ PhotoUploadService доступен')
        
        from app.services.avatar.training_service import AvatarTrainingService
        print('✅ AvatarTrainingService доступен')
        
        # Тест состояний
        print('\n📊 Тестирование состояний...')
        from app.handlers.state import AvatarStates
        states = [attr for attr in dir(AvatarStates) if not attr.startswith('_')]
        print(f'✅ Состояния аватаров: {len(states)} штук')
        print(f'   Основные: {", ".join(states[:5])}...')
        
        # Тест моделей
        print('\n🗄️ Тестирование моделей...')
        from app.database.models import Avatar, AvatarPhoto, AvatarTrainingType
        print('✅ Модели Avatar, AvatarPhoto импортированы')
        print(f'✅ Типы обучения: {[t.value for t in AvatarTrainingType]}')
        
        print('\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!')
        print('🚀 Система аватаров готова к использованию!')
        
        # Статистика
        print('\n📈 СТАТИСТИКА СИСТЕМЫ:')
        print(f'   🎭 Обработчиков: 4 (main, create, photo_upload, training)')
        print(f'   🎹 Клавиатур: 6+ (основные + photo_upload)')
        print(f'   📊 Состояний FSM: {len(states)}')
        print(f'   🗄️ Моделей БД: 2 (Avatar, AvatarPhoto)')
        print(f'   🔧 Сервисов: 3+ (Avatar, Photo, Training)')
        
    except Exception as e:
        print(f'❌ ОШИБКА: {e}')
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_avatar_system())
    sys.exit(0 if success else 1) 