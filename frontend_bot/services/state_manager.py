"""
Менеджер состояний пользователей.
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
from frontend_bot.shared.file_operations import AsyncFileManager
from frontend_bot.config import STORAGE_DIR, STATE_FILE, CACHE_ENABLED, CACHE_TTL, CACHE_MAX_SIZE

logger = logging.getLogger(__name__)

# Создаем глобальный экземпляр StateManager
_state_manager = None

def get_state_manager() -> 'StateManager':
    """Получает глобальный экземпляр StateManager."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager

async def get_state(user_id: str) -> Optional[Dict[str, Any]]:
    """Получает состояние пользователя."""
    return await get_state_manager().get_state(user_id)

async def set_state(user_id: str, state: Dict[str, Any]) -> None:
    """Устанавливает состояние пользователя."""
    await get_state_manager().set_state(user_id, state)

async def clear_state(user_id: str) -> None:
    """Очищает состояние пользователя."""
    await get_state_manager().clear_state(user_id)

class StateManager:
    """Менеджер для работы с состояниями пользователей."""
    
    def __init__(self, storage_dir: Path = STORAGE_DIR):
        """
        Инициализация менеджера состояний.
        
        Args:
            storage_dir: Директория для хранения файлов
        """
        self.storage_dir = storage_dir
        self.state_file = storage_dir / STATE_FILE
        self._states_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_enabled = CACHE_ENABLED
        self._cache_ttl = CACHE_TTL
        self._cache_max_size = CACHE_MAX_SIZE
        self._last_load_time = 0
    
    async def _ensure_dirs(self) -> None:
        """Создает необходимые директории, если они не существуют."""
        await AsyncFileManager.ensure_dir(self.storage_dir)
    
    async def _load_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Загружает состояния пользователей из файла.
        
        Returns:
            Dict[str, Dict[str, Any]]: Словарь с состояниями пользователей
        """
        current_time = time.time()
        
        # Если кэш включен и не истек TTL, возвращаем закэшированные данные
        if (
            self._cache_enabled 
            and self._states_cache 
            and (current_time - self._last_load_time) < self._cache_ttl
        ):
            return self._states_cache.copy()
            
        await self._ensure_dirs()
        
        if not await AsyncFileManager.exists(self.state_file):
            self._states_cache = {}
            self._last_load_time = current_time
            return {}
        
        try:
            content = await AsyncFileManager.read_file(self.state_file)
            states = json.loads(content)
            if self._cache_enabled:
                self._states_cache = states.copy()
                self._last_load_time = current_time
            return states
        except Exception as e:
            logger.error(f"Error loading states: {e}")
            self._states_cache = {}
            self._last_load_time = current_time
            return {}
    
    async def _save_states(self, states: Dict[str, Dict[str, Any]]) -> None:
        """
        Сохраняет состояния пользователей в файл.
        
        Args:
            states: Словарь с состояниями пользователей
        """
        await self._ensure_dirs()
        
        try:
            content = json.dumps(states, ensure_ascii=False, indent=2)
            await AsyncFileManager.write_file(self.state_file, content)
            if self._cache_enabled:
                self._states_cache = states.copy()
                self._last_load_time = time.time()
        except Exception as e:
            logger.error(f"Error saving states: {e}")
            raise
    
    async def get_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает состояние пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[Dict[str, Any]]: Состояние пользователя или None
        """
        states = await self._load_states()
        return states.get(str(user_id))
    
    async def set_state(self, user_id: str, state: Dict[str, Any]) -> None:
        """
        Устанавливает состояние пользователя.
        
        Args:
            user_id: ID пользователя
            state: Новое состояние
        """
        states = await self._load_states()
        states[str(user_id)] = state
        await self._save_states(states)
    
    async def clear_state(self, user_id: str) -> None:
        """
        Очищает состояние пользователя.
        
        Args:
            user_id: ID пользователя
        """
        states = await self._load_states()
        if str(user_id) in states:
            del states[str(user_id)]
            await self._save_states(states)
    
    async def cleanup_state(self, user_id: str) -> None:
        """
        Очищает все данные пользователя.
        
        Args:
            user_id: ID пользователя
        """
        await self.clear_state(user_id)
    
    def clear_cache(self) -> None:
        """Очищает кэш состояний."""
        self._states_cache.clear()
        self._last_load_time = 0
