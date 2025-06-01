from aiogram.fsm.state import State, StatesGroup


class GenerationStates(StatesGroup):
    """Состояния FSM для генерации изображений"""
    
    waiting_for_custom_prompt = State()
    waiting_for_quality_selection = State()
    generation_in_progress = State() 