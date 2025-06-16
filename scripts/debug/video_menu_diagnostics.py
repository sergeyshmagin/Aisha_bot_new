#!/usr/bin/env python3
"""
Диагностика видео меню - определяет причину неработающего видео меню

Использование:
    python scripts/debug/video_menu_diagnostics.py
"""
import sys
import asyncio
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.logger import get_logger

logger = get_logger(__name__)

async def check_video_menu_registration():
    """Проверяет регистрацию обработчиков видео меню"""
    print("🔍 Проверка регистрации обработчиков видео меню...")
    
    try:
        # Импортируем основные компоненты
        from app.handlers.menu.creativity_handler import creativity_handler
        from app.handlers.menu.router import menu_router
        from app.handlers import main_router
        
        print("✅ Все обработчики импортированы")
        
        # Проверяем creativity_handler
        router = creativity_handler.router
        print(f"📋 Роутер творчества: {router}")
        
        # Проверяем обработчики
        if hasattr(router, 'callback_query') and hasattr(router.callback_query, 'handlers'):
            handlers = router.callback_query.handlers
            print(f"🔧 Найдено {len(handlers)} callback обработчиков")
            
            # Ищем обработчик show_video_menu
            video_menu_handler = None
            for handler in handlers:
                if hasattr(handler, 'callback') and hasattr(handler.callback, '__name__'):
                    if handler.callback.__name__ == 'show_video_menu':
                        video_menu_handler = handler
                        break
            
            if video_menu_handler:
                print("✅ Обработчик show_video_menu найден")
                
                # Проверяем фильтры
                if hasattr(video_menu_handler, 'filters'):
                    print(f"🔍 Фильтров: {len(video_menu_handler.filters)}")
                    for i, filter_obj in enumerate(video_menu_handler.filters):
                        print(f"   Фильтр {i+1}: {filter_obj}")
            else:
                print("❌ Обработчик show_video_menu НЕ найден!")
                return False
        
        print("✅ Проверка регистрации завершена")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки регистрации: {e}")
        import traceback
        traceback.print_exc()
        return False

async def simulate_callback_processing():
    """Симулирует обработку callback video_menu"""
    print("\n🎭 Симуляция обработки callback 'video_menu'...")
    
    try:
        from aiogram.types import CallbackQuery, User, Chat, Message
        from aiogram.fsm.context import FSMContext
        from aiogram.fsm.storage.memory import MemoryStorage
        from app.handlers.menu.creativity_handler import creativity_handler
        
        # Создаем mock объекты
        storage = MemoryStorage()
        
        # Создаем тестового пользователя
        test_user = User(
            id=174171680,  # Тестовый ID из логов
            is_bot=False,
            first_name="Тест",
            username="test_user"
        )
        
        # Создаем тестовый чат
        test_chat = Chat(
            id=174171680,
            type="private"
        )
        
        # Создаем тестовое сообщение
        from datetime import datetime
        test_message = Message(
            message_id=1,
            date=datetime.now(),
            chat=test_chat,
            from_user=test_user,
            text="Тестовое сообщение"
        )
        
        # Создаем тестовый callback
        test_callback = CallbackQuery(
            id="test_callback",
            from_user=test_user,
            chat_instance="test_instance",
            data="video_menu",
            message=test_message
        )
        
        # Создаем FSMContext
        state = FSMContext(storage=storage, key="test_key")
        
        print("✅ Mock объекты созданы")
        
        # Пытаемся вызвать обработчик напрямую
        print("🎯 Вызов show_video_menu...")
        await creativity_handler.show_video_menu(test_callback, state)
        
        print("✅ Обработчик вызван успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка симуляции callback: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_keyboard_consistency():
    """Проверяет консистентность клавиатур"""
    print("\n⌨️ Проверка консистентности клавиатур...")
    
    try:
        from app.keyboards.menu.creativity import get_creativity_menu, get_video_menu
        from app.keyboards.main import get_video_menu as get_video_menu_main
        
        # Проверяем меню творчества
        creativity_kb = get_creativity_menu()
        video_kb_creativity = get_video_menu()
        video_kb_main = get_video_menu_main()
        
        print("✅ Все клавиатуры созданы")
        
        # Сравниваем video меню из разных источников
        creativity_buttons = []
        for row in video_kb_creativity.inline_keyboard:
            for btn in row:
                creativity_buttons.append((btn.text, btn.callback_data))
        
        main_buttons = []
        for row in video_kb_main.inline_keyboard:
            for btn in row:
                main_buttons.append((btn.text, btn.callback_data))
        
        if creativity_buttons == main_buttons:
            print("✅ Клавиатуры видео меню идентичны")
        else:
            print("⚠️ Клавиатуры видео меню РАЗЛИЧАЮТСЯ!")
            print("   Из creativity:", creativity_buttons)
            print("   Из main:", main_buttons)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки клавиатур: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Основная функция диагностики"""
    print("🚀 Диагностика видео меню")
    print("=" * 50)
    
    # Проверяем регистрацию обработчиков
    if not await check_video_menu_registration():
        print("\n❌ ПРОБЛЕМА: Обработчики не зарегистрированы правильно")
        return
    
    # Проверяем консистентность клавиатур
    if not await check_keyboard_consistency():
        print("\n❌ ПРОБЛЕМА: Клавиатуры неконсистентны")
        return
    
    # Симулируем обработку callback
    if not await simulate_callback_processing():
        print("\n❌ ПРОБЛЕМА: Ошибка в обработчике show_video_menu")
        return
    
    print("\n" + "=" * 50)
    print("🎉 ВСЯ ДИАГНОСТИКА ПРОШЛА УСПЕШНО!")
    print("\n💡 Возможные причины проблемы:")
    print("   1. Ошибка в логах бота при реальной работе")
    print("   2. Проблема с базой данных или внешними сервисами")
    print("   3. Некорректное состояние FSM")
    print("   4. Проблема с middleware")
    print("   5. Timeout при обработке callback")
    
    print("\n🔧 Рекомендации:")
    print("   1. Запустите бота и проверьте логи")
    print("   2. Попробуйте нажать кнопку видео и проследите в логах")
    print("   3. Проверьте работу других кнопок меню")
    print("   4. Убедитесь что callback_data точно равен 'video_menu'")

if __name__ == "__main__":
    asyncio.run(main()) 