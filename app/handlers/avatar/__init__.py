"""
Модуль обработчиков аватаров
"""
from .training_type_selection import router as training_type_router
from .create import router as create_router
from .main import router as main_router, avatar_main_handler

# Создаем объединенный роутер
from aiogram import Router

router = Router()
router.include_router(main_router)
router.include_router(training_type_router)
router.include_router(create_router)

# Функция для регистрации обработчиков (для совместимости с main.py)
async def register_avatar_handlers():
    """Функция для регистрации обработчиков (заглушка для совместимости)"""
    # В новой архитектуре регистрация происходит через роутеры
    pass

__all__ = [
    "training_type_router", 
    "create_router",
    "main_router",
    "router",
    "avatar_main_handler",
    "register_avatar_handlers"
] 