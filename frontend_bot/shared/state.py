"""
Глобальные переменные состояния для всех хендлеров и сервисов бота.
"""

from typing import Dict

# user_id -> текущее состояние FSM (если используется)
user_states: Dict[int, str] = {}
