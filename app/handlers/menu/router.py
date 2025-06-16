"""
Роутер для модуля меню

Новая структура меню без LEGACY поддержки.
Переиспользует существующий функционал из app/handlers/profile/
"""
from aiogram import Router

# Импортируем роутеры обработчиков
from .main_handler import MainMenuHandler
from .creativity_handler import router as creativity_router
from .projects_handler import router as projects_router
from .business_handler import router as business_router
from .balance_handler import router as balance_router
from .settings_handler import router as settings_router
from .help_handler import router as help_router
from .navigation_handler import router as navigation_router

# ==================== LEGACY ИМПОРТЫ (ЗАКОММЕНТИРОВАНЫ) ====================
# TODO: Удалить после полного перехода на новую структуру

# LEGACY: Миграционный слой - больше не нужен
# from .migration import router as migration_router

# LEGACY: Старый роутер профиля - заменен на новые обработчики
# from app.handlers.profile.router import profile_router

# Создаем основной роутер меню
menu_router = Router(name="menu")

# Создаем экземпляр главного обработчика меню
main_menu_handler = MainMenuHandler()

# ==================== НОВАЯ СТРУКТУРА РОУТЕРОВ ====================

# 1. Роутер главного обработчика меню (высший приоритет)
menu_router.include_router(main_menu_handler.router)

# 2. Роутеры подразделов нового меню
menu_router.include_router(creativity_router)
menu_router.include_router(projects_router)
menu_router.include_router(business_router)
menu_router.include_router(balance_router)
menu_router.include_router(settings_router)
menu_router.include_router(help_router)
menu_router.include_router(navigation_router)

# ==================== LEGACY РОУТЕРЫ (ЗАКОММЕНТИРОВАНЫ) ====================
# TODO: Удалить после полного перехода на новую структуру

# LEGACY: Миграционный слой (больше не нужен)
# menu_router.include_router(migration_router)

# LEGACY: Роутер профиля для обратной совместимости
# menu_router.include_router(profile_router)

# Экспортируем для использования в main.py
__all__ = ["menu_router", "main_menu_handler"] 