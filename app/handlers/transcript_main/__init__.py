"""
Модульная структура основного обработчика транскриптов
Рефакторинг app/handlers/transcript_main.py (547 строк → модули)
"""

# Основной обработчик
from .main_handler import TranscriptMainHandler

# Экспорт для обратной совместимости
__all__ = [
    "TranscriptMainHandler"
]
