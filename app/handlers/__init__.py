"""
Экспорт роутеров хендлеров
"""
# Новая модульная структура меню
from app.handlers.menu.router import menu_router as main_router

# ==================== LEGACY ИМПОРТ (ЗАКОММЕНТИРОВАН) ====================
# TODO: Удалить после полного перехода на новую структуру
# from app.handlers.main_menu import router as main_router

__all__ = [
    # Новая модульная структура
    "main_router",      # menu_router -> main_router (алиас для совместимости)
]
