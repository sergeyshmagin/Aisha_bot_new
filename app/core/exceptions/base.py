"""
Базовые классы исключений для Aisha Bot
"""


class AishaBaseException(Exception):
    """Базовое исключение для всех ошибок Aisha Bot"""
    
    def __init__(self, message: str = None, code: str = None, details: dict = None):
        self.message = message or "Произошла ошибка"
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return self.message
    
    def to_dict(self):
        """Преобразует исключение в словарь для логирования"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details
        } 