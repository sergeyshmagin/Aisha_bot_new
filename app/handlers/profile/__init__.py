"""
Модуль личного кабинета пользователя
"""

from .main_handler import ProfileMainHandler
from .balance_handler import BalanceHandler
from .settings_handler import SettingsHandler
from .stats_handler import StatsHandler

__all__ = [
    "ProfileMainHandler",
    "BalanceHandler", 
    "SettingsHandler",
    "StatsHandler"
] 