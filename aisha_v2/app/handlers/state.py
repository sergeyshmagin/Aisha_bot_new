"""
Состояния для FSM
"""
from aiogram.fsm.state import StatesGroup, State

class TranscribeStates(StatesGroup):
    """Состояния для транскрибации"""
    menu = State()  # Меню транскрибации
    waiting_audio = State()  # Ожидание аудио
    waiting_text = State()  # Ожидание текста
    processing = State()  # Обработка файла
    result = State()  # Показ результата
    format_selection = State()  # Выбор формата
    error = State()  # Состояние ошибки 