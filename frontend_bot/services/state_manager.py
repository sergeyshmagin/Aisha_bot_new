"""
Модуль для управления состояниями пользователя (user_states).
В будущем можно заменить реализацию на Redis.
"""

_user_states = {}

def set_state(user_id, state):
    _user_states[user_id] = state

def get_state(user_id):
    return _user_states.get(user_id)

def clear_state(user_id):
    _user_states.pop(user_id, None) 