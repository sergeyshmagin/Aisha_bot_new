"""
Модуль обработчиков нового меню

Экспортирует все обработчики для удобного импорта
"""

# Главное меню
from .main_handler import MainMenuHandler

# Творчество
from .creativity_handler import CreativityHandler

# Мои работы
from .projects_handler import ProjectsHandler

# Бизнес-ассистент
from .business_handler import BusinessHandler

# Баланс (переиспользует profile)
from .balance_handler import BalanceMenuHandler

# Настройки (переиспользует profile)
from .settings_handler import SettingsMenuHandler

# Помощь (переиспользует profile)
from .help_handler import HelpMenuHandler

# ==================== LEGACY ИМПОРТ (ЗАКОММЕНТИРОВАН) ====================
# TODO: Удалить после полного перехода на новую структуру
# Миграционный слой больше не нужен
# from .migration import MenuMigration

__all__ = [
    # Главное меню
    "MainMenuHandler",
    
    # Творчество
    "CreativityHandler",
    
    # Мои работы
    "ProjectsHandler",
    
    # Бизнес-ассистент
    "BusinessHandler",
    
    # Баланс
    "BalanceMenuHandler",
    
    # Настройки
    "SettingsMenuHandler",
    
    # Помощь
    "HelpMenuHandler",
    
    # ==================== LEGACY (ЗАКОММЕНТИРОВАНО) ====================
    # "MenuMigration",
] 