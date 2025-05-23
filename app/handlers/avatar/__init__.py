"""
Модуль обработчиков аватаров
"""
from .training_type_selection import router as training_type_router
from .create import router as create_router
from .main import router as main_router, avatar_main_handler
from .photo_upload import router as photo_upload_router
from .training_production import router as training_router

# Создаем объединенный роутер
from aiogram import Router

router = Router()
router.include_router(main_router)
router.include_router(training_type_router)
router.include_router(create_router)
router.include_router(photo_upload_router)
router.include_router(training_router)

# Заглушка для совместимости с тестами (для старого AvatarHandler)
class AvatarHandler:
    """Заглушка для совместимости с тестами"""
    
    def __init__(self):
        """Инициализация заглушки"""
        pass
    
    async def get_services(self):
        """Заглушка для получения сервисов"""
        return {}
    
    async def show_avatar_menu(self, callback_query, state):
        """Заглушка для показа меню аватаров"""
        await avatar_main_handler.show_avatar_menu(callback_query, state)
    
    async def process_avatar_name(self, message, state):
        """Обработка имени аватара без ограничений символов"""
        name = message.text.strip()
        
        # Простая валидация - только длина
        if not name:
            await message.answer("❌ Имя не может быть пустым. Попробуйте еще раз:")
            return
            
        if len(name) < 2:
            await message.answer("❌ Имя слишком короткое. Минимум 2 символа:")
            return
            
        if len(name) > 50:
            await message.answer("❌ Имя слишком длинное. Максимум 50 символов:")
            return
        
        # ✅ Никаких ограничений на символы - принимаем любые буквы и цифры
        await state.update_data(avatar_name=name)
        
        # Переходим к следующему шагу
        await message.answer(f"✅ Имя '{name}' принято! Переходим к следующему шагу...")

# Функция для регистрации обработчиков (для совместимости с main.py)
async def register_avatar_handlers():
    """Функция для регистрации обработчиков (заглушка для совместимости)"""
    # В новой архитектуре регистрация происходит через роутеры
    pass

__all__ = [
    "training_type_router", 
    "create_router",
    "main_router",
    "photo_upload_router",
    "training_router",
    "router",
    "avatar_main_handler",
    "register_avatar_handlers",
    "AvatarHandler"  # Добавляем для совместимости
] 