"""
Базовый класс для сервисов
"""
import logging
from typing import Optional

class BaseService:
    """Базовый класс для всех сервисов"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def __str__(self) -> str:
        return f"{self.__class__.__name__}"
