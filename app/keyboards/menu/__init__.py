"""
Клавиатуры для нового меню

Экспортирует все клавиатуры для удобного импорта
"""

# Главное меню
from .main import get_main_menu_v2

# Творчество
from .creativity import get_creativity_menu, get_photo_menu, get_video_menu

# Мои работы (проекты)
from .projects import get_projects_menu, get_all_photos_menu, get_all_videos_menu, get_favorites_menu

# Баланс (переиспользует profile)
from .balance import get_balance_menu

# Настройки (переиспользует profile)
from .settings import get_settings_menu

# Помощь (переиспользует profile)
from .help import get_help_menu

# Бизнес-ассистент (создадим позже при необходимости)
# from .business import get_business_menu_v2, get_tasks_section_menu, get_news_section_menu

__all__ = [
    # Главное меню
    "get_main_menu_v2",
    
    # Творчество
    "get_creativity_menu",
    "get_photo_menu", 
    "get_video_menu",
    
    # Мои работы
    "get_projects_menu",
    "get_all_photos_menu",
    "get_all_videos_menu",
    "get_favorites_menu",
    
    # Баланс
    "get_balance_menu",
    
    # Настройки
    "get_settings_menu",
    
    # Помощь
    "get_help_menu",
    
    # Бизнес-ассистент (закомментировано до создания)
    # "get_business_menu_v2",
    # "get_tasks_section_menu", 
    # "get_news_section_menu",
] 