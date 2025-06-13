"""
Состояния для системы генерации изображений
"""
from aiogram.fsm.state import State, StatesGroup


class GenerationStates(StatesGroup):
    """Состояния для генерации изображений"""
    
    # Ожидание кастомного промпта
    waiting_for_custom_prompt = State()
    
    # Ожидание референсного фото для создания промпта
    waiting_for_reference_photo = State()
    
    # Выбор соотношения сторон
    waiting_for_aspect_ratio_selection = State()
    
    # Выбор качества
    waiting_for_quality_selection = State()
    
    # Процесс генерации
    generation_in_progress = State()
    
    # 🆕 Imagen 4 States
    # Ожидание промпта для Imagen 4
    waiting_for_imagen4_prompt = State()
    
    # Выбор aspect ratio для Imagen 4
    imagen4_selecting_aspect_ratio = State() 