"""
Утилиты для работы с состоянием.
"""

from typing import Dict, Any, Optional
from frontend_bot.services.state_manager import StateManager
from frontend_bot.config import STORAGE_DIR

# Создаем глобальный экземпляр StateManager
state_manager = StateManager(STORAGE_DIR)

async def get_state(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Получает состояние пользователя.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        Optional[Dict[str, Any]]: Состояние пользователя или None
    """
    return await state_manager.get_state(str(user_id))

async def set_state(user_id: int, state: Dict[str, Any]) -> None:
    """
    Устанавливает состояние пользователя.
    
    Args:
        user_id: ID пользователя
        state: Новое состояние
    """
    await state_manager.set_state(str(user_id), state)

async def clear_state(user_id: int) -> None:
    """
    Очищает состояние пользователя.
    
    Args:
        user_id: ID пользователя
    """
    await state_manager.clear_state(str(user_id))

async def cleanup_state(user_id: int) -> None:
    """
    Очищает все данные пользователя.
    
    Args:
        user_id: ID пользователя
    """
    await state_manager.cleanup_state(str(user_id)) 